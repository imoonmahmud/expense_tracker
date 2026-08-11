import json
from datetime import datetime

from prettytable import PrettyTable

import config
import notion_sync
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
    notion_sync.try_sync_create(expense)
    return expense

def list_expenses(data: list, month: str = None) -> None:
    filtered = data
    if month is not None:
        filtered = [e for e in filtered if e['created_at'].split(' ')[0] == month[:3].capitalize()]
    if not filtered:
        print('No expenses fount.')
        return
    table = PrettyTable()
    table.field_names = ['ID', 'Date', 'Description', 'Amount']
    for expense in filtered:
        table.add_row([
            expense['id'],
            expense['created_at'],
            expense['description'],
            f"${expense['amount']}",
        ])
    print(table)

def update_expense(data:list, expense_id: int, description: str, amount:float) -> float:
    amount_usd = None
    if amount is not None:
        rate = get_rate_with_fallback()
        amount_usd = round(amount * rate, 2)
    for expense in data:
        if expense['id'] == expense_id:
            if description is not None:
                expense['description'] = description
            if amount_usd is not None:
                expense['amount'] = amount_usd
            notion_sync.try_sync_update(expense)
            return expense
    return None

def delete_expense(data: list, expense_id: int) -> bool:
    target = next((expense for expense in data if expense['id'] == expense_id), None)
    if target is None:
        return False
    page_id = target.get('notion_page_id')
    data[:] = [expense for expense in data if expense['id'] != expense_id]
    notion_sync.try_sync_delete(expense_id, page_id)
    return True
 
def total_summary(data: list) -> float:
    return round(sum(expense['amount'] for expense in data), 2)
 
def month_summary(data: list, month: str) -> float:
    total = 0
    for expense in data:
        expense_month = expense['created_at'].split(' ')[0]
        if expense_month == month[:3].capitalize():
            total += expense['amount']
    return round(total, 2)