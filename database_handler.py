# database_handler.py

import mysql.connector
from tkinter import messagebox

class DatabaseHandler:
    """Handles all database operations for the billing system."""
    def __init__(self, db_config):
        self.db_config = db_config

    def _connect(self):
        """Establishes a connection to the database."""
        try:
            return mysql.connector.connect(**self.db_config)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error connecting to the database: {err}")
            return None

    def _execute_query(self, query, params=None, fetch=None, commit=False):
        """A generic method to execute database queries."""
        conn = self._connect()
        if not conn:
            return None if fetch else False
        
        result = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if commit:
                conn.commit()
                if cursor.lastrowid:
                    result = cursor.lastrowid
                else:
                    result = True
            if fetch == 'all':
                result = cursor.fetchall()
            elif fetch == 'one':
                result = cursor.fetchone()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Query failed: {err}")
            result = None if fetch else False
        finally:
            conn.close()
        return result

    def fetch_items(self):
        """Fetches all items from the stock table."""
        return self._execute_query("SELECT Slno, ItemName, Rate FROM stock", fetch='all') or []

    def add_item(self, sl_no, item_name, rate):
        """Adds a new item to the stock table."""
        sql = "INSERT INTO stock (Slno, ItemName, Rate) VALUES (%s, %s, %s)"
        return self._execute_query(sql, (sl_no, item_name, rate), commit=True)

    def add_bill(self, items):
        """Adds a new bill and its items to the database."""
        conn = self._connect()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO bills (total_amount) VALUES (0)")
            bill_id = cursor.lastrowid
            
            total_amount = 0
            for item_name, (quantity, unit_price) in items.items():
                total_price = quantity * unit_price
                total_amount += total_price
                cursor.execute(
                    "INSERT INTO bill_items (bill_id, item_name, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                    (bill_id, item_name, quantity, unit_price)
                )
            
            cursor.execute("UPDATE bills SET total_amount = %s WHERE bill_id = %s", (total_amount, bill_id))
            conn.commit()
            return bill_id
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error adding bill: {err}")
            return None
        finally:
            conn.close()

    def fetch_sales_data(self, date):
        """Fetches sales data for a specific date."""
        sales_query = """
            SELECT bi.item_name, SUM(bi.quantity), SUM(bi.quantity * bi.unit_price)
            FROM bill_items bi JOIN bills b ON bi.bill_id = b.bill_id
            WHERE DATE(b.bill_date) = %s
            GROUP BY bi.item_name ORDER BY bi.item_name
        """
        sales_data = self._execute_query(sales_query, (date,), fetch='all')

        total_query = "SELECT SUM(total_amount) FROM bills WHERE DATE(bill_date) = %s"
        total_result = self._execute_query(total_query, (date,), fetch='one')
        total_amount = total_result[0] if total_result and total_result[0] is not None else 0
        
        return sales_data or [], total_amount