import os
from dotenv import load_dotenv

load_dotenv()

# --- File paths
DATA_DIR = 'data'
EXPENSES_FILE = os.path.join(DATA_DIR, 'expenses_data.json')
RATE_FALLBACK_FILE = os.path.join(DATA_DIR, 'last_known_rate.json')
SYNC_QUEUE_FILE = os.path.json(DATA_DIR, 'sync_queue.json')

# --- Notion credntials
NOTION_API_KEY = os.environ.get('NOTION_API_KEY')
NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')  # expenses database
NOTION_BUDGETS_DATABASE_ID = os.environ.get('NOTION_BUDGETS_DATABASE_ID')
NOTION_VERSION = '2022-06-28'
NOTION_TIMEOUT = 5  # seconds

def notion_configured() -> bool:
    return bool(NOTION_API_KEY and NOTION_DATABASE_ID)