#!/usr/bin/env python3
"""OCR-extract text from PDFs (image-based).

Usage:
  python3 backend/ocr_extract.py --input-dir /path/to/pdfs --output-dir /path/to/output --lang eng

Requirements:
  - Python packages: pdf2image, pytesseract, Pillow
  - System packages: tesseract-ocr, poppler-utils (on Debian/Ubuntu)
"""
import argparse
import os
from pdf2image import convert_from_path
import pytesseract


def ocr_pdf_to_text(pdf_path, dpi=300, lang='eng'):
    pages = convert_from_path(pdf_path, dpi=dpi)
    texts = []
    for i, img in enumerate(pages):
        text = pytesseract.image_to_string(img, lang=lang)
        texts.append(text)
    return "\n\n---PAGE_BREAK---\n\n".join(texts)


def process_directory(input_dir, output_dir, dpi=300, lang='eng'):
    os.makedirs(output_dir, exist_ok=True)
    pdfs = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not pdfs:
        print('No PDF files found in', input_dir)
        return
    for pdf in pdfs:
        pdf_path = os.path.join(input_dir, pdf)
        try:
            print('Processing', pdf)
            text = ocr_pdf_to_text(pdf_path, dpi=dpi, lang=lang)
            out_name = os.path.splitext(pdf)[0] + '.txt'
            out_path = os.path.join(output_dir, out_name)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print('Wrote', out_path)
        except Exception as e:
            print('Error processing', pdf, e)


def main():
    p = argparse.ArgumentParser(description='OCR PDF directory (image-based PDFs)')
    p.add_argument('--input-dir', required=True)
    p.add_argument('--output-dir', required=True)
    p.add_argument('--dpi', type=int, default=300)
    p.add_argument('--lang', default='eng')
    args = p.parse_args()
    process_directory(args.input_dir, args.output_dir, dpi=args.dpi, lang=args.lang)


if __name__ == '__main__':
    main()
