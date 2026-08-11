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

def update_expense_page(page_id: str, expense: dict) -> None:
    payload = {"properties": _expense_properties(expense)}
    response = requests.patch(
        f'https://api.notion.com/v1/pages/{page_id}',
        headers=_headers(),
        json=payload,
        timeout=config.NOTION_TIMEOUT
    )
    response.raise_for_status()

def archive_expense_page(page_id: str) -> None:
    payload = {'archived': True}
    response = requests.patch(
        f'https://api.notion.com/v1/pages/{page_id}',
        headers=_headers(),
        json=payload,
        timeout=config.NOTION_TIMEOUT
    )
    response.raise_for_status()

# --- Budget pages
def _budget_properties(month_key: str, info: dict) -> dict:
    properties = {
        "Month": {"title": [{"text": {"content": month_key}}]},
        "Limit": {"number": info['limit']}
    }
    if info.get('actual') is not None:
        properties["Actual"] = {"number": info['actual']}
    return properties

def create_budget_page(month_key: str, info: dict) -> str:
    payload = {
        "parent": {"database_id": config.NOTION_BUDGETS_DATABASE_ID},
        "properties": _budget_properties(month_key, info)
    }
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=_headers(),
        json=payload,
        timeout=config.NOTION_TIMEOUT
    )
    response.raise_for_status()
    return response.json()['id']

def update_budget_page(page_id: str, month_key: str, info: dict) -> None:
    payload = {"properties": _budget_properties(month_key, info)}
    response = requests.patch(
        f'https://api.notion.com/v1/pages/{page_id}',
        headers=_headers(),
        json=payload,
        timeout=config.NOTION_TIMEOUT
    )
    response.raise_for_status()

def create_budget_page(month_key: str, info: dict) -> str:
    """Create a Notion page for this budget month. Returns the new page ID."""
    payload = {
        "parent": {"database_id": config.NOTION_BUDGETS_DATABASE_ID},
        "properties": _budget_properties(month_key, info)
    }
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=_headers(),
        json=payload,
        timeout=config.NOTION_TIMEOUT
    )
    response.raise_for_status()
    return response.json()['id']
 
 
def update_budget_page(page_id: str, month_key: str, info: dict) -> None:
    payload = {"properties": _budget_properties(month_key, info)}
    response = requests.patch(
        f'https://api.notion.com/v1/pages/{page_id}',
        headers=_headers(),
        json=payload,
        timeout=config.NOTION_TIMEOUT
    )
    response.raise_for_status()

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

def queue_update(expense_id: int) -> None:
    queue = load_queue()
    queue.append({'record': 'expense', 'op': 'update', 'expense_id': expense_id})
    save_queue(queue)

def queue_delete(expense_id: int, page_id) -> None:
    queue = load_queue()
    queue.append({'record': 'expense', 'op': 'delete', 'expense_id': expense_id, 'page_id': page_id})
    save_queue(queue)

def drop_pending_ops_for(expense_id: int) -> None:
    # Remove any queued create/update for an expense that added while offline
    queue = load_queue()
    queue = [op for op in queue
             if not (op.get('record') == 'expense' and op['op'] in ('create', 'update') and op['expense_id'] == expense_id)]
    save_queue(queue)

def find_expense(expenses: list, expense_id: int):
    for expense in expenses:
        if expense['id'] == expense_id:
            return expense
    return None

def find_budget(budgets: list, month_key: str):
    """Budgets are stored as a list of single-key dicts, e.g.
    [{'August, 2026': {'limit': ..., 'actual': ..., 'notion_page_id': ...}}].
    Returns the inner info dict for month_key, or None."""
    for budget in budgets:
        if month_key in budget:
            return budget[month_key]
    return None

def queue_budget_create(month_key: str) -> None:
    queue = load_queue()
    queue.append({'record': 'budget', 'op': 'create', 'month_key': month_key})
    save_queue(queue)
 
 
