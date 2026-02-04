"""
Token Database Helpers
Bridging module for Fyers API code to access symbol data
"""
from typing import Optional
from src.database.connection import get_session
from src.database.schema import SymTokenModel

def get_br_symbol(symbol: str, exchange: str) -> Optional[str]:
    """Get broker symbol from database"""
    try:
        session = get_session()
        try:
            # 1. Exact match
            result = session.query(SymTokenModel).filter(
                SymTokenModel.symbol == symbol,
                SymTokenModel.exchange == exchange
            ).first()
            if result: return result.brsymbol
            
            # 2. Check Index segments (NSE_INDEX, BSE_INDEX)
            if exchange == "NSE":
                result = session.query(SymTokenModel).filter(
                    SymTokenModel.symbol == symbol,
                    SymTokenModel.exchange == "NSE_INDEX"
                ).first()
                if result: return result.brsymbol
                
            if exchange == "BSE":
                result = session.query(SymTokenModel).filter(
                    SymTokenModel.symbol == symbol,
                    SymTokenModel.exchange == "BSE_INDEX"
                ).first()
                if result: return result.brsymbol
            
            # 4. Hardcoded Fallbacks for Indices (if missing in DB)
            if symbol == "NIFTY 50" and exchange == "NSE":
                return "NSE:NIFTY50-INDEX"
            if symbol == "SENSEX" and exchange == "BSE":
                return "BSE:SENSEX-INDEX"
            if symbol == "BANKNIFTY" and exchange == "NSE":
                return "NSE:NIFTYBANK-INDEX"
            
            # 5. Try common suffixes (Equity/Derivatives)
            if exchange == "NSE":
                variations = [
                    f"{symbol}-EQ",
                    f"{symbol}-INDEX",
                    f"{symbol.replace(' ', '')}-INDEX", # NIFTY 50 -> NIFTY50-INDEX fallback
                    f"{symbol} " 
                ]
                for v in variations:
                    result = session.query(SymTokenModel).filter(
                        SymTokenModel.symbol == v,
                        SymTokenModel.exchange == exchange
                    ).first()
                    if result: return result.brsymbol
            
            return None
        finally:
            session.close()
    except Exception:
        return None

def get_oa_symbol(token: str, exchange: str = None) -> Optional[str]:
    """Get OpenAlgo symbol from token/ticker"""
    try:
        session = get_session()
        try:
            # Try by token first
            query = session.query(SymTokenModel)
            if exchange:
                query = query.filter(SymTokenModel.exchange == exchange)
            
            result = query.filter(SymTokenModel.token == str(token)).first()
            if result:
                return result.symbol
                
            # Try by brsymbol
            query = session.query(SymTokenModel)
            if exchange:
                query = query.filter(SymTokenModel.exchange == exchange)
            result = query.filter(SymTokenModel.brsymbol == str(token)).first()
            if result:
                return result.symbol
                
            return None
        finally:
            session.close()
    except Exception:
        return None
