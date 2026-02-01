"""
Master Contract Service - Downloads and manages Fyers symbol data
"""
import os
import logging
import pandas as pd
import httpx
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from src.database.schema import SymTokenModel

logger = logging.getLogger(__name__)

# CSV Headers from Fyers
HEADERS = [
    "Fytoken", "Symbol Details", "Exchange Instrument type", "Minimum lot size",
    "Tick size", "ISIN", "Trading Session", "Last update date", "Expiry date",
    "Symbol ticker", "Exchange", "Segment", "Scrip code", "Underlying symbol",
    "Underlying scrip code", "Strike price", "Option type", "Underlying FyToken",
    "Reserved column1", "Reserved column2", "Reserved column3"
]

DATA_TYPES = {
    "Fytoken": str,
    "Symbol Details": str,
    "Exchange Instrument type": int,
    "Minimum lot size": int,
    "Tick size": float,
    "ISIN": str,
    "Trading Session": str,
    "Last update date": str,
    "Expiry date": str,
    "Symbol ticker": str,
    "Exchange": int,
    "Segment": int,
    "Scrip code": int,
    "Underlying symbol": str,
    "Underlying scrip code": pd.Int64Dtype(),
    "Strike price": float,
    "Option type": str,
    "Underlying FyToken": str,
    "Reserved column1": str,
    "Reserved column2": str,
    "Reserved column3": str,
}

# Fyers CSV URLs
CSV_URLS = {
    "NSE_CD": "https://public.fyers.in/sym_details/NSE_CD.csv",
    "NSE_FO": "https://public.fyers.in/sym_details/NSE_FO.csv",
    "NSE_CM": "https://public.fyers.in/sym_details/NSE_CM.csv",
    "BSE_CM": "https://public.fyers.in/sym_details/BSE_CM.csv",
    "BSE_FO": "https://public.fyers.in/sym_details/BSE_FO.csv",
    "MCX_COM": "https://public.fyers.in/sym_details/MCX_COM.csv"
}


