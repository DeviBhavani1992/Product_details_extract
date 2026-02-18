#!/usr/bin/env python3
"""Extract text from PDFs (image-based) and ingest product details into SQLite database.

Usage:
  python3 backend/pdf_ingestion.py --input-dir backend/Set\ 1\ -\ Foods --output-dir /tmp/extracted_texts

Requirements:
  - System: tesseract-ocr, poppler-utils
  - Python: pdf2image, pytesseract, PyPDF2, Pillow
"""
import argparse
import os
import sqlite3
import re
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader

DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')


def extract_text_pypdf(pdf_path):
    """Try text extraction first (for searchable PDFs)."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            if text.strip():
                return text
    except Exception as e:
        print(f'  PyPDF2 failed: {e}')
    return None


def extract_text_ocr(pdf_path, dpi=200):
    """OCR extraction for image-based PDFs."""
    try:
        pages = convert_from_path(pdf_path, dpi=dpi)
        texts = []
        for img in pages:
            text = pytesseract.image_to_string(img, lang='eng')
            texts.append(text)
        return "\n\n---PAGE_BREAK---\n\n".join(texts)
    except Exception as e:
        print(f'  OCR failed: {e}')
        return None


def extract_pdf_text(pdf_path, dpi=200):
    """Extract text from PDF, try PyPDF2 first, then OCR."""
    print(f'Extracting: {os.path.basename(pdf_path)}')
    text = extract_text_pypdf(pdf_path)
    if not text:
        print('  PyPDF2 returned empty, trying OCR...')
        text = extract_text_ocr(pdf_path, dpi=dpi)
    return text or ''


def parse_product_details(text, pdf_filename):
    """Parse product details from extracted text.
    
    Heuristic: look for common patterns like phone numbers, company names, etc.
    Falls back to filename as product name.
    """
    # Clean text
    text = text.strip()
    lines = text.split('\n')
    
    # Default values
    product_name = os.path.splitext(pdf_filename)[0]  # filename as product name
    company_name = product_name
    seller_contact = ''
    website = ''
    catalogue_link = pdf_filename
    description = text[:200] if text else ''  # First 200 chars as description
    
    # Try to find phone number (basic heuristic)
    phone_pattern = r'\b(\+?\d{1,3}[-.\s]?)?\d{7,15}\b'
    phones = re.findall(phone_pattern, text)
    if phones:
        seller_contact = phones[0]
    
    # Try to find website/email
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    emails = re.findall(email_pattern, text)
    if emails:
        website = emails[0]
    
    # Try to find website URL
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    if urls:
        website = urls[0]
    
    return {
        'product_name': product_name,
        'company_name': company_name,
        'seller_contact': seller_contact,
        'website': website,
        'catalogue_link': catalogue_link,
        'description': description
    }


def ingest_pdfs_to_db(input_dir, dpi=200):
    """Extract text from all PDFs in input_dir and ingest into database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Clear existing data or create table if needed
    try:
        cur.execute('DELETE FROM products_fts')
    except sqlite3.OperationalError:
        print('Table products_fts does not exist, creating...')
        cur.execute('''CREATE VIRTUAL TABLE products_fts USING fts5(
            product_name,
            company_name,
            seller_contact,
            website,
            catalogue_link,
            description
        )''')
    
    pdfs = sorted([f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')])
    print(f'Found {len(pdfs)} PDFs in {input_dir}')
    
    for i, pdf_filename in enumerate(pdfs, 1):
        pdf_path = os.path.join(input_dir, pdf_filename)
        text = extract_pdf_text(pdf_path, dpi=dpi)
        details = parse_product_details(text, pdf_filename)
        
        try:
            cur.execute('''INSERT INTO products_fts 
                (product_name, company_name, seller_contact, website, catalogue_link, description)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (details['product_name'], details['company_name'], details['seller_contact'],
                 details['website'], details['catalogue_link'], details['description']))
            print(f"  [{i}/{len(pdfs)}] Inserted: {details['product_name']}")
        except Exception as e:
            print(f"  [{i}/{len(pdfs)}] Error inserting: {e}")
    
    conn.commit()
    conn.close()
    print(f'Ingestion complete. {len(pdfs)} PDFs processed.')


def main():
    p = argparse.ArgumentParser(description='Extract text from PDFs and ingest into database')
    p.add_argument('--input-dir', required=True, help='Directory containing PDFs')
    p.add_argument('--dpi', type=int, default=200, help='DPI for OCR')
    args = p.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print(f'Error: {args.input_dir} is not a directory')
        return
    
    ingest_pdfs_to_db(args.input_dir, dpi=args.dpi)


if __name__ == '__main__':
    main()
