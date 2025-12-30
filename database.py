# database.py
# Database operations for Skylume ERP - permanent save/load

import sqlite3
import json
from datetime import datetime

DB_FILE = "data.db"

def init_db():
    """Startup pe tables create karo agar nahi hain"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Chart of Accounts
    c.execute('''CREATE TABLE IF NOT EXISTS chart_of_accounts (
        code TEXT PRIMARY KEY,
        name TEXT,
        parent_code TEXT,
        is_group INTEGER
    )''')
    
    # Vouchers (common table for all types)
    c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,  -- 'bank', 'cash', 'journal', 'sales', 'purchase'
        prefix TEXT,
        date TEXT,
        cheque_date TEXT,
        cheque_no TEXT,
        added_by TEXT,
        added_on TEXT,
        lines TEXT  -- JSON string of lines
    )''')
    
    # Logs (user actions)
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        timestamp TEXT
    )''')
    
    conn.commit()
    conn.close()
    print("Database initialized - all tables ready")


def save_chart_of_accounts(accounts):
    """COA poora overwrite/save karo"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM chart_of_accounts")  # Purana data clear
    for acc in accounts:
        c.execute('''INSERT OR REPLACE INTO chart_of_accounts 
                     (code, name, parent_code, is_group) 
                     VALUES (?, ?, ?, ?)''', 
                  (acc['code'], acc['name'], acc.get('parent_code'), 1 if acc.get('is_group') else 0))
    conn.commit()
    conn.close()
    print(f"COA saved to DB - {len(accounts)} accounts")


def load_chart_of_accounts():
    """COA database se load karo"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT code, name, parent_code, is_group FROM chart_of_accounts")
    rows = c.fetchall()
    conn.close()
    data = [
        {"code": row[0], "name": row[1], "parent_code": row[2], "is_group": bool(row[3])}
        for row in rows
    ]
    print(f"Loaded COA from DB - {len(data)} accounts")
    return data


def save_voucher_to_db(vtype, vouchers):
    """Vouchers save karo (append mode - purane delete nahi honge)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for v in vouchers:
        lines_json = json.dumps(v.get('lines', []))
        date_str = v['date'].isoformat() if 'date' in v and v['date'] else None
        cheque_date_str = v.get('cheque_date').isoformat() if v.get('cheque_date') else None
        added_on_str = v.get('added_on', datetime.now()).isoformat() if v.get('added_on') else datetime.now().isoformat()
        c.execute('''INSERT INTO vouchers 
                     (type, prefix, date, cheque_date, cheque_no, added_by, added_on, lines) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                  (vtype, v.get('prefix', ''), date_str, cheque_date_str, v.get('cheque_no', ''),
                   v.get('added_by', 'admin'), added_on_str, lines_json))
    conn.commit()
    conn.close()
    print(f"Saved {len(vouchers)} {vtype} vouchers to DB")


def load_vouchers(vtype):
    """Vouchers database se load karo (type ke hisab se)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT prefix, date, cheque_date, cheque_no, added_by, added_on, lines FROM vouchers WHERE type = ? ORDER BY added_on DESC", (vtype,))
    rows = c.fetchall()
    conn.close()
    vouchers = []
    for row in rows:
        try:
            date_obj = datetime.fromisoformat(row[1]) if row[1] else None
            cheque_date_obj = datetime.fromisoformat(row[2]) if row[2] else None
            added_on_obj = datetime.fromisoformat(row[5]) if row[5] else None
        except:
            date_obj = cheque_date_obj = added_on_obj = None
        lines = json.loads(row[6]) if row[6] else []
        vouchers.append({
            "prefix": row[0],
            "date": date_obj,
            "cheque_date": cheque_date_obj,
            "cheque_no": row[3],
            "added_by": row[4],
            "added_on": added_on_obj,
            "lines": lines
        })
    print(f"Loaded {len(vouchers)} {vtype} vouchers from DB")
    return vouchers


def save_log(username, action, timestamp):
    """User action log save karo"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO logs (username, action, timestamp) VALUES (?, ?, ?)", 
              (username, action, timestamp))
    conn.commit()
    conn.close()


def load_logs():
    """Poora log load karo (latest first)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, action, timestamp FROM logs ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return [{"username": r[0], "action": r[1], "timestamp": r[2]} for r in rows]