def queue_budget_update(month_key: str) -> None:
    queue = load_queue()
    queue.append({'record': 'budget', 'op': 'update', 'month_key': month_key})
    save_queue(queue)

def describe_pending_operations(expenses: list, budgets: list) -> list:
    lines = []
    for op in load_queue():
        record = op.get('record', 'expense')
 
        if record == 'expense':
            expense = find_expense(expenses, op['expense_id'])
            label = f"expense #{op['expense_id']}"
            if expense is not None:
                label += f" ({expense['description']})"
            lines.append(f"{op['op']} {label}")
 
        else:  # 'budget'
            label = f"budget {op['month_key']}"
            lines.append(f"{op['op']} {label}")
 
    return lines

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

def try_sync_update(expense: dict) -> bool:
    if not config.notion_configured():
        return False
    page_id = expense.get('notion_page_id')
    if not page_id:
        # No page exists in the notion database, nothing to update
        return False
    try:
        update_expense_page(page_id, expense)
        return True
    except requests.exceptions.RequestException as e:
        print("Note: couldn't reach Notion - will sync later:", e)
        queue_update(expense['id'])
        return False

def try_sync_delete(expense_id: int, page_id: str) -> bool:
    if not config.notion_configured():
        return False
    if not page_id:
        drop_pending_ops_for(expense_id)
        return False
    try:
        archive_expense_page(page_id)
        return True
    except requests.exceptions.RequestException as e:
        print("Note: couldn't reach Notion - will sync later:", e)
        queue_delete(expense_id, page_id)
        return False

def try_sync_budget_create(month_key: str, info: dict) -> bool:
    if not config.budgets_notion_configured():
        return False
    try:
        page_id = create_budget_page(month_key, info)
        info['notion_page_id'] = page_id
        return True
    except requests.exceptions.RequestException as e:
        print("Note: couldn't reach Notion - will sync later:", e)
        queue_budget_create(month_key)
        return False

def try_sync_budget_update(month_key: str, info: dict) -> bool:
    if not config.budgets_notion_configured():
        return False
    page_id = info.get('notion_page_id')
    if not page_id:
        # No page exists yet a pending 'create' will pick up current data.
        return False
    try:
        update_budget_page(page_id, month_key, info)
        return True
    except requests.exceptions.RequestException as e:
        print("Note: couldn't reach Notion - will sync later:", e)
        queue_budget_update(month_key)
        return False

# --- Flushing the queue called once at the start of every run
def sync_pending_operations(expenses: list, budgets: list = None) -> bool:
    if not (config.notion_configured() or config.budgets_notion_configured()):
        return False
 
    budgets = budgets or []
    remaining = load_queue()
    data_changed = False
 
    while remaining:
        op = remaining[0]
 
        try:
            if op.get('record', 'expense') == 'expense':
                if op['op'] == 'create':
                    expense = find_expense(expenses, op['expense_id'])
                    if expense is not None:
                        page_id = create_expense_page(expense)
                        expense['notion_page_id'] = page_id
                        data_changed = True
 
                elif op['op'] == 'update':
                    expense = find_expense(expenses, op['expense_id'])
                    if expense is not None and expense.get('notion_page_id'):
                        update_expense_page(expense['notion_page_id'], expense)
 
                elif op['op'] == 'delete':
                    if op.get('page_id'):
                        archive_expense_page(op['page_id'])
 
            elif op['record'] == 'budget':
                month_key = op['month_key']
                info = find_budget(budgets, month_key)
                if info is None:
                    pass  # budget entry no longer exists — nothing to sync
                elif op['op'] == 'create':
                    page_id = create_budget_page(month_key, info)
                    info['notion_page_id'] = page_id
                    data_changed = True
                elif op['op'] == 'update' and info.get('notion_page_id'):
                    update_budget_page(info['notion_page_id'], month_key, info)
 
        except requests.exceptions.RequestException:
            break  # still offline (or Notion is down) keep the rest queued
 
        remaining.pop(0)
 
    save_queue(remaining)
    return data_changed