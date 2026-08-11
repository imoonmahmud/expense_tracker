import json
from datetime import datetime

import config
import notion_sync
from expenses import month_summary
from exchange_rate import get_rate_with_fallback

def load_budgets(path: str = config.BUDGETS_FILE) -> list:
    try:
        with open(path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    if not isinstance(data, list):
        return []
    for budget in data:
        for info in budget.values():
            info.setdefault('notion_page_id', None)
    return data

def save_budgets(data: list, path: str = config.BUDGETS_FILE) -> None:
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def set_budget(budgets_data: list, limit_tk: float) -> list:
    rate = get_rate_with_fallback()
    limit_usd = round(limit_tk * rate, 2)
    month_and_year = datetime.now().strftime('%B, %Y')
    info = {'limit': limit_usd, 'actual': None, 'notion_page_id': None}
    budgets_data.append({month_and_year: info})
    notion_sync.try_sync_budget_create(month_and_year, info)
    return budgets_data

def check_budget(expenses: list, budgets: list) -> None:
    month_and_year = datetime.now().strftime('%B, %Y')
    month = datetime.now().strftime('%B')
    actual_amount = month_summary(expenses, month)
 
    for budget in budgets:
        info = budget.get(month_and_year)
        if info is None:
            continue  # this entry is for a different month — skip it
 
        limit = info['limit']
        if actual_amount > limit:
            print(f"Warning: you've spent ${actual_amount} this month, over your ${limit} budget")
        elif actual_amount < limit and actual_amount + 10 >= limit:
            print(f"Warning: you're close — ${actual_amount} spent against your ${limit} budget")

def close_finished_months(expenses: list, budgets: list) -> bool:
    current_month_start = datetime.now().replace(day=1)
    changed = False
    for budget in budgets:
        for month_str, info in budget.items():
            month_start = datetime.strptime(month_str, "%B, %Y").replace(day=1)
            if month_start < current_month_start and info.get('actual') is None:
                info['actual'] = month_summary(expenses, month_str[:3])
                notion_sync.try_sync_budget_update(month_str, info)
                changed = True
    return changed