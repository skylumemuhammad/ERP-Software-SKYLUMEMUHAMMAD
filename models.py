# models.py
# Global data aur helper functions for Skylume ERP

from datetime import datetime

# Default users (startup pe yeh load hoga agar database mein nahi mile)
users = [
    {
        "name": "Administrator",
        "username": "admin",
        "password": "admin",
        "email": "admin@skylume.com",
        "designation": "System Administrator",
        "role": "Admin"
    }
]

# Poori Hierarchy (aap ke Excel se direct – parent-child sahi set)
chart_of_accounts = [
    {"code": "1", "name": "Assets", "parent_code": None, "is_group": True},
    {"code": "1.1", "name": "Current Assets", "parent_code": "1", "is_group": True},
    {"code": "1.1.1000", "name": "Cash in Hand", "parent_code": "1.1", "is_group": True},
    {"code": "1.1.10001", "name": "Cash in Hand UBL Shaheed e Millat, Karachi", "parent_code": "1.1.1000", "is_group": False},
    {"code": "1.1.1010", "name": "Petty Cash", "parent_code": "1.1.1000", "is_group": False},
    {"code": "1.1.1020", "name": "Bank", "parent_code": "1.1", "is_group": True},
    {"code": "1.1.10201", "name": "UBL A/C Shaheed E Millat Road", "parent_code": "1.1.1020", "is_group": False},
    {"code": "1.1.1030", "name": "Accounts Receivable", "parent_code": "1.1", "is_group": True},
    {"code": "1.1.10301", "name": "Accounts Receivable (Ahliya Muhammad Ali)", "parent_code": "1.1.1030", "is_group": False},
    {"code": "1.1.10302", "name": "Accounts Receivable (Muhammad Ali)", "parent_code": "1.1.1030", "is_group": False},
    {"code": "1.1.10303", "name": "Accounts Receivable (Arif Shaikh)", "parent_code": "1.1.1030", "is_group": False},
    {"code": "1.1.1040", "name": "Advance to Employees", "parent_code": "1.1", "is_group": False},
    {"code": "1.1.1050", "name": "Prepaid Account", "parent_code": "1.1", "is_group": True},
    {"code": "1.1.10501", "name": "Muhammad Ali (CEO) - Imprest", "parent_code": "1.1.1050", "is_group": False},
    {"code": "1.1.10502", "name": "Nida Ali (Co Manager) - Imprest", "parent_code": "1.1.1050", "is_group": False},
    {"code": "1.1.10503", "name": "Arif Shaikh (Admin Manager) - Imprest", "parent_code": "1.1.1050", "is_group": False},
    {"code": "1.1.1060", "name": "Short-term Investments", "parent_code": "1.1", "is_group": False},
    {"code": "1.2", "name": "Fixed Assets", "parent_code": "1", "is_group": True},
    {"code": "1.2.1500", "name": "Office Furniture & Fixtures", "parent_code": "1.2", "is_group": False},
    {"code": "1.2.1510", "name": "Computers & Equipment", "parent_code": "1.2", "is_group": False},
    {"code": "1.2.1520", "name": "Vehicles", "parent_code": "1.2", "is_group": False},
    {"code": "1.2.1530", "name": "Office Renovation / Leasehold Improvements", "parent_code": "1.2", "is_group": False},
    {"code": "1.2.1540", "name": "Accumulated Depreciation", "parent_code": "1.2", "is_group": False},
    {"code": "1.3", "name": "Intangible Assets", "parent_code": "1", "is_group": True},
    {"code": "1.3.1600", "name": "Software & Licenses", "parent_code": "1.3", "is_group": False},
    {"code": "1.3.1610", "name": "Trademarks / Registration Cost", "parent_code": "1.3", "is_group": False},
    {"code": "2", "name": "Liabilities", "parent_code": None, "is_group": True},
    {"code": "2.1", "name": "Current Liabilities", "parent_code": "2", "is_group": True},
    {"code": "2.1.2000", "name": "Accounts Payable (Vendors)", "parent_code": "2.1", "is_group": False},
    {"code": "2.1.2010", "name": "Accrued Expenses", "parent_code": "2.1", "is_group": False},
    {"code": "2.1.2020", "name": "Withholding Tax Payable", "parent_code": "2.1", "is_group": False},
    {"code": "2.1.2030", "name": "Sales Tax Payable", "parent_code": "2.1", "is_group": False},
    {"code": "2.1.2040", "name": "Short-term Loan / Overdraft", "parent_code": "2.1", "is_group": False},
    {"code": "2.2", "name": "Long-term Liabilities", "parent_code": "2", "is_group": True},
    {"code": "2.2.2500", "name": "Director's Loan", "parent_code": "2.2", "is_group": False},
    {"code": "2.2.2510", "name": "Bank Loan (Term)", "parent_code": "2.2", "is_group": False},
    {"code": "3", "name": "Equity", "parent_code": None, "is_group": True},
    {"code": "3.3010", "name": "Share Capital – Muhammad Ali Gohar", "parent_code": "3", "is_group": False},
    {"code": "3.3020", "name": "Share Capital – Nida Ali", "parent_code": "3", "is_group": False},
    {"code": "3.3030", "name": "Share Capital – Arif Shaikh", "parent_code": "3", "is_group": False},
    {"code": "3.3100", "name": "Retained Earnings / Profit & Loss", "parent_code": "3", "is_group": False},
    {"code": "4", "name": "Income / Revenue", "parent_code": None, "is_group": True},
    {"code": "4.1", "name": "Consultancy & Design Revenue", "parent_code": "4", "is_group": True},
    {"code": "4.1.4000", "name": "Architectural Design Income", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4010", "name": "Residential Project Income", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4020", "name": "Commercial Project Income", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4030", "name": "Interior Design Services Income", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4040", "name": "Supervision & Site Visit Charges", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4050", "name": "Consulting Fees", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4060", "name": "3D Rendering & Visualization Income", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4070", "name": "Landscape Design Income", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4080", "name": "Plan Approval Assistance Income", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4090", "name": "Structural & Planning Consultancy Fees", "parent_code": "4.1", "is_group": False},
    {"code": "4.1.4011", "name": "Project Supervision / Management Income", "parent_code": "4.1", "is_group": False},
    {"code": "4.2", "name": "Software & IT Revenue", "parent_code": "4", "is_group": True},
    {"code": "4.2.4100", "name": "Software Development Services", "parent_code": "4.2", "is_group": False},
    {"code": "4.2.4110", "name": "Accounting System Customization", "parent_code": "4.2", "is_group": False},
    {"code": "4.2.4120", "name": "Website / App Design Income", "parent_code": "4.2", "is_group": False},
    {"code": "4.2.4130", "name": "Maintenance / Subscription Revenue", "parent_code": "4.2", "is_group": False},
    {"code": "4.3", "name": "Other Income", "parent_code": "4", "is_group": True},
    {"code": "4.3.4200", "name": "Commission Income", "parent_code": "4.3", "is_group": False},
    {"code": "4.3.4210", "name": "Training & Workshop Income Fees", "parent_code": "4.3", "is_group": False},
    {"code": "4.3.4220", "name": "Miscellaneous Income", "parent_code": "4.3", "is_group": False},
    {"code": "5", "name": "Expenses", "parent_code": None, "is_group": True},
    {"code": "5.1", "name": "Direct / Project Expenses", "parent_code": "5", "is_group": True},
    {"code": "5.1.5000", "name": "Site Visits & Project Travel", "parent_code": "5.1", "is_group": False},
    {"code": "5.1.50001", "name": "Site Expenses", "parent_code": "5.1.5000", "is_group": False},
    {"code": "5.1.50002", "name": "Project Expenses", "parent_code": "5.1.5000", "is_group": False},
    {"code": "5.1.5010", "name": "Subcontractor / Draughtsman Charges", "parent_code": "5.1", "is_group": False},
    {"code": "5.1.5020", "name": "Design Software Subscription", "parent_code": "5.1", "is_group": False},
    {"code": "5.1.5030", "name": "Printing & Plotting", "parent_code": "5.1", "is_group": False},
    {"code": "5.1.5040", "name": "Material Sampling / Prototype Cost", "parent_code": "5.1", "is_group": False},
    {"code": "5.2", "name": "Operating Expenses", "parent_code": "5", "is_group": True},
    {"code": "5.2.5100", "name": "Salaries & Wages", "parent_code": "5.2", "is_group": False},
    {"code": "5.2.5110", "name": "Office Rent", "parent_code": "5.2", "is_group": False},
    {"code": "5.2.5120", "name": "Utilities", "parent_code": "5.2", "is_group": True},
    {"code": "5.2.51201", "name": "Electricity Expenses", "parent_code": "5.2.5120", "is_group": False},
    {"code": "5.2.51202", "name": "Internet Expenses", "parent_code": "5.2.5120", "is_group": False},
    {"code": "5.2.51203", "name": "Gas Expenses", "parent_code": "5.2.5120", "is_group": False},
    {"code": "5.2.51204", "name": "Mobile Expenses", "parent_code": "5.2.5120", "is_group": False},
    {"code": "5.2.51205", "name": "Water Expenses", "parent_code": "5.2.5120", "is_group": False},
    {"code": "5.2.5130", "name": "Marketing & Advertisement", "parent_code": "5.2", "is_group": False},
    {"code": "5.2.5140", "name": "Vehicle Fuel & Maintenance", "parent_code": "5.2", "is_group": True},
    {"code": "5.2.51401", "name": "ABK-804 Suzuki Khyber", "parent_code": "5.2.5140", "is_group": True},
    {"code": "5.2.514011", "name": "ABK-804 Repair Expenses", "parent_code": "5.2.51401", "is_group": False},
    {"code": "5.2.514012", "name": "ABK-804 Running Expenses", "parent_code": "5.2.51401", "is_group": False},
    {"code": "5.2.51402", "name": "V-8962 D-Charade", "parent_code": "5.2.5140", "is_group": True},
    {"code": "5.2.514021", "name": "V-8962 Repair Expenses", "parent_code": "5.2.51402", "is_group": False},
    {"code": "5.2.514022", "name": "V-8962 Running Expenses", "parent_code": "5.2.51402", "is_group": False},
    {"code": "5.2.5141", "name": "Motor Cycle Expenses", "parent_code": "5.2", "is_group": True},
    {"code": "5.2.51411", "name": "Motor Cycle Repair Expenses", "parent_code": "5.2.5141", "is_group": False},
    {"code": "5.2.51412", "name": "Motor Cycle Running Expenses", "parent_code": "5.2.5141", "is_group": False},
    {"code": "5.2.5142", "name": "KVH-9229 Honda CD-125", "parent_code": "5.2", "is_group": True},
    {"code": "5.2.51421", "name": "KVH-9229 Repair Expenses", "parent_code": "5.2.5142", "is_group": False},
    {"code": "5.2.51422", "name": "KVH-9229 Running Expenses", "parent_code": "5.2.5142", "is_group": False},
    {"code": "5.2.5143", "name": "Conveyance Charges", "parent_code": "5.2", "is_group": False},
    {"code": "5.2.5144", "name": "Carriage Charges", "parent_code": "5.2", "is_group": False},
    {"code": "5.2.5150", "name": "Office Supplies", "parent_code": "5.2", "is_group": False},
    {"code": "5.2.51501", "name": "Maintenance Supplies & Repairs", "parent_code": "5.2.5150", "is_group": False},
    {"code": "5.2.51502", "name": "Printing Expenses", "parent_code": "5.2.5150", "is_group": False},
    {"code": "5.2.51503", "name": "Stationery Expenses", "parent_code": "5.2.5150", "is_group": False},
    {"code": "5.2.5160", "name": "Legal & Professional Fees (SECP, FBR, etc.)", "parent_code": "5.2", "is_group": False},
    {"code": "5.2.5170", "name": "Bank Charges", "parent_code": "5.2", "is_group": False},
    {"code": "5.2.5180", "name": "Depreciation Expense", "parent_code": "5.2", "is_group": False},
    {"code": "5.3", "name": "Other Expenses", "parent_code": "5", "is_group": True},
    {"code": "5.3.5300", "name": "Miscellaneous Expense", "parent_code": "5.3", "is_group": False},
    {"code": "5.3.5310", "name": "Donations / CSR (if applicable)", "parent_code": "5.3", "is_group": False},
    {"code": "5.3.5320", "name": "Partner Expense Control A/C", "parent_code": "5.3", "is_group": False},
]
bank_vouchers     = []          # List of dicts
cash_vouchers     = []
journal_vouchers  = []
sales_vouchers    = []
purchase_vouchers = []

logs = []                       # List of dicts: {'username', 'action', 'timestamp'}

# Helper Functions

def get_account_name(code):
    """Account code se name return karega"""
    acc = next((a for a in chart_of_accounts if a['code'] == code), None)
    return acc['name'] if acc else f"Unknown ({code})"


def get_posting_accounts():
    """Voucher dropdown ke liye sirf ledger accounts (non-group) return karega"""
    return [acc for acc in chart_of_accounts if not acc.get("is_group", False)]


def log_action(username, action):
    """Users Log mein entry add karega"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append({
        "username": username,
        "action": action,
        "timestamp": timestamp
    })
    # Agar database save karna hai toh yahan call karo
    # from database import save_log
    # save_log(username, action, timestamp)


def reload_vouchers():
    """Data fresh load karne ka function (database se baad mein connect kar sakte ho)"""
    global chart_of_accounts, bank_vouchers, cash_vouchers, journal_vouchers
    global sales_vouchers, purchase_vouchers, users, logs

    # Agar database.py se load kar rahe ho toh yahan uncomment kar do
    try:
        from database import load_chart_of_accounts, load_vouchers, load_logs
        chart_of_accounts = load_chart_of_accounts()
        bank_vouchers     = load_vouchers('bank')
        cash_vouchers     = load_vouchers('cash')
        journal_vouchers  = load_vouchers('journal')
        sales_vouchers    = load_vouchers('sales')
        purchase_vouchers = load_vouchers('purchase')
        logs              = load_logs()
    except Exception as e:
        print("Warning: Database load failed - using in-memory data only")
        print(e)

    # Debug ke liye print
    print("Reloaded vouchers - Chart accounts count:", len(chart_of_accounts))
    print("Bank vouchers count:", len(bank_vouchers))
    print("Cash vouchers count:", len(cash_vouchers))
    print("Journal vouchers count:", len(journal_vouchers))
    print("Sales vouchers count:", len(sales_vouchers))
    print("Purchase vouchers count:", len(purchase_vouchers))
    print("Users count:", len(users))
    print("Logs count:", len(logs))