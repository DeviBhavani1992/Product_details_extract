import os
import tempfile
from fastapi import FastAPI, UploadFile, File
from pymongo import MongoClient
from pdf2image import convert_from_path
import pytesseract
from langdetect import detect
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# MongoDB
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["pdf_text_db"]
collection = db["extracted_text"]


def extract_pdf_text(pdf_path):
    text = ""
    images = convert_from_path(pdf_path)
    for img in images:
        text += pytesseract.image_to_string(img)
    return text


def structure_text_with_gpt(text):
    response = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """
You are a product catalogue extraction assistant.

FIRST:
Extract company details from entire text:
- company_name
- contact_number
- website

These usually appear:
- first page
- last page
- footer/header sections

If website appears anywhere, apply it to ALL products.

THEN:
Extract all products.

OUTPUT JSON ONLY:
[
{
  "product_name": "",
  "company_name": "",
  "contact_number": "",
  "website": "",
  "description": "",
  "catalogue_link": null
}
]

STRICT RULES:

1. Extract ALL products, even if repeated with:
   - different pack size
   - flavor variant
   - weight/volume
   → treat them as separate products.

2. Fix OCR mistakes logically:
   Example:
   "320m!" → "320ml"
   "Oldeniandia" → "Oldenlandia"

3. Ignore company description text.

4. Include pack size inside description.

5. Do NOT summarize.

6. Expected output size:
   Around 40–60 products.

7. Output MUST be valid JSON only.
- Website must be extracted even if outside product section.
- Look carefully for URLs like:
  www.*, .com, .sg, http.
- Fix OCR errors logically.
- Do NOT skip last page text.
"""
            },
            {"role": "user", "content": text}
        ]
    )

    return response.choices[0].message.content

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            temp_path = tmp.name

        text = extract_pdf_text(temp_path)

        try:
            lang = detect(text)
        except:
            lang = "none"

        structured_data = structure_text_with_gpt(text)

        data = {
            "file_name": file.filename,
            "language": lang,
            "raw_text": text,
            "structured_json": structured_data
        }

        collection.insert_one(data)
        os.remove(temp_path)

        return {"status": "success"}

    except Exception as e:
        return {"error": str(e)}