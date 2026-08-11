import os
from dotenv import load_dotenv

load_dotenv()

# --- File paths ------------
DATA_DIR = 'data'
EXPENSES_FILE = os.path.join(DATA_DIR, 'expenses_data.json')
RATE_FALLBACK_FILE = os.path.join(DATA_DIR, 'last_known_rate.json')

