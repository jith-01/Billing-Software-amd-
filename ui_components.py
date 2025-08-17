# ui_components.py

import customtkinter as ctk
from tkinter import messagebox
import win32print
import win32ui
from PIL import Image, ImageWin

class BillingTab(ctk.CTkFrame):
    """UI Frame for the Billing Tab."""
    def __init__(self, master, db_handler, **kwargs):
        super().__init__(master, **kwargs)
        self.db_handler = db_handler
        self.stock_items = self.db_handler.fetch_items()
        
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_columnconfigure(2, weight=2) # Give more weight to receipt frame
        self.grid_rowconfigure(1, weight=1)

        # --- Details Frame ---
        details_frame = ctk.CTkFrame(master=self)
        details_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        
        ctk.CTkLabel(master=details_frame, text="Customer Name:", font=ctk.CTkFont(size=16)).grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.name_entry = ctk.CTkEntry(master=details_frame, placeholder_text="Enter Name")
        self.name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(master=details_frame, text="Ration Card Number:", font=ctk.CTkFont(size=16)).grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.ration_card_entry = ctk.CTkEntry(master=details_frame, placeholder_text="Enter Ration Card Number")
        self.ration_card_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # --- Items Frame ---
        scrollable_frame = ctk.CTkScrollableFrame(master=self, label_text="Items")
        scrollable_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")
        
        self.item_entries = {}
        for index, item in enumerate(self.stock_items):
            item_name = item[1]
            ctk.CTkLabel(master=scrollable_frame, text=item_name, font=ctk.CTkFont(size=16)).grid(row=index, column=0, padx=20, pady=10, sticky="e")
            entry = ctk.CTkEntry(master=scrollable_frame, placeholder_text="Quantity")
            entry.grid(row=index, column=1, padx=20, pady=10, sticky="w")
            self.item_entries[item_name] = entry

        # --- Receipt Frame ---
        receipt_frame = ctk.CTkFrame(master=self)
        receipt_frame.grid(row=0, column=2, rowspan=3, padx=20, pady=20, sticky="nsew")
        receipt_frame.grid_rowconfigure(1, weight=1)
        receipt_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(master=receipt_frame, text="Receipt", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=10)
        self.receipt_textbox = ctk.CTkTextbox(master=receipt_frame)
        self.receipt_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkButton(master=receipt_frame, text="Print Receipt", command=self.print_receipt).grid(row=2, column=0, pady=10)

        # --- Generate Bill Button ---
        ctk.CTkButton(master=self, text="Generate Bill", command=self.generate_bill).grid(row=2, column=0, columnspan=2, pady=20)

    def generate_bill(self):
        customer_name = self.name_entry.get().strip()
        ration_card = self.ration_card_entry.get().strip()
        if not customer_name or not ration_card:
            messagebox.showwarning("Input Error", "Please enter customer name and ration card number.")
            return

        bill_items = {}
        total = 0
        receipt = [
            "----------- RECEIPT -----------",
            f"Customer: {customer_name}",
            f"Ration Card: {ration_card}",
            "-------------------------------",
            f"{'Item':<15}{'Qty':<5}{'Price':<7}{'Total':<7}",
            "-------------------------------"
        ]
        
        item_rates = {item[1]: item[2] for item in self.stock_items}

        for name, entry in self.item_entries.items():
            qty_str = entry.get().strip()
            if qty_str:
                try:
                    qty = int(qty_str)
                    rate = item_rates.get(name, 0)
                    total_price = qty * rate
                    total += total_price
                    bill_items[name] = (qty, rate)
                    receipt.append(f"{name:<15}{qty:<5}{rate:<7.2f}{total_price:<7.2f}")
                except ValueError:
                    messagebox.showwarning("Input Error", f"Invalid quantity for {name}.")
                    return
        
        receipt.extend(["-------------------------------", f"Total Amount: {total:.2f}", "-------------------------------"])

        if self.db_handler.add_bill(bill_items):
            self.receipt_textbox.delete("1.0", "end")
            self.receipt_textbox.insert("1.0", "\n".join(receipt))
        else:
            messagebox.showerror("Database Error", "Failed to generate and save the bill.")

    def print_receipt(self):
        receipt_text = self.receipt_textbox.get("1.0", "end-1c")
        if not receipt_text:
            messagebox.showwarning("Print Error", "No receipt to print.")
            return

        printer_name = win32print.GetDefaultPrinter()
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        hDC.StartDoc("Receipt")
        hDC.StartPage()
        
        y = 100
        for line in receipt_text.split('\n'):
            hDC.TextOut(100, y, line)
            y += 50 # Increment y-coordinate for the next line

        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        messagebox.showinfo("Print Success", "Receipt sent to the printer.")

