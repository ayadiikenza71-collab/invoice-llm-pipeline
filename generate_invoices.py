import os
import random
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

os.makedirs("data/raw", exist_ok=True)
random.seed(42)

vendors = ["AgroTrade SA", "Sahara Grains", "Medina Foods", "Atlas Commodities", "Carthage Oils"]
products = [("Wheat", 320), ("Corn", 250), ("Sugar", 410), ("Soybean", 480), ("Olive oil", 3200)]

for i in range(1, 11):
    vendor = random.choice(vendors)
    product, unit_price = random.choice(products)
    quantity = random.randint(5, 50)
    total = quantity * unit_price
    inv_date = date(2026, 1, 1) + timedelta(days=random.randint(0, 300))

    c = canvas.Canvas(f"data/raw/invoice_{i:02d}.pdf", pagesize=A4)
    y = 780
    for line in [
        f"INVOICE No: INV-2026-{i:03d}",
        f"Vendor: {vendor}",
        f"Date: {inv_date.strftime('%d/%m/%Y')}",
        f"Product: {product}",
        f"Quantity (tons): {quantity}",
        f"Unit price (USD per ton): {unit_price}",
        f"TOTAL: {total} USD",
    ]:
        c.drawString(60, y, line)
        y -= 30
    c.save()

print("Done: 10 invoices created in data/raw/")