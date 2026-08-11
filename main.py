import argparse

import config
import notion_sync
from expenses import (
    load_expenses,
    save_expenses,
    add_expense,
    list_expenses,
    update_expense,
    delete_expense,
    total_summary,
    month_summary
)
from budgets import (
    load_budgets,
    save_budgets,
    set_budget,
    check_budget,
    close_finished_months
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='command')

    add_parser = subparser.add_parser('add')
    add_parser.add_argument('description')
    add_parser.add_argument('amount', type=float)

    list_parser = subparser.add_parser('list')
    list_parser.add_argument('-m', '--month', default=None)

    update_parser = subparser.add_parser('update')
    update_parser.add_argument('expense_id', type=int)
    update_parser.add_argument('-d', '--description', default=None)
    update_parser.add_argument('-a', '--amount', type= float, default=None)

    delete_parser = subparser.add_parser('delete')
    delete_parser.add_argument('expense_id', type=int)

    summary_parser = subparser.add_parser('summary')
    summary_parser.add_argument('-m' '--month', default=None)

    add_budget_parser = subparser.add_parser('add_budget')
    add_budget_parser.add_argument('budget', type=float)
 
    subparser.add_parser('sync_status')


    return parser

def main():
    args = build_parser().parse_args()

    expenses = load_expenses(config.EXPENSES_FILE)
    budgets_data = load_budgets(config.BUDGETS_FILE)

    # Catch up anything that couldn't reach Notion
    if notion_sync.sync_pending_operations(expenses, budgets_data):
        save_expenses(expenses, config.EXPENSES_FILE)
        save_budgets(budgets_data, config.BUDGETS_FILE)
 
    if close_finished_months(expenses, budgets_data):
        save_budgets(budgets_data, config.BUDGETS_FILE)


    match args.command:
        case 'add':
            if args.amount <= 0:
                print('Error: amount must be greater than 0.')
            else:
                expense = add_expense(expenses, args.description, args.amount)
                save_expenses(expenses, config.EXPENSES_FILE)
                print(f"Expense added successfully (ID: {expense['id']})")
                check_budget(expenses, budgets_data)

        case 'list':
            list_expenses(expenses, args.month)

        case 'update':
            if args.amount is not None and args.amount <= 0:
                print('Error: amount must be greater than 0.')
            elif args.description is None and args.amount is None:
                print('Error: provide at least one of --description or --amount to update.')
            else:
                expense = update_expense(expenses, args.expense_id, args.description, args.amount)
                if expense is None:
                    print(f'No expense found with ID {args.expense_id}')
                else:
                    save_expenses(expenses, config.EXPENSES_FILE)
                    print(f'Expense {args.expense_id} updated successfully')

        case 'delete':
            if delete_expense(expenses, args.expense_id):
                save_expenses(expenses, config.EXPENSES_FILE)
                print(f'Expense ID {args.expense_id} deleted successfully')
            else:
                print(f'No expense found with ID {args.expense_id}')

        case 'summary':
            if args.month is None:
                print(f'Total expenses: ${total_summary(expenses)}')
            else:
                print(f'Total expenses for {args.month.capitalize()}: ${month_summary(expenses, args.month)}')

        case 'add_budget':
            set_budget(budgets_data, args.budget)
            save_budgets(budgets_data, config.BUDGETS_FILE)
            print('Added budget successfully.')
 
        case 'sync_status':
            if not (config.notion_configured() or config.budgets_notion_configured()):
                print('Notion sync isn\'t set up (no credentials in .env) — everything is local-only.')
            else:
                pending = notion_sync.describe_pending_operations(expenses, budgets_data)
                if not pending:
                    print('Everything is synced with Notion.')
                else:
                    print(f'{len(pending)} change(s) waiting to sync to Notion:')
                    for line in pending:
                        print(f'  - {line}')
 
        case _:
            print('Unknown command. Run with -h to see available commands.')

        


if __name__ == '__main__':
    main()