class StockTab(ctk.CTkFrame):
    """UI Frame for the Stock Management Tab."""
    def __init__(self, master, db_handler, **kwargs):
        super().__init__(master, **kwargs)
        self.db_handler = db_handler

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Stock Table Frame ---
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.stock_table = ctk.CTkTextbox(master=table_frame)
        self.stock_table.grid(row=0, column=0, sticky="nsew")

        # --- Add Item Frame ---
        add_item_frame = ctk.CTkFrame(master=self)
        add_item_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        
        self.sl_no_entry = ctk.CTkEntry(master=add_item_frame, placeholder_text="Sl No")
        self.sl_no_entry.pack(side="left", padx=10, pady=5, expand=True)
        self.item_name_entry = ctk.CTkEntry(master=add_item_frame, placeholder_text="Item Name")
        self.item_name_entry.pack(side="left", padx=10, pady=5, expand=True)
        self.rate_entry = ctk.CTkEntry(master=add_item_frame, placeholder_text="Rate")
        self.rate_entry.pack(side="left", padx=10, pady=5, expand=True)

        ctk.CTkButton(master=self, text="Add Item", command=self.add_item).grid(row=2, column=0, pady=10)
        
        self.refresh_stock_table()

    def add_item(self):
        sl_no = self.sl_no_entry.get().strip()
        name = self.item_name_entry.get().strip()
        rate_str = self.rate_entry.get().strip()

        if not all([sl_no, name, rate_str]):
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        try:
            rate = float(rate_str)
        except ValueError:
            messagebox.showwarning("Input Error", "Rate must be a number.")
            return

        if self.db_handler.add_item(sl_no, name, rate):
            self.refresh_stock_table()
            self.sl_no_entry.delete(0, "end")
            self.item_name_entry.delete(0, "end")
            self.rate_entry.delete(0, "end")
            messagebox.showinfo("Success", "Item added successfully.")
        else:
            messagebox.showerror("Database Error", "Failed to add item.")

    def refresh_stock_table(self):
        items = self.db_handler.fetch_items()
        self.stock_table.delete("1.0", "end")
        header = f"{'Sl No':<10}{'Item Name':<25}{'Rate':<10}\n"
        separator = "-" * 45 + "\n"
        self.stock_table.insert("1.0", header + separator)
        for item in items:
            row = f"{item[0]:<10}{item[1]:<25}{item[2]:<10.2f}\n"
            self.stock_table.insert("end", row)

class SalesTab(ctk.CTkFrame):
    """UI Frame for the Sales Report Tab."""
    def __init__(self, master, db_handler, **kwargs):
        super().__init__(master, **kwargs)
        self.db_handler = db_handler

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Controls Frame ---
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.sales_date_entry = ctk.CTkEntry(master=controls_frame, placeholder_text="Enter Date (YYYY-MM-DD)")
        self.sales_date_entry.pack(side="left", padx=10, pady=10, expand=True)
        ctk.CTkButton(master=controls_frame, text="Fetch Sales", command=self.fetch_sales).pack(side="left", padx=10, pady=10)

        # --- Sales Table Frame ---
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.sales_table = ctk.CTkTextbox(master=table_frame)
        self.sales_table.grid(row=0, column=0, sticky="nsew")

    def fetch_sales(self):
        date = self.sales_date_entry.get().strip()
        if not date:
            messagebox.showwarning("Input Error", "Please enter a date.")
            return

        sales_data, total_amount = self.db_handler.fetch_sales_data(date)
        
        self.sales_table.delete("1.0", "end")
        header = f"{'Item':<20}{'Qty Sold':<15}{'Total Sales':<15}\n"
        separator = "-" * 50 + "\n"
        self.sales_table.insert("1.0", header + separator)

        for item in sales_data:
            row = f"{item[0]:<20}{item[1]:<15}{item[2]:<15.2f}\n"
            self.sales_table.insert("end", row)
            
        self.sales_table.insert("end", separator)
        self.sales_table.insert("end", f"Total Sales Amount for {date}: {total_amount:.2f}")

class MainTabView(ctk.CTkTabview):
    """The main TabView that holds all the tabs."""
    def __init__(self, master, db_handler, **kwargs):
        super().__init__(master, **kwargs)
        
        # Add tabs
        self.add("BILLING")
        self.add("STOCK")
        self.add("SALES")
        
        # Create tab content
        self.billing_tab = BillingTab(self.tab("BILLING"), db_handler)
        self.billing_tab.pack(fill="both", expand=True)
        
        self.stock_tab = StockTab(self.tab("STOCK"), db_handler)
        self.stock_tab.pack(fill="both", expand=True)
        
        self.sales_tab = SalesTab(self.tab("SALES"), db_handler)
        self.sales_tab.pack(fill="both", expand=True)