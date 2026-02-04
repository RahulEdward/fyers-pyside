"""
Test Fyers Data Connectivity & Mapping
Run this to verify API keys, Token mapping, and Data fetching.
"""
import sys
import os
import logging
import time

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.database.connection import get_session
from src.database.schema import BrokerCredentialModel, SymTokenModel
from src.services.market_data_service import MarketDataService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestFyers")

def test_connectivity():
    print("\n" + "="*50)
    print("STARTING FYERS CONNECTION TEST")
    print("="*50)

    # 1. Check Database Credentials
    print("\n[1] Checking Database Credentials...")
    session = get_session()
    try:
        creds = session.query(BrokerCredentialModel).first()
        
        if not creds:
            print("No credentials found in database! Please login via the App first.")
            return
        
        if not creds.access_token:
            print("Credentials found but NO Access Token! Login flow incomplete.")
            return
            
        print(f"Found Credentials for user: {creds.broker_username}")
        print(f"Access Token present (Length: {len(creds.access_token)})")
        
        # 2. Check Symbol Mapping (Crucial for Fyers)
        print("\n[2] Checking Master Contract (Symbol) Database...")
        symbol_count = session.query(SymTokenModel).count()
        print(f"Total Symbols in DB: {symbol_count}")
        
        # Always attempt download for testing setup
        print("Diagnosis: Triggering Master Contract Download to ensure fresh data...")
        try:
            from src.services.master_contract_service import MasterContractService
            mcs = MasterContractService(session)
            success, msg = mcs.download_master_contracts(on_progress=lambda x: print(f"    processing {x}"))
            if success:
                print(f"Download Complete: {msg}")
            else:
                print(f"Download Failed: {msg}")
        except Exception as e:
            print(f"Auto-download exception: {e}")
                
        # Debug: Search for NIFTY and SBIN to see what's actually there
        print(f"\n[2.1] Inspecting DB content for 'NIFTY' and 'SBIN'...")
        nifty_matches = session.query(SymTokenModel).filter(SymTokenModel.symbol.like("%NIFTY%")).limit(5).all()
        for m in nifty_matches:
            print(f"   found: symbol='{m.symbol}', exchange='{m.exchange}', brsymbol='{m.brsymbol}'")
            
        sbin_matches = session.query(SymTokenModel).filter(SymTokenModel.symbol.like("%SBIN%")).limit(5).all()
        for m in sbin_matches:
            print(f"   found: symbol='{m.symbol}', exchange='{m.exchange}', brsymbol='{m.brsymbol}'")

        test_symbol = "NIFTY 50"
        test_exchange = "NSE"
        
        # Try looking up NIFTY 50
        nifty = session.query(SymTokenModel).filter(
            SymTokenModel.symbol == test_symbol,
            SymTokenModel.exchange == test_exchange
        ).first()
        
        if nifty:
            print(f"Found {test_symbol}: Token={nifty.token}, BrSymbol={nifty.brsymbol}")
        else:
            print(f"Could NOT find {test_symbol} in database.")
            print("   CRITICAL: If database is empty or missing symbols, Live Data WILL NOT WORK.")
            print("   Solution: You need to run 'Download Master Contracts'.")
        
        token = creds.access_token
        
    finally:
        session.close()
    
    print(f"\n[2.5] Verifying Token Resolution for SBIN-EQ...")
    try:
        from src.database.token_db import get_br_symbol
        br_sym = get_br_symbol("SBIN-EQ", "NSE")
        print(f"      get_br_symbol('SBIN-EQ', 'NSE') -> {br_sym} (Type: {type(br_sym)})")
        
        if not br_sym:
            print("      Could not resolve SBIN-EQ! History/Quote will fail.")
            # Verify NIFTY 50 too
            br_nifty = get_br_symbol("NIFTY 50", "NSE")
            print(f"      get_br_symbol('NIFTY 50', 'NSE') -> {br_nifty}")
            
    except Exception as e:
        print(f"      Token Resolution Error: {e}")

    # 3. Test API Fetching (Historical & Quotes)
    print("\n[3] Testing Fyers API Data Fetching...")
    service = MarketDataService(token)
    
    # Check if initialized
    if service._broker_data is None:
        print("   Fyers API (BrokerData) failed to initialize!")
        print("      This usually means an ImportError or missing dependency.")
        # Try manual import to see error
        try:
            from fyers.api.data import BrokerData
            print("      Manual import of BrokerData SUCCEEDED (unexpected).")
        except Exception as e:
            print(f"      Manual import ERROR: {e}")
    else:
        print("   Fyers API initialized successfully.")
    
    # Test Quote
    print("   Requesting Quote for NSE:SBIN-EQ (State Bank of India)...")
    try:
        quote_res = service.get_quote("SBIN-EQ", "NSE")
        
        if quote_res.is_ok():
            q = quote_res.value
            print(f"   Quote Success: {q.symbol} LTP = {q.ltp} ({q.change_pct:.2f}%)")
        else:
            print(f"   Quote Failed: {quote_res.error}")
            
    except Exception as e:
        print(f"   Quote Exception: {e}")

    # Test Historical
    print("\n   Requesting Historical Data (Candles)...")
    try:
        # Corrected arguments: start_date, end_date
        hist_res = service.get_historical_data("SBIN-EQ", "NSE", start_date="2024-01-01", end_date="2024-01-05")
        if hist_res.is_ok():
            df = hist_res.value
            if not df.empty:
                print(f"   Historical Data Received: {len(df)} candles")
                print(df.head(2))
            else:
                print("   Historical Data response was empty (but successful).")
        else:
            print(f"   Historical Failed: {hist_res.error}")

    except Exception as e:
        print(f"   Historical Exception: {e}")

    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)

if __name__ == "__main__":
    test_connectivity()
