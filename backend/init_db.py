import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), 'sample_data.csv')

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Create FTS5 virtual table
    cur.execute('''CREATE VIRTUAL TABLE products_fts USING fts5(
        product_name,
        company_name,
        seller_contact,
        website,
        catalogue_link,
        description
    )''')

    with open(SAMPLE_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append((r['product_name'], r['company_name'], r['seller_contact'], r['website'], r['catalogue_link'], r.get('description','')))

    cur.executemany('INSERT INTO products_fts(product_name, company_name, seller_contact, website, catalogue_link, description) VALUES (?,?,?,?,?,?)', rows)
    conn.commit()
    conn.close()
    print('Initialized', DB_PATH)

if __name__ == '__main__':
    init_db()
