# main.py

import customtkinter as ctk
from config import DB_CONFIG
from database_handler import DatabaseHandler
from ui_components import MainTabView

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Billing System")
        self.geometry("1000x650")

        # Initialize database handler
        db_handler = DatabaseHandler(DB_CONFIG)

        # Create and pack the main tab view
        self.tab_view = MainTabView(master=self, db_handler=db_handler)
        self.tab_view.pack(padx=20, pady=20, fill="both", expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()