class MasterContractService:
    """Service for managing Fyers master contract/symbol data"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.tmp_path = "tmp"
        
        # Create tmp directory if not exists
        if not os.path.exists(self.tmp_path):
            os.makedirs(self.tmp_path)
    
    def download_master_contracts(self, on_progress=None) -> Tuple[bool, str]:
        """
        Download and process all master contract files
        
        Args:
            on_progress: Optional callback for progress updates
            
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info("Starting master contract download...")
            
            # Download CSV files
            if on_progress:
                on_progress("Downloading symbol files...")
            
            success, files, error = self._download_csv_files()
            if not success:
                return False, f"Download failed: {error}"
            
            # Clear existing data
            if on_progress:
                on_progress("Clearing old data...")
            self._delete_all_symbols()
            
            # Process each exchange
            processors = [
                ("NSE", self._process_nse_csv),
                ("BSE", self._process_bse_csv),
                ("NFO", self._process_nfo_csv),
                ("CDS", self._process_cds_csv),
                ("BFO", self._process_bfo_csv),
                ("MCX", self._process_mcx_csv),
            ]
            
            total_symbols = 0
            for exchange_name, processor in processors:
                if on_progress:
                    on_progress(f"Processing {exchange_name}...")
                try:
                    df = processor()
                    if df is not None and len(df) > 0:
                        self._bulk_insert(df)
                        total_symbols += len(df)
                        logger.info(f"Processed {len(df)} symbols for {exchange_name}")
                except Exception as e:
                    logger.error(f"Error processing {exchange_name}: {e}")
            
            # Cleanup temp files
            self._cleanup_temp_files()
            
            logger.info(f"Master contract download complete. Total symbols: {total_symbols}")
            return True, f"Downloaded {total_symbols} symbols successfully"
            
        except Exception as e:
            logger.exception(f"Master contract download failed: {e}")
            return False, str(e)
    
    def _download_csv_files(self) -> Tuple[bool, List[str], Optional[str]]:
        """Download all CSV files from Fyers"""
        downloaded = []
        errors = []
        
        with httpx.Client(timeout=60.0) as client:
            for key, url in CSV_URLS.items():
                try:
                    response = client.get(url)
                    response.raise_for_status()
                    
                    file_path = os.path.join(self.tmp_path, f"{key}.csv")
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    downloaded.append(file_path)
                    logger.info(f"Downloaded {key}")
                except Exception as e:
                    errors.append(f"{key}: {e}")
                    logger.error(f"Failed to download {key}: {e}")
        
        success = len(downloaded) == len(CSV_URLS)
        error_msg = "; ".join(errors) if errors else None
        return success, downloaded, error_msg
    
    def _delete_all_symbols(self):
        """Delete all symbols from database"""
        try:
            self.db_session.query(SymTokenModel).delete()
            self.db_session.commit()
            logger.info("Cleared symbol table")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error clearing symbols: {e}")
    
    def _bulk_insert(self, df: pd.DataFrame):
        """Bulk insert DataFrame into database"""
        try:
            records = df.to_dict(orient='records')
            self.db_session.bulk_insert_mappings(SymTokenModel, records)
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Bulk insert error: {e}")
            raise
    
    def _reformat_symbol_detail(self, s: str) -> str:
        """Reformat symbol detail string"""
        try:
            parts = s.split()
            return f"{parts[0]}{parts[3]}{parts[2].upper()}{parts[1]}{parts[4]}"
        except:
            return s
    
    def _process_nse_csv(self) -> pd.DataFrame:
        """Process NSE CM CSV"""
        file_path = os.path.join(self.tmp_path, "NSE_CM.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        df = pd.read_csv(file_path, names=HEADERS, dtype=DATA_TYPES)
        
        df['token'] = df['Fytoken']
        df['name'] = df['Symbol Details']
        df['expiry'] = df['Expiry date']
        df['strike'] = df['Strike price']
        df['lotsize'] = df['Minimum lot size']
        df['tick_size'] = df['Tick size']
        df['brsymbol'] = df['Symbol ticker']
        
        # Filter equity and index
        df.loc[df['Exchange Instrument type'].isin([0, 9]), 'exchange'] = 'NSE'
        df.loc[df['Exchange Instrument type'].isin([0, 9]), 'instrumenttype'] = 'EQ'
        df.loc[df['Exchange Instrument type'] == 10, 'exchange'] = 'NSE_INDEX'
        df.loc[df['Exchange Instrument type'] == 10, 'instrumenttype'] = 'INDEX'
        
        df_filtered = df[df['exchange'].isin(['NSE', 'NSE_INDEX'])].copy()
        df_filtered['symbol'] = df_filtered['Underlying symbol']
        df_filtered['brexchange'] = 'NSE'
        
        return self._clean_columns(df_filtered)
    
    def _process_bse_csv(self) -> pd.DataFrame:
        """Process BSE CM CSV"""
        file_path = os.path.join(self.tmp_path, "BSE_CM.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        df = pd.read_csv(file_path, names=HEADERS, dtype=DATA_TYPES)
        
        df['token'] = df['Fytoken']
        df['name'] = df['Symbol Details']
        df['expiry'] = df['Expiry date']
        df['strike'] = df['Strike price']
        df['lotsize'] = df['Minimum lot size']
        df['tick_size'] = df['Tick size']
        df['brsymbol'] = df['Symbol ticker']
        
        df.loc[df['Exchange Instrument type'].isin([0, 4, 50]), 'exchange'] = 'BSE'
        df.loc[df['Exchange Instrument type'].isin([0, 4, 50]), 'instrumenttype'] = 'EQ'
        df.loc[df['Exchange Instrument type'] == 10, 'exchange'] = 'BSE_INDEX'
        df.loc[df['Exchange Instrument type'] == 10, 'instrumenttype'] = 'INDEX'
        
        df_filtered = df[df['Exchange Instrument type'].isin([0, 4, 10, 50])].copy()
        df_filtered['symbol'] = df_filtered['Underlying symbol']
        df_filtered['brexchange'] = 'BSE'
        
        return self._clean_columns(df_filtered)
    
    def _process_nfo_csv(self) -> pd.DataFrame:
        """Process NFO CSV"""
        file_path = os.path.join(self.tmp_path, "NSE_FO.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        df = pd.read_csv(file_path, names=HEADERS, dtype=DATA_TYPES)
        
        df['token'] = df['Fytoken']
        df['name'] = df['Symbol Details']
        df['expiry'] = pd.to_datetime(pd.to_numeric(df['Expiry date'], errors='coerce'), unit='s')
        df['expiry'] = df['expiry'].dt.strftime('%d-%b-%y').str.upper()
        df['strike'] = df['Strike price']
        df['lotsize'] = df['Minimum lot size']
        df['tick_size'] = df['Tick size']
        df['brsymbol'] = df['Symbol ticker']
        df['brexchange'] = 'NFO'
        df['exchange'] = 'NFO'
        df['instrumenttype'] = df['Option type'].str.replace('XX', 'FUT')
        
        # Format symbols
        df.loc[df['Option type'] == 'XX', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x)
        df.loc[df['Option type'] == 'CE', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x) + 'CE'
        df.loc[df['Option type'] == 'PE', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x) + 'PE'
        
        return self._clean_columns(df)
    
    def _process_cds_csv(self) -> pd.DataFrame:
        """Process CDS CSV"""
        file_path = os.path.join(self.tmp_path, "NSE_CD.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        df = pd.read_csv(file_path, names=HEADERS, dtype=DATA_TYPES)
        
        df['token'] = df['Fytoken']
        df['name'] = df['Symbol Details']
        df['expiry'] = pd.to_datetime(pd.to_numeric(df['Expiry date'], errors='coerce'), unit='s')
        df['expiry'] = df['expiry'].dt.strftime('%d-%b-%y').str.upper()
        df['strike'] = df['Strike price']
        df['lotsize'] = df['Minimum lot size']
        df['tick_size'] = df['Tick size']
        df['brsymbol'] = df['Symbol ticker']
        df['brexchange'] = 'CDS'
        df['exchange'] = 'CDS'
        df['instrumenttype'] = df['Option type'].str.replace('XX', 'FUT')
        
        df.loc[df['Option type'] == 'XX', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x)
        df.loc[df['Option type'] == 'CE', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x) + 'CE'
        df.loc[df['Option type'] == 'PE', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x) + 'PE'
        
        return self._clean_columns(df)
    
    def _process_bfo_csv(self) -> pd.DataFrame:
        """Process BFO CSV"""
        file_path = os.path.join(self.tmp_path, "BSE_FO.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        df = pd.read_csv(file_path, names=HEADERS, dtype=DATA_TYPES)
        
        df['token'] = df['Fytoken']
        df['name'] = df['Symbol Details']
        df['expiry'] = pd.to_datetime(pd.to_numeric(df['Expiry date'], errors='coerce'), unit='s')
        df['expiry'] = df['expiry'].dt.strftime('%d-%b-%y').str.upper()
        df['strike'] = df['Strike price']
        df['lotsize'] = df['Minimum lot size']
        df['tick_size'] = df['Tick size']
        df['brsymbol'] = df['Symbol ticker']
        df['brexchange'] = 'BFO'
        df['exchange'] = 'BFO'
        df['instrumenttype'] = df['Option type'].fillna('FUT').str.replace('XX', 'FUT')
        
        df.loc[(df['Option type'] == 'XX') | df['Option type'].isna(), 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x)
        df.loc[df['Option type'] == 'CE', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x) + 'CE'
        df.loc[df['Option type'] == 'PE', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x) + 'PE'
        
        return self._clean_columns(df)
    
    def _process_mcx_csv(self) -> pd.DataFrame:
        """Process MCX CSV"""
        file_path = os.path.join(self.tmp_path, "MCX_COM.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        df = pd.read_csv(file_path, names=HEADERS, dtype=DATA_TYPES)
        
        df['token'] = df['Fytoken']
        df['name'] = df['Symbol Details']
        df['expiry'] = pd.to_datetime(pd.to_numeric(df['Expiry date'], errors='coerce'), unit='s')
        df['expiry'] = df['expiry'].dt.strftime('%d-%b-%y').str.upper()
        df['strike'] = df['Strike price']
        df['lotsize'] = df['Minimum lot size']
        df['tick_size'] = df['Tick size']
        df['brsymbol'] = df['Symbol ticker']
        df['brexchange'] = 'MCX'
        df['exchange'] = 'MCX'
        df['instrumenttype'] = df['Option type'].str.replace('XX', 'FUT')
        
        df.loc[df['Option type'] == 'XX', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x)
        df.loc[df['Option type'] == 'CE', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x) + 'CE'
        df.loc[df['Option type'] == 'PE', 'symbol'] = df['Symbol Details'].apply(
            lambda x: self._reformat_symbol_detail(x) if pd.notnull(x) else x) + 'PE'
        
        return self._clean_columns(df)
    
    def _clean_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only required columns"""
        columns_to_keep = ['symbol', 'brsymbol', 'name', 'exchange', 'brexchange', 
                          'token', 'expiry', 'strike', 'lotsize', 'instrumenttype', 'tick_size']
        return df[[col for col in columns_to_keep if col in df.columns]]
    
    def _cleanup_temp_files(self):
        """Delete temporary CSV files"""
        for filename in os.listdir(self.tmp_path):
            if filename.endswith(".csv"):
                try:
                    os.remove(os.path.join(self.tmp_path, filename))
                except:
                    pass
    
    def search_symbols(self, query: str, exchange: str = None, limit: int = 50) -> List[Dict]:
        """
        Search symbols by name/symbol
        
        Args:
            query: Search query
            exchange: Optional exchange filter
            limit: Max results
            
        Returns:
            List of matching symbols
        """
        try:
            q = self.db_session.query(SymTokenModel).filter(
                SymTokenModel.symbol.ilike(f'%{query}%')
            )
            
            if exchange:
                q = q.filter(SymTokenModel.exchange == exchange)
            
            results = q.limit(limit).all()
            
            return [{
                'symbol': r.symbol,
                'brsymbol': r.brsymbol,
                'name': r.name,
                'exchange': r.exchange,
                'token': r.token,
                'lotsize': r.lotsize,
                'instrumenttype': r.instrumenttype
            } for r in results]
            
        except Exception as e:
            logger.error(f"Symbol search error: {e}")
            return []
    
    def get_symbol(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Get symbol details"""
        try:
            result = self.db_session.query(SymTokenModel).filter(
                SymTokenModel.symbol == symbol,
                SymTokenModel.exchange == exchange
            ).first()
            
            if result:
                return {
                    'symbol': result.symbol,
                    'brsymbol': result.brsymbol,
                    'name': result.name,
                    'exchange': result.exchange,
                    'token': result.token,
                    'lotsize': result.lotsize,
                    'tick_size': result.tick_size,
                    'instrumenttype': result.instrumenttype
                }
            return None
        except Exception as e:
            logger.error(f"Get symbol error: {e}")
            return None
    
    def get_br_symbol(self, symbol: str, exchange: str) -> Optional[str]:
        """Get broker symbol for a given symbol"""
        result = self.get_symbol(symbol, exchange)
        return result['brsymbol'] if result else None
    
    def get_symbol_count(self) -> int:
        """Get total symbol count"""
        try:
            return self.db_session.query(SymTokenModel).count()
        except:
            return 0
