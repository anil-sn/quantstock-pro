import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.context import get_market_context
from app.models import MarketContext

print("Attempting to fetch context for AAPL...")
try:
    ctx = get_market_context("AAPL")
    print("Success!")
    print(ctx.model_dump_json(indent=2))
except Exception as e:
    print(f"CRASHED: {e}")
    import traceback
    traceback.print_exc()
