import os
from datetime import date
from decimal import Decimal
from functools import wraps

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-key")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "shopping_analysis"),
}
CHART_DIR = os.path.join(app.static_folder, "generated")
os.makedirs(CHART_DIR, exist_ok=True)


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def query_all(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def execute(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def create_charts():
    """Build charts from non-cancelled/non-refunded orders unless noted."""
    orders = query_all("""
        SELECT o.order_id, o.order_date, o.payment_method, o.order_status,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS order_total
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        GROUP BY o.order_id, o.order_date, o.payment_method, o.order_status
        ORDER BY o.order_date
    """)
    items = query_all("""
        SELECT p.product_name, COALESCE(SUM(oi.quantity), 0) AS units_sold
        FROM products p
        LEFT JOIN order_items oi ON oi.product_id = p.product_id
        LEFT JOIN orders o ON o.order_id = oi.order_id
             AND o.order_status NOT IN ('Cancelled', 'Refunded')
        WHERE oi.item_id IS NULL OR o.order_id IS NOT NULL
        GROUP BY p.product_id, p.product_name
        ORDER BY units_sold DESC, p.product_name
        LIMIT 10
    """)
    if not orders:
        for name in ["monthly_orders.png", "payment_methods.png", "order_status.png", "top_products.png"]:
            p = os.path.join(CHART_DIR, name)
            if os.path.exists(p):
                os.remove(p)
        return

    df = pd.DataFrame(orders)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["order_total"] = pd.to_numeric(df["order_total"], errors="coerce").fillna(0)
    valid = df[~df["order_status"].isin(["Cancelled", "Refunded"])]

    monthly = df.groupby(df["order_date"].dt.to_period("M")).size()
    plt.figure(figsize=(8, 4))
    if not monthly.empty:
        monthly.index = monthly.index.astype(str)
        monthly.plot(kind="bar")
    plt.title("Monthly Order Volume (all statuses)")
    plt.xlabel("Month")
    plt.ylabel("Orders")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "monthly_orders.png"))
    plt.close()

    payment = valid["payment_method"].value_counts()
    plt.figure(figsize=(7, 4))
    if not payment.empty:
        payment.plot(kind="bar")
    plt.title("Payment Method Distribution (excluding cancelled/refunded)")
    plt.xlabel("Payment method")
    plt.ylabel("Orders")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "payment_methods.png"))
    plt.close()

    status = df["order_status"].value_counts()
    plt.figure(figsize=(7, 4))
    if not status.empty:
        status.plot(kind="bar")
    plt.title("Order Status Distribution")
    plt.xlabel("Status")
    plt.ylabel("Orders")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "order_status.png"))
    plt.close()

    product_df = pd.DataFrame(items)
    plt.figure(figsize=(8, 4))
    if not product_df.empty:
        product_df = product_df.sort_values("units_sold", ascending=True)
        plt.barh(product_df["product_name"], product_df["units_sold"])
    plt.title("Product Units Sold (fulfilled/in-progress orders)")
    plt.xlabel("Units")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "top_products.png"))
    plt.close()


