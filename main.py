import argparse

import config
from expenses import (
    load_expenses,
    save_expenses,
    add_expense,
    list_expenses
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='command')

    add_parser = subparser.add_parser('add')
    add_parser.add_argument('description')
    add_parser.add_argument('amount', type=float)

    list_parser = subparser.add_parser('list')
    list_parser.add_argument('-m', '--month', default=None)


    return parser

def main():
    args = build_parser().parse_args()

    expenses = load_expenses(config.EXPENSES_FILE)


    match args.command:
        case 'add':
            if args.amount <= 0:
                print('Error: amount must be greater than 0.')
            else:
                expense = add_expense(expenses, args.description, args.amount)
                save_expenses(expenses, config.EXPENSES_FILE)
                print(f"Expense added successfully (ID: {expense['id']})")

        case 'list':
            list_expenses(expense, args.month)

        


if __name__ == '__main__':
    main()