# Expense Tracker

A command-line expense tracker with monthly budgets **offline-first sync to Notion**. Track spending from the terminal, even without an internet connection, and have it automatically catch up with your Notion database once you're back online.

Project idea based on roadmap.sh's Expense Tracker, extended with categories, budget warnings, and Notion integration.

## Features

- Add, update, delete, and list expenses
- Filter expenses by month
- Spending summaries: overall total, or total for a specific month
- Budget warnings: set a monthly limit and get warned at 80% and over-budget
- Automatic month closing: once a budgeted month ends, its final total is recorded automatically
- **Notion sync**: every change pushes to a connected Notion database
- **Offline-first**: no internet or a failed API call queues the change locally instead of losing it; the queue automatically syncs once you're back online
- Installed as a global `expense` command, works from any folder, like `git`

## Requirements

- Python 3.10+
- `prettytable` — for formatted table output
- `python-dotenv` — for loading Notion API credentials from a `.env` file
- A free Notion account + integration (for sync features)

## Installation

### 1. Clone and set up

```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker
pip install -r requirements.txt
```

### 2. Set up Notion sync (optional but recommended)

1. Create an integration at notion.so/my-integrations and copy the secret
2. Create a Notion database with these columns: `Description` (Title), `Amount` (Number), `Category` (Text), `Date` (Date)
3. Share the database with your integration (database page → **...** → **Connections**)
4. Create a `.env` file in the project root:
   ```
   NOTION_API_KEY=your_secret_here
   NOTION_DATABASE_ID=your_database_id_here
   ```

### 3. Install as a global command

```bash
pipx install -e .
```

This makes `expense` available from any folder, without needing to activate a virtual environment or type `python main.py` every time.

## Usage

### Add an expense
```bash
expense add "Lunch" 20
expense add "Bus fare" 40 -c Transport
```

### List expenses
```bash
expense list
expense list -m August
expense list -c Food
expense list -m August -c Food
```

### Update an expense
```bash
expense update 1 "New description"
expense update 1 -a 25
expense update 1 "New description" -a 25 -c Food
```

### Delete an expense
```bash
expense delete 1
```

### Summaries
```bash
expense summary              # total of everything
expense summary -m August    # total for one month
```

### Budgets
```bash
expense set-budget "September, 2026" 500
```
A warning appears automatically when adding an expense pushes that month's spending past 80% of its budget, and again once it goes over.

### Sync status
```bash
expense sync_status
```
Shows any changes waiting to be pushed to Notion (e.g. if they were made while offline).

## How the offline-first sync works

1. Every change (`add`, `update`, `delete`) tries to push to Notion immediately.
2. If that fails — no internet, a Notion API error, a timeout — the change is written to a local **sync queue** file instead of being lost.
3. Your local `expenses_data.json` always updates regardless, so the app works fully offline.
4. Every time the program starts, it checks the sync queue and retries anything pending. If Notion is reachable again, those changes go through and get cleared from the queue.

## Data storage

Data lives in a fixed location tied to your user account, not the folder you happen to run `expense` from the same approach as `git` uses for global config:

```
~/.expense_tracker/
├── expenses_data.json
├── budgets.json
└── sync_queue.json
```

This matters because `expense` is a global command — if data were stored using a relative path, it would only find that data when run from inside the original project folder.

## Project structure

```
expense-tracker/
├── main.py             # CLI entry point, argparse setup, and dispatch
├── functions.py         # Core expense logic (add/list/update/delete/summary)
├── budget_functions.py  # Budget setting, checking, and month-closing logic
├── notion_sync.py       # Notion API calls + offline sync queue
├── config.py             # Paths, environment variables, constants
├── pyproject.toml        # Packaging config (makes `expense` installable)
└── README.md
```

## Acknowledgements

Core project idea from roadmap.sh — Expense Tracker.
