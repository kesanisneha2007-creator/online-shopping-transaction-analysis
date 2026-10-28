# Online Shopping Transaction Analysis System

A Flask + MySQL web application for managing products, orders, and order items, with transaction-level analysis using Pandas and NumPy and charts generated with Matplotlib.

## Features

- Add and view products.
- Create orders with product, quantity, date, payment method, and status.
- View calculated order totals and order line items.
- Update order status.
- Reports for average order value, total eligible order value, units sold, and order-status/payment-method/monthly charts.
- `/health` endpoint to verify the application and database connection.

## Business rules and assumptions

- Each new order currently contains one product line. The `order_items` schema supports multiple lines per order; the UI can be extended with a dynamic multi-line form.
- The order total is calculated from `SUM(quantity * unit_price)` in `order_items`; it is not stored as a manually entered total.
- `unit_price` is copied into `order_items` when the order is created, preserving the price at the time of purchase even if a product's price changes later.
- Cancelled and Refunded orders are excluded from the transaction value, average order value, and units-sold analysis. They remain included in the total order count, monthly order volume, and order-status chart so operational activity remains visible.
- Average order value = sum of eligible order totals / number of eligible orders. Eligible means not Cancelled or Refunded.
- This is a learning/demo project. Add authentication, authorization, CSRF protection, migrations, validation, and production server configuration before deploying publicly.

## Folder structure

```text
online_shopping_transaction_analysis/
├── app.py
├── schema.sql
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── setup_error.html
│   ├── products.html
│   ├── product_form.html
│   ├── orders.html
│   ├── order_form.html
│   ├── order_detail.html
│   └── reports.html
└── static/
    ├── css/style.css
    └── generated/  # charts are generated here at runtime
```

## Requirements

- Python 3.10 or newer
- MySQL Server 8.x (or a compatible MySQL server)
- Git
- A terminal (Windows PowerShell, macOS Terminal, or Linux shell)

## Run locally

### 1. Create the database and tables

Start MySQL, then run the SQL file from the project folder:

```bash
mysql -u root -p < schema.sql
```

Enter your MySQL password when prompted. `schema.sql` includes optional sample records. If you want an empty database, remove the sample `INSERT` statements before running it.

Alternatively, open `schema.sql` in MySQL Workbench and execute it.

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure database credentials

Copy `.env.example` to `.env`, then edit `.env` with your local MySQL username and password.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Do not commit `.env` to Git. It is ignored by `.gitignore`.

### 5. Start the Flask application

```bash
python app.py
```

Open the local URL shown in the terminal, usually `http://127.0.0.1:5000`.

Pages:
- `/` — dashboard
- `/products` — product list
- `/products/add` — add a product
- `/orders` — orders
- `/orders/add` — create an order
- `/reports` — transaction analysis and charts
- `/health` — database connection check

## Troubleshooting

- **Access denied for user**: verify `DB_USER` and `DB_PASSWORD` in `.env`.
- **Unknown database**: run `schema.sql` successfully and verify `DB_NAME`.
- **Can't connect to MySQL server**: ensure the MySQL service is running and `DB_HOST` / `DB_PORT` are correct.
- **ModuleNotFoundError**: activate `.venv` and run `pip install -r requirements.txt`.
- **Charts not appearing**: open `/reports` after adding data; Matplotlib charts are regenerated from the database.
- **Port 5000 is in use**: stop the other process or change the port in `app.run(...)`.

## Push the project to GitHub

1. Create a new **empty** repository on GitHub (do not initialize it with a README if you already have this one).
2. In a terminal, move into this project folder.
3. Run:

```bash
git init
git add .
git status
git commit -m "Build online shopping transaction analysis system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/online-shopping-transaction-analysis.git
git push -u origin main
```

Replace the remote URL with your actual GitHub repository URL. If Git asks you to sign in, complete the browser authentication prompt or use Git Credential Manager. Do not place passwords, access tokens, or `.env` values in source code or commits.

If you have already initialized Git, do not run `git init` again. If `origin` already exists, inspect it with `git remote -v` rather than adding it twice.

## Suggested future improvements

- Multi-item order form.
- Search/filter and pagination.
- Export reports to CSV.
- Login roles for administrator/staff.
- Automated tests and database migrations.
- Deploy to a platform that supports Flask and MySQL.
