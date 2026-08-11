import json
from datetime import datetime

from prettytable import PrettyTable

import config
from exchange_rate import get_rate_with_fallback


def load_expenses(path: str = config.EXPENSES_FILE) -> list:
    try:
        with open(path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    for expense in data:
        expense.setdefault('notion_page_id', None)
    return data

def save_expenses(data: list, path: str = config.EXPENSES_FILE) -> None:
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def add_expense(data: list, description: str, amount_tk: float) -> dict:
    existing_ids = [expense['id'] for expense in data]
    next_id = max(existing_ids) + 1 if existing_ids else 1
    date = datetime.now().strftime('%b %d, %Y')
    rate = get_rate_with_fallback()
    amount_usd = round(amount_tk * rate, 2)

    expense ={
        'id': next_id,
        'description': description,
        'amount': amount_usd,
        'created_at': date,
        'notion_page_id': None
    }

    data.append(expense)
    return expense