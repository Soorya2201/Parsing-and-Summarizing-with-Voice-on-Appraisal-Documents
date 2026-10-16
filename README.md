# Appraisal Report Parser with Voice Summary

**Extracts structured data from commercial real-estate appraisal PDFs (valuation, financials, expenses, comparable sales, unit mix) and reads a spoken summary aloud.**

## Pipeline

```
appraisal PDF
  ├─ pdfplumber text extraction ─(empty?)─► PyPDF2 fallback ─(scanned?)─► Tesseract OCR via pdf2image
  ▼
regex field extraction ─► appraisal_data.json + CSVs (comparables, unit mix, financials)
  ▼
plain-English summary ─► gTTS speech (MP3)        Whisper: speech-to-text for spoken questions/notes
```

## What gets extracted (`PDF_PARSER.py`)

| Section | Fields |
|---|---|
| Property | name, address, city/state/ZIP, total units, acreage |
| Valuation | final reconciled value, sales-comparison value, income-approach value, effective date |
| Financials | potential and effective gross income, vacancy and vacancy rate, total expenses, NOI, cap rate, expense ratio |
| Expenses | management, utilities, maintenance, property taxes, insurance, reserves |
| Comparables | per sale: address, price, units, price per unit, sale date |
| Unit mix | count, bedrooms, bathrooms, rent per unit type |

Three-level text extraction keeps it working across digitally generated PDFs, odd encodings and scanned reports. `OCRAppraisalParser` switches to OCR automatically when fewer than 100 characters of text are found.

## Run it

```bash
pip install -r requirements.txt        # OCR also needs the tesseract and poppler binaries
python PDF_PARSER.py Appraisal-Report.pdf     # writes appraisal_data.json + appraisal_tables/*.csv
python TTS_Whisper.py appraisal_data.json     # writes appraisal_output.mp3
```

## Limitations

Field extraction is regex-based, so it is tuned to common appraisal report layouts and will miss fields in unusual formats. A layout-aware model (e.g. LayoutLM, or an LLM with structured output) would generalize better; the JSON schema here would carry over unchanged.
