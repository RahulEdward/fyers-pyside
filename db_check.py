from src.database.connection import get_session
from src.database.schema import SymTokenModel

session = get_session()
try:
    print("Searching ALL NIFTY in NSE_INDEX...")
    # Search specific indices
    results = session.query(SymTokenModel).filter(
        SymTokenModel.exchange == 'NSE_INDEX',
        SymTokenModel.symbol.like("%NIFTY%")
    ).all()
    
    found = False
    for r in results:
        # Check against "NIFTY 50" variants
        if "50" in r.symbol and "NIFTY" in r.symbol:
            print(f"MATCH: '{r.symbol}' (len={len(r.symbol)}) -> '{r.brsymbol}'")
            found = True
            
    if not found:
        print("No NIFTY 50 variant found in NSE_INDEX.")
        
    print(f"Total NIFTY indices found: {len(results)}")

finally:
    session.close()
