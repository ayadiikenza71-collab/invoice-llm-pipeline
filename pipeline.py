import glob
import json
import os
import sqlite3

import matplotlib.pyplot as plt
import ollama
import pandas as pd
import pdfplumber

MODEL = "llama3.2:3b"

PROMPT = """Extract these fields from the invoice text below.
Answer with JSON only, using exactly these keys:
invoice_number (string), vendor (string), date (format YYYY-MM-DD),
product (string), quantity (number), unit_price (number), total (number).

Invoice text:
{text}
"""


def read_pdf(path):
    """Step 1: read the text of a PDF."""
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def extract_fields(text):
    """Step 2: ask the local LLM to extract the fields as JSON."""
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.format(text=text)}],
        format="json",
        options={"temperature": 0},
    )
    return json.loads(response["message"]["content"])


def validate(df):
    """Step 3: clean types and check the data quality."""
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["quantity", "unit_price", "total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Quality rule: quantity x unit price must equal the total
    df["total_ok"] = (df["quantity"] * df["unit_price"] - df["total"]).abs() < 0.01
    # Required fields must not be missing
    required = df[["invoice_number", "vendor", "date", "total"]].notna().all(axis=1)
    df["valid"] = required & df["total_ok"]
    return df


def make_chart(df):
    """Step 5: chart of total amount per vendor."""
    summary = df[df["valid"]].groupby("vendor")["total"].sum().sort_values()
    summary.plot(kind="barh", color="#2a9d8f")
    plt.title("Total invoiced amount per vendor (USD)")
    plt.xlabel("USD")
    plt.tight_layout()
    plt.savefig("output/total_per_vendor.png", dpi=150)
    plt.close()


def main():
    os.makedirs("output", exist_ok=True)
    rows = []
    for path in sorted(glob.glob("data/raw/*.pdf")):
        try:
            data = extract_fields(read_pdf(path))
            data["source_file"] = os.path.basename(path)
            rows.append(data)
            print("OK    ", path)
        except Exception as error:
            print("FAILED", path, error)

    df = validate(pd.DataFrame(rows))
    print(f"\n{df['valid'].sum()} valid invoices out of {len(df)}")

    make_chart(df)

    # Step 4: store in SQL (SQLite) and export a CSV
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    with sqlite3.connect("output/invoices.db") as conn:
        df.to_sql("invoices", conn, if_exists="replace", index=False)
    df.to_csv("output/invoices.csv", index=False)
    print("Saved: output/invoices.db, output/invoices.csv, output/total_per_vendor.png")


if __name__ == "__main__":
    main()