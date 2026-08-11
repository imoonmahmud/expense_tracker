import requests
import json
from datetime import datetime

import config

# Notion API calls
def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.NOTION_API_KEY}",
        "Notion-Version": config.NOTION_VERSION,
        "Content-Type": "application/json"
    }

def _to_iso_date(date_str: str) -> str:
    return datetime.strptime(date_str, '%b %d, %Y').strftime('%Y-%m-%d')

def _expense_properties(expense: dict) -> dict:
    return {
        'Description': {'title': [{'text': {'content': expense['description']}}]},
        'Amount': {'number': expense['amount']},
        'ID': {'number': expense['id']},
        'Date': {'date': {'start': _to_iso_date(expense['created_at'])}}
    }

def create_expense_page(expense: dict) -> str:
    # Create a notion page for expense and the returns the new page ID.
    payload = {
        'parent': {'database_id': config.NOTION_DATABASE_ID},
        'properties': _expense_properties(expense)
    }
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=_headers(),
        json=payload,
        timeout=config.NOTION_TIMEOUT
    )
    response.raise_for_status()
    return response.json()['id']

# Offline queue, each entry is one of:
#   {'op': 'create', 'expense_id': 5}
#   {'op': 'update', 'expense_id': 5}
#   {'op': 'delete', 'expense_id': 5, 'page_id': '...'}
# 'delete' carries its own page_id because by the time it's queued, the
# expense has already been removed from expenses_data.json there'd be
# nothing left to look it up from.

def load_queue() -> list:
    try:
        with open(config.SYNC_QUEUE_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_queue(queue: list) -> list:
    with open(config.SYNC_QUEUE_FILE, 'w', encoding='utf-8') as file:
        json.dump(queue, file, indent=4)

def queue_create(expense_id: int) -> None:
    queue = load_queue()
    queue.append({'record': 'expense', 'op': 'create', 'expense_id': expense_id})
    save_queue(queue)



# Immediate sync attempts
def try_sync_create(expense: dict) -> bool:
    if not config.notion_configured():
        return False
    try:
        page_id = create_expense_page(expense)
        expense['notion_page_id'] = page_id
        return True
    except requests.exceptions.RequestException as e:
        print("Note: couldn't reach Notion - will sync later:", e)
        queue_create(expense['id'])
        return False