@app.template_filter("money")
def money(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


@app.route("/")
def dashboard():
    try:
        create_charts()
        summary = query_all("""
            SELECT
              COUNT(*) AS total_orders,
              SUM(order_status NOT IN ('Cancelled','Refunded')) AS valid_orders,
              SUM(order_status = 'Cancelled') AS cancelled_orders,
              SUM(order_status = 'Refunded') AS refunded_orders
            FROM orders
        """)[0]
        totals = query_all("""
            SELECT o.order_id, o.order_status,
                   COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS order_total
            FROM orders o LEFT JOIN order_items oi ON oi.order_id = o.order_id
            GROUP BY o.order_id, o.order_status
        """)
        total_df = pd.DataFrame(totals)
        if total_df.empty:
            gross = avg = 0.0
        else:
            total_df["order_total"] = pd.to_numeric(total_df["order_total"], errors="coerce").fillna(0)
            eligible = total_df[~total_df["order_status"].isin(["Cancelled", "Refunded"])]
            gross = float(np.sum(eligible["order_total"].to_numpy(dtype=float)))
            avg = float(np.mean(eligible["order_total"].to_numpy(dtype=float))) if len(eligible) else 0.0
        recent = query_all("""
            SELECT o.order_id, o.order_date, o.payment_method, o.order_status,
                   COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS order_total
            FROM orders o LEFT JOIN order_items oi ON oi.order_id = o.order_id
            GROUP BY o.order_id, o.order_date, o.payment_method, o.order_status
            ORDER BY o.order_date DESC, o.order_id DESC LIMIT 8
        """)
        return render_template("dashboard.html", summary=summary, gross=gross, avg=avg, recent=recent)
    except mysql.connector.Error as exc:
        return render_template("setup_error.html", error=str(exc)), 500


@app.route("/products")
def products():
    rows = query_all("SELECT * FROM products ORDER BY product_id DESC")
    return render_template("products.html", products=rows)


@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("product_name", "").strip()
        category = request.form.get("category", "").strip()
        try:
            price = float(request.form.get("unit_price", ""))
            if not name or price < 0:
                raise ValueError()
            execute("INSERT INTO products(product_name, category, unit_price) VALUES (%s,%s,%s)",
                    (name, category, price))
            flash("Product added.", "success")
            return redirect(url_for("products"))
        except (ValueError, mysql.connector.Error) as exc:
            flash(f"Could not add product: {exc or 'enter a valid name and non-negative price'}", "danger")
    return render_template("product_form.html")


@app.route("/orders")
def orders():
    rows = query_all("""
        SELECT o.order_id, o.order_date, o.payment_method, o.order_status,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS order_total
        FROM orders o LEFT JOIN order_items oi ON oi.order_id = o.order_id
        GROUP BY o.order_id, o.order_date, o.payment_method, o.order_status
        ORDER BY o.order_date DESC, o.order_id DESC
    """)
    return render_template("orders.html", orders=rows)


@app.route("/orders/add", methods=["GET", "POST"])
def add_order():
    product_rows = query_all("SELECT product_id, product_name, unit_price FROM products ORDER BY product_name")
    if request.method == "POST":
        try:
            order_date = request.form.get("order_date") or date.today().isoformat()
            payment = request.form.get("payment_method", "").strip()
            status = request.form.get("order_status", "Pending")
            product_id = int(request.form.get("product_id", ""))
            quantity = int(request.form.get("quantity", ""))
            product = query_all("SELECT unit_price FROM products WHERE product_id=%s", (product_id,))
            if not product or quantity < 1 or payment not in ["UPI", "Card", "Cash on Delivery", "Net Banking", "Wallet"]:
                raise ValueError("Choose valid order details.")
            # Snapshot the current product price into order_items to preserve historical order value.
            price = Decimal(str(product[0]["unit_price"]))
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO orders(order_date,payment_method,order_status) VALUES (%s,%s,%s)",
                            (order_date, payment, status))
                order_id = cur.lastrowid
                cur.execute("INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES (%s,%s,%s,%s)",
                            (order_id, product_id, quantity, price))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()
                conn.close()
            flash(f"Order #{order_id} created.", "success")
            return redirect(url_for("orders"))
        except (ValueError, mysql.connector.Error) as exc:
            flash(f"Could not create order: {exc}", "danger")
    return render_template("order_form.html", products=product_rows, today=date.today().isoformat())


@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    order = query_all("SELECT * FROM orders WHERE order_id=%s", (order_id,))
    if not order:
        abort(404)
    items = query_all("""
        SELECT oi.*, p.product_name, p.category, (oi.quantity * oi.unit_price) AS line_total
        FROM order_items oi JOIN products p ON p.product_id=oi.product_id
        WHERE oi.order_id=%s ORDER BY oi.item_id
    """, (order_id,))
    total = sum(float(i["line_total"]) for i in items)
    return render_template("order_detail.html", order=order[0], items=items, total=total)


@app.route("/orders/<int:order_id>/status", methods=["POST"])
def update_status(order_id):
    status = request.form.get("order_status")
    if status not in ["Pending", "Processing", "Shipped", "Delivered", "Cancelled", "Refunded"]:
        flash("Invalid status.", "danger")
    else:
        execute("UPDATE orders SET order_status=%s WHERE order_id=%s", (status, order_id))
        flash("Order status updated.", "success")
    return redirect(url_for("order_detail", order_id=order_id))


@app.route("/reports")
def reports():
    create_charts()
    rows = query_all("""
        SELECT o.order_id, o.order_date, o.payment_method, o.order_status,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS order_total,
               COALESCE(SUM(oi.quantity), 0) AS item_count
        FROM orders o LEFT JOIN order_items oi ON oi.order_id=o.order_id
        GROUP BY o.order_id, o.order_date, o.payment_method, o.order_status
        ORDER BY o.order_date DESC
    """)
    df = pd.DataFrame(rows)
    if df.empty:
        metrics = {"orders": 0, "eligible_orders": 0, "gross_value": 0, "average_value": 0, "units": 0}
    else:
        df["order_total"] = pd.to_numeric(df["order_total"], errors="coerce").fillna(0)
        df["item_count"] = pd.to_numeric(df["item_count"], errors="coerce").fillna(0)
        eligible = df[~df["order_status"].isin(["Cancelled", "Refunded"])]
        values = eligible["order_total"].to_numpy(dtype=float)
        metrics = {
            "orders": int(len(df)),
            "eligible_orders": int(len(eligible)),
            "gross_value": float(np.sum(values)),
            "average_value": float(np.mean(values)) if len(values) else 0,
            "units": int(eligible["item_count"].sum()),
        }
    return render_template("reports.html", metrics=metrics, orders=rows)


@app.route("/health")
def health():
    query_all("SELECT 1 AS ok")
    return {"status": "ok", "database": "connected"}


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "true").lower() == "true")
