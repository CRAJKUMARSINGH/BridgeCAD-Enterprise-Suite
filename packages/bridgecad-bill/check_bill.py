from bridgecad_bill.rates_db import get_rates_db
db = get_rates_db()
print(f"Rates DB: {len(db)} items")
print(f"M30 substructure: INR {float(db.get('1701.3')):,.0f}/CUM")
print(f"Pile 1200mm: INR {float(db.get('1801.3')):,.0f}/RM")
print("M5 rates_db OK")
