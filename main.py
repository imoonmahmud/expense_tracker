import argparse

import config
from expenses import (
    load_expenses,
    save_expenses,
    add_expense
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='command')

    add_parser = subparser.add_parser('add')
    add_parser.add_argument('description')
    add_parser.add_argument('amount', type=float)


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


if __name__ == '__main__':
    main()