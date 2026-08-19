import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# ============================================================
# NEXUS LIBRARY - Frontend + SQLite Backend
# Single-file, offline desktop library management system.
# No external packages required.
# ============================================================

DB_FILE = "library.db"

# ---------------------------- Theme ----------------------------
BG = "#08111f"
SIDEBAR = "#0e1a2d"
CARD = "#13233a"
CARD2 = "#1b304d"
TEXT = "#eef5ff"
MUTED = "#9badc7"
ACCENT = "#5eead4"
BLUE = "#60a5fa"
PURPLE = "#a78bfa"
ORANGE = "#fbbf24"
RED = "#fb7185"
GREEN = "#4ade80"

# ---------------------------- Database -------------------------
class LibraryDB:
    def __init__(self, path=DB_FILE):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()
        self.seed_books()

    def create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                action TEXT NOT NULL CHECK(action IN ('BORROW', 'RETURN')),
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(book_id) REFERENCES books(id)
            );
        """)
        self.conn.commit()

    def seed_books(self):
        if self.conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] != 0:
            return

        # Based on the user's existing library data. Duplicate Harry Potter
        # entries are intentionally merged into one title with quantity 12.
        seed = [
            ("king of the jungle", "king", 10),
            ("lionking", "bradley", 4),
            ("Harry Potter", "JK Rowling", 12),
            ("Wings of Fire", "A. P. J. Abdul Kalam", 4),
            ("Atomic Habits", "James Clear", 5),
            ("Rich Dad Poor Dad", "Robert T. Kiyosaki", 5),
            ("Sapiens", "Yuval Noah Harari", 4),
            ("The Psychology of Money", "Morgan Housel", 3),
            ("Deep Work", "Cal Newport", 5),
            ("Think and Grow Rich", "Napoleon Hill", 11),
            ("The Book Thief", "Markus Zusak", 10),
            ("Educated", "Tara Westover", 5),
        ]
        now = datetime.now().isoformat(timespec="seconds")
        self.conn.executemany(
            "INSERT INTO books(title,author,quantity,created_at) VALUES(?,?,?,?)",
            [(t, a, q, now) for t, a, q in seed]
        )
        self.conn.commit()

    # -------- Dashboard --------
    def stats(self):
        row = self.conn.execute("""
            SELECT
                COALESCE(SUM(quantity),0) AS copies,
                COUNT(*) AS titles,
                (SELECT COUNT(*) FROM users) AS users,
                SUM(CASE WHEN quantity BETWEEN 1 AND 3 THEN 1 ELSE 0 END) AS low_stock,
                SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END) AS out_stock
            FROM books
        """).fetchone()
        return dict(row)

    # -------- Books --------
    def books(self, query=""):
        q = f"%{query.strip()}%"
        return self.conn.execute("""
            SELECT id, title, author, quantity
            FROM books
            WHERE title LIKE ? OR author LIKE ?
            ORDER BY LOWER(title), LOWER(author)
        """, (q, q)).fetchall()

    def add_book(self, title, author, quantity):
        title, author = title.strip(), author.strip()
        if not title or not author:
            raise ValueError("Title and author are required.")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")

        # Merge same title + author.
        existing = self.conn.execute("""
            SELECT id FROM books
            WHERE LOWER(title)=LOWER(?) AND LOWER(author)=LOWER(?)
        """, (title, author)).fetchone()

        if existing:
            self.conn.execute(
                "UPDATE books SET quantity=quantity+? WHERE id=?",
                (quantity, existing["id"])
            )
        else:
            self.conn.execute(
                "INSERT INTO books(title,author,quantity,created_at) VALUES(?,?,?,?)",
                (title, author, quantity, datetime.now().isoformat(timespec="seconds"))
            )
        self.conn.commit()

    def update_book(self, book_id, title, author, quantity):
        if not title.strip() or not author.strip() or quantity < 0:
            raise ValueError("Enter valid title, author and quantity.")
        self.conn.execute("""
            UPDATE books SET title=?, author=?, quantity=? WHERE id=?
        """, (title.strip(), author.strip(), quantity, book_id))
        self.conn.commit()

    def delete_book(self, book_id):
        used = self.conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE book_id=?", (book_id,)
        ).fetchone()[0]
        if used:
            raise ValueError("This book has transaction history and cannot be deleted.")
        self.conn.execute("DELETE FROM books WHERE id=?", (book_id,))
        self.conn.commit()

    def get_book(self, book_id):
        return self.conn.execute(
            "SELECT * FROM books WHERE id=?", (book_id,)
        ).fetchone()

    # -------- Users --------
    def users(self, query=""):
        q = f"%{query.strip()}%"
        return self.conn.execute("""
            SELECT id, name, email
            FROM users
            WHERE name LIKE ? OR email LIKE ?
            ORDER BY LOWER(name)
        """, (q, q)).fetchall()

    def add_user(self, name, email):
        name, email = name.strip(), email.strip().lower()
        if not name or "@" not in email:
            raise ValueError("Enter a valid name and email.")
        try:
            self.conn.execute(
                "INSERT INTO users(name,email,created_at) VALUES(?,?,?)",
                (name, email, datetime.now().isoformat(timespec="seconds"))
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("A user with this email already exists.")

    def delete_user(self, user_id):
        used = self.conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE user_id=?", (user_id,)
        ).fetchone()[0]
        if used:
            raise ValueError("This user has transaction history and cannot be deleted.")
        self.conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        self.conn.commit()

    # -------- Borrow / Return --------
    def transaction(self, user_id, book_id, action):
        if action not in ("BORROW", "RETURN"):
            raise ValueError("Invalid transaction.")

        self.conn.execute("BEGIN")
        try:
            book = self.conn.execute(
                "SELECT quantity,title FROM books WHERE id=?", (book_id,)
            ).fetchone()
            user = self.conn.execute(
                "SELECT name FROM users WHERE id=?", (user_id,)
            ).fetchone()

            if not book or not user:
                raise ValueError("Selected user or book no longer exists.")

            qty = book["quantity"]

            if action == "BORROW":
                if qty <= 0:
                    raise ValueError("This book is currently out of stock.")
                new_qty = qty - 1
            else:
                new_qty = qty + 1

            self.conn.execute(
                "UPDATE books SET quantity=? WHERE id=?", (new_qty, book_id)
            )
            self.conn.execute("""
                INSERT INTO transactions(user_id,book_id,action,created_at)
                VALUES(?,?,?,?)
            """, (user_id, book_id, action, datetime.now().isoformat(timespec="seconds")))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def recent_transactions(self, limit=8):
        return self.conn.execute("""
            SELECT t.action, t.created_at, u.name, b.title
            FROM transactions t
            JOIN users u ON u.id=t.user_id
            JOIN books b ON b.id=t.book_id
            ORDER BY t.id DESC LIMIT ?
        """, (limit,)).fetchall()

    def close(self):
        self.conn.close()


db = LibraryDB()

# ---------------------------- UI -------------------------------
root = tk.Tk()
root.title("NEXUS LIBRARY • Smart Library Management")
root.geometry("1280x780")
root.minsize(1080, 680)
root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background=CARD, foreground=TEXT,
                fieldbackground=CARD, rowheight=38, borderwidth=0,
                font=("Segoe UI", 10))
style.configure("Treeview.Heading", background=CARD2, foreground=ACCENT,
                font=("Segoe UI Semibold", 10))
style.map("Treeview", background=[("selected", "#2b4c73")])

content = tk.Frame(root, bg=BG)
content.pack(side="right", fill="both", expand=True)

# ---------------------------- Helpers ---------------------------
def clear_content():
    for w in content.winfo_children():
        w.destroy()

def page_title(title, subtitle):
    tk.Label(content, text=title, bg=BG, fg=TEXT,
             font=("Segoe UI Semibold", 25)).pack(anchor="w", padx=28, pady=(25, 3))
    tk.Label(content, text=subtitle, bg=BG, fg=MUTED,
             font=("Segoe UI", 10)).pack(anchor="w", padx=30, pady=(0, 18))

def button(parent, text, command, color=BLUE, width=15):
    return tk.Button(parent, text=text, command=command, bg=color, fg="#07111f",
                     activebackground=color, relief="flat", bd=0,
                     font=("Segoe UI Semibold", 10), padx=12, pady=9,
                     cursor="hand2", width=width)

def safe(action):
    try:
        action()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    except ValueError as e:
        messagebox.showwarning("Check Input", str(e))

def refresh_all():
    dashboard()

# ---------------------------- Dashboard ------------------------
def dashboard():
    clear_content()
    page_title("Library Command Center",
               "Everything important at a glance — powered by a local SQLite backend.")

    stats = db.stats()

    cards = tk.Frame(content, bg=BG)
    cards.pack(fill="x", padx=20)

    def card(title, value, accent, icon):
        f = tk.Frame(cards, bg=CARD, padx=18, pady=14)
        f.pack(side="left", fill="both", expand=True, padx=7)
        tk.Label(f, text=icon, bg=CARD, fg=accent,
                 font=("Segoe UI Emoji", 20)).pack(anchor="w")
        tk.Label(f, text=str(value), bg=CARD, fg=TEXT,
                 font=("Segoe UI Semibold", 25)).pack(anchor="w")
        tk.Label(f, text=title, bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")

    card("Total Copies", stats["copies"], ACCENT, "▣")
    card("Unique Titles", stats["titles"], BLUE, "◈")
    card("Registered Users", stats["users"], PURPLE, "●")
    card("Low Stock (≤ 3)", stats["low_stock"], ORANGE, "!")

    body = tk.Frame(content, bg=BG)
    body.pack(fill="both", expand=True, padx=27, pady=25)

    left = tk.Frame(body, bg=CARD)
    left.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(left, text="✨ Quick Actions", bg=CARD, fg=ACCENT,
             font=("Segoe UI Semibold", 18)).pack(anchor="w", padx=24, pady=(23, 10))

    actions = tk.Frame(left, bg=CARD)
    actions.pack(anchor="w", padx=20)
    button(actions, "＋ Add Book", add_book_page, GREEN, 15).pack(side="left", padx=5, pady=5)
    button(actions, "● Register User", register_page, PURPLE, 15).pack(side="left", padx=5, pady=5)
    button(actions, "↪ Borrow", borrow_page, BLUE, 15).pack(side="left", padx=5, pady=5)
    button(actions, "↩ Return", return_page, ACCENT, 15).pack(side="left", padx=5, pady=5)

    tk.Label(left, text="System Status", bg=CARD, fg=TEXT,
             font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=24, pady=(25, 5))
    tk.Label(left, text="●  DATABASE ONLINE     ●  LOCAL & PRIVATE     ●  AUTO-SAVE",
             bg=CARD, fg=GREEN, font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=24)

    right = tk.Frame(body, bg=CARD)
    right.pack(side="right", fill="both", expand=True, padx=(10, 0))

    tk.Label(right, text="Recent Activity", bg=CARD, fg=TEXT,
             font=("Segoe UI Semibold", 16)).pack(anchor="w", padx=20, pady=(20, 10))

    recent = db.recent_transactions()
    if not recent:
        tk.Label(right, text="No transactions yet.\nBorrow or return a book to see activity here.",
                 bg=CARD, fg=MUTED, justify="left",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=10)
    else:
        for r in recent:
            row = tk.Frame(right, bg=CARD2, padx=10, pady=8)
            row.pack(fill="x", padx=16, pady=3)
            color = BLUE if r["action"] == "BORROW" else GREEN
            tk.Label(row, text=r["action"], bg=CARD2, fg=color,
                     font=("Segoe UI Semibold", 8), width=8).pack(side="left")
            tk.Label(row, text=f'{r["name"]} • {r["title"]}',
                     bg=CARD2, fg=TEXT, anchor="w",
                     font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True)

# ---------------------------- Books page -----------------------
def books_page():
    clear_content()
    page_title("Book Catalog", "Live search • sorting • edit • delete • automatic stock tracking.")

    toolbar = tk.Frame(content, bg=BG)
    toolbar.pack(fill="x", padx=28, pady=(0, 12))

    search = tk.StringVar()
    entry = tk.Entry(toolbar, textvariable=search, bg=CARD, fg=TEXT,
                     insertbackground=TEXT, relief="flat",
                     font=("Segoe UI", 11), width=40)
    entry.pack(side="left", ipady=9)
    tk.Label(toolbar, text="  🔎 Search title or author", bg=BG, fg=MUTED).pack(side="left")

    button(toolbar, "＋ Add Book", add_book_page, GREEN, 14).pack(side="right")

    frame = tk.Frame(content, bg=CARD)
    frame.pack(fill="both", expand=True, padx=28)

    scroll = ttk.Scrollbar(frame, orient="vertical")
    tree = ttk.Treeview(frame, columns=("ID", "Title", "Author", "Qty"),
                        show="headings", yscrollcommand=scroll.set)
    scroll.config(command=tree.yview)
    scroll.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    for col, width in [("ID", 60), ("Title", 350), ("Author", 300), ("Qty", 100)]:
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center" if col in ("ID","Qty") else "w")

    def load():
        for i in tree.get_children():
            tree.delete(i)
        for b in db.books(search.get()):
            tree.insert("", "end", values=(b["id"], b["title"], b["author"], b["quantity"]))

    def selected_id():
        item = tree.focus()
        if not item:
            messagebox.showinfo("Select Book", "Select a book first.")
            return None
        return int(tree.item(item)["values"][0])

    def edit():
        bid = selected_id()
        if bid is None: return
        b = db.get_book(bid)
        book_form("Edit Book", b, load)

    def delete():
        bid = selected_id()
        if bid is None: return
        if not messagebox.askyesno("Confirm Delete", "Delete this book?"):
            return
        safe(lambda: db.delete_book(bid))
        load()
        dashboard()

    actions = tk.Frame(content, bg=BG)
    actions.pack(fill="x", padx=28, pady=12)
    button(actions, "✎ Edit Selected", edit, BLUE, 16).pack(side="left", padx=(0,7))
    button(actions, "✕ Delete Selected", delete, RED, 16).pack(side="left")

    search.trace_add("write", lambda *_: load())
    load()

def book_form(title, book=None, after=None):
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry("480x390")
    win.configure(bg=BG)
    win.transient(root)
    win.grab_set()

    tk.Label(win, text=title, bg=BG, fg=TEXT,
             font=("Segoe UI Semibold", 20)).pack(anchor="w", padx=30, pady=(25, 15))

    entries = {}
    initial = [
        ("Title", book["title"] if book else ""),
        ("Author", book["author"] if book else ""),
        ("Quantity", str(book["quantity"] if book else 1))
    ]
    form = tk.Frame(win, bg=CARD, padx=25, pady=20)
    form.pack(fill="x", padx=25)

    for label, value in initial:
        tk.Label(form, text=label, bg=CARD, fg=MUTED).pack(anchor="w", pady=(5,3))
        e = tk.Entry(form, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat")
        e.pack(fill="x", ipady=8)
        e.insert(0, value)
        entries[label] = e

    def save():
        try:
            title_v = entries["Title"].get().strip()
            author_v = entries["Author"].get().strip()
            qty = int(entries["Quantity"].get())
            if book:
                db.update_book(book["id"], title_v, author_v, qty)
            else:
                db.add_book(title_v, author_v, qty)
            win.destroy()
            if after: after()
            dashboard()
        except (ValueError, sqlite3.Error) as e:
            messagebox.showerror("Could not save", str(e), parent=win)

    button(form, "Save Changes" if book else "＋ Save Book",
           save, ACCENT, 20).pack(anchor="w", pady=18)

def add_book_page():
    book_form("Add New Book")

# ---------------------------- Users page -----------------------
def register_page():
    user_form("Register User")

def user_form(title, user=None, after=None):
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry("480x300")
    win.configure(bg=BG)
    win.transient(root)
    win.grab_set()

    tk.Label(win, text=title, bg=BG, fg=TEXT,
             font=("Segoe UI Semibold", 20)).pack(anchor="w", padx=30, pady=(25,15))

    form = tk.Frame(win, bg=CARD, padx=25, pady=20)
    form.pack(fill="x", padx=25)
    fields = {}
    for label, value in [("Name", user["name"] if user else ""),
                         ("Email", user["email"] if user else "")]:
        tk.Label(form, text=label, bg=CARD, fg=MUTED).pack(anchor="w", pady=(3,3))
        e = tk.Entry(form, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat")
        e.pack(fill="x", ipady=8)
        e.insert(0, value)
        fields[label] = e

    def save():
        try:
            db.add_user(fields["Name"].get(), fields["Email"].get())
            win.destroy()
            if after: after()
            dashboard()
        except (ValueError, sqlite3.Error) as e:
            messagebox.showerror("Could not register", str(e), parent=win)

    button(form, "＋ Register User", save, PURPLE, 20).pack(anchor="w", pady=18)

def users_page():
    clear_content()
    page_title("Library Members", "Search, register and manage members.")

    toolbar = tk.Frame(content, bg=BG)
    toolbar.pack(fill="x", padx=28, pady=(0,12))
    search = tk.StringVar()
    e = tk.Entry(toolbar, textvariable=search, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", width=40)
    e.pack(side="left", ipady=9)
    button(toolbar, "＋ Register User", register_page, PURPLE, 16).pack(side="right")

    frame = tk.Frame(content, bg=CARD)
    frame.pack(fill="both", expand=True, padx=28)
    tree = ttk.Treeview(frame, columns=("ID","Name","Email"), show="headings")
    tree.heading("ID", text="ID"); tree.heading("Name", text="Name"); tree.heading("Email", text="Email")
    tree.column("ID", width=70, anchor="center"); tree.column("Name", width=300); tree.column("Email", width=400)
    tree.pack(fill="both", expand=True)

    def load():
        for i in tree.get_children(): tree.delete(i)
        for u in db.users(search.get()):
            tree.insert("", "end", values=(u["id"],u["name"],u["email"]))
    def delete():
        item = tree.focus()
        if not item: return messagebox.showinfo("Select User","Select a user first.")
        uid = int(tree.item(item)["values"][0])
        if messagebox.askyesno("Confirm Delete","Delete this user?"):
            safe(lambda: db.delete_user(uid))
            load(); dashboard()

    search.trace_add("write", lambda *_: load())
    load()
    button(content, "✕ Delete Selected", delete, RED, 18).pack(anchor="w", padx=28, pady=12)

# ---------------------------- Transactions ---------------------
def transaction_page(action):
    clear_content()
    label = "Borrow Book" if action == "BORROW" else "Return Book"
    page_title(label, "Choose a member and a book. Stock is updated automatically.")

    users = db.users()
    books = db.books()

    if not users:
        tk.Label(content, text="No registered users yet. Register a user first.",
                 bg=BG, fg=ORANGE, font=("Segoe UI", 12)).pack(anchor="w", padx=100, pady=30)
        button(content, "＋ Register User", register_page, PURPLE, 18).pack(anchor="w", padx=100)
        return

    if not books:
        tk.Label(content, text="No books available.", bg=BG, fg=ORANGE,
                 font=("Segoe UI", 12)).pack(anchor="w", padx=100, pady=30)
        return

    form = tk.Frame(content, bg=CARD, padx=30, pady=28)
    form.pack(fill="x", padx=100)

    user_var = tk.StringVar()
    book_var = tk.StringVar()

    user_values = [f'{u["id"]} • {u["name"]} • {u["email"]}' for u in users]
    book_values = [f'{b["id"]} • {b["title"]} • {b["author"]} • {b["quantity"]} available'
                   for b in books]

    tk.Label(form, text="Member", bg=CARD, fg=MUTED).pack(anchor="w", pady=(0,5))
    ub = ttk.Combobox(form, textvariable=user_var, values=user_values, state="readonly")
    ub.pack(fill="x", ipady=7, pady=(0,15))

    tk.Label(form, text="Book", bg=CARD, fg=MUTED).pack(anchor="w", pady=(0,5))
    bb = ttk.Combobox(form, textvariable=book_var, values=book_values, state="readonly")
    bb.pack(fill="x", ipady=7)

    def submit():
        if not user_var.get() or not book_var.get():
            messagebox.showwarning("Missing Selection","Select both a member and a book.")
            return
        uid = int(user_var.get().split(" • ")[0])
        bid = int(book_var.get().split(" • ")[0])
        safe(lambda: db.transaction(uid, bid, action))
        messagebox.showinfo("Success", f"{label} completed successfully.")
        dashboard()

    button(form, "Confirm Transaction", submit, ACCENT, 22).pack(anchor="w", pady=22)

def borrow_page():
    transaction_page("BORROW")

def return_page():
    transaction_page("RETURN")

# ---------------------------- Sidebar --------------------------
sidebar = tk.Frame(root, bg=SIDEBAR, width=235)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(sidebar, text="NEXUS", bg=SIDEBAR, fg=ACCENT,
         font=("Segoe UI Black", 23)).pack(anchor="w", padx=22, pady=(25,0))
tk.Label(sidebar, text="LIBRARY SYSTEM", bg=SIDEBAR, fg=MUTED,
         font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=23, pady=(0,25))

def nav(text, command, color=TEXT):
    b = tk.Button(sidebar, text=text, command=command,
                  bg=SIDEBAR, fg=color, activebackground=CARD2,
                  activeforeground=ACCENT, relief="flat", bd=0,
                  anchor="w", padx=22, pady=13,
                  font=("Segoe UI Semibold", 10), cursor="hand2")
    b.pack(fill="x", padx=8, pady=2)
    return b

nav("⌂   Dashboard", dashboard, ACCENT)
nav("▤   Book Catalog", books_page)
nav("●   Users", users_page)
nav("＋   Add Book", add_book_page)
nav("↪   Borrow Book", borrow_page)
nav("↩   Return Book", return_page)

tk.Frame(sidebar, bg=SIDEBAR).pack(fill="both", expand=True)
tk.Label(sidebar, text="SMART LIBRARY\nSQLite • Offline • Auto-save",
         bg=SIDEBAR, fg=MUTED, justify="left",
         font=("Segoe UI", 8)).pack(anchor="w", padx=23, pady=20)

# ---------------------------- Main header ----------------------
header = tk.Frame(content, bg=BG, height=65)
# header must be above page content; move current content into a wrapper.
# Rebuild layout: sidebar + right-side wrapper.
header.destroy()

# The current content frame is the right side. Create a top status strip
# using a child frame, while pages continue below it.
# Dashboard/pages occupy the same parent; header is recreated as a fixed child.
page_container = content
content = tk.Frame(root, bg=BG)  # unused compatibility alias
# Repack the actual page frame is already attached; easiest is to use a
# status overlay-style top strip inside the existing root right area.

# Add a thin status strip to the top of the right-side area.
status = tk.Frame(root, bg=BG, height=48)
status.place(x=235, y=0, relwidth=1, anchor="nw")
status.pack_propagate(False)

tk.Label(status, text="LIBRARY MANAGEMENT", bg=BG, fg=TEXT,
         font=("Segoe UI Semibold", 10)).pack(side="left", padx=28, pady=14)
tk.Label(status, text="● DATABASE ONLINE  •  AUTO-SAVE",
         bg=BG, fg=GREEN, font=("Segoe UI Semibold", 9)).pack(side="right", padx=28)

# Keep content below status strip.
# content was originally packed from y=0, so use padding by moving its window.
# Instead, configure the root's right region with a frame and reparenting is
# not possible. Add a small top padding by placing content and status carefully.
# The original content is already packed right; repack it with top padding.
content.pack_forget()
content.pack(side="right", fill="both", expand=True, padx=(0,0), pady=(48,0))

def on_close():
    db.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
dashboard()
root.mainloop()
