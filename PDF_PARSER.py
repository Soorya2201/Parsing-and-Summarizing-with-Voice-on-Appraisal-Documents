import re
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import PyPDF2
import pdfplumber
from pathlib import Path

class AppraisalReportParser:
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.data = {}
        
    def extract_text(self) -> str:
        text = ""
        
        # Extracting text from pdf using two ways 
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            
        if not text.strip():
            try:
                with open(self.pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                print(f"PyPDF2 extraction failed: {e}")
        
        self.text = text
        return text
    
    def extract_property_info(self) -> Dict:
        property_info = {}
        
        # Property name
        name_pattern = r"Subject[:\s]+([^\n]+(?:Apartments|Housing|Complex)[^\n]*)"
        name_match = re.search(name_pattern, self.text, re.IGNORECASE)
        if name_match:
            property_info['name'] = name_match.group(1).strip()
        
        # Address
        address_pattern = r"(?:Address|Location)[:\s]*\n?\s*(\d+[^\n]+)\n?\s*([A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5})"
        address_match = re.search(address_pattern, self.text, re.IGNORECASE)
        if address_match:
            property_info['address'] = address_match.group(1).strip()
            property_info['city_state_zip'] = address_match.group(2).strip()
        
        # Units
        units_pattern = r"(\d+)\s+Unit"
        units_match = re.search(units_pattern, self.text, re.IGNORECASE)
        if units_match:
            property_info['total_units'] = int(units_match.group(1))
        
        # Acres
        acres_pattern = r"(\d+\.?\d*)\s+acres?"
        acres_match = re.search(acres_pattern, self.text, re.IGNORECASE)
        if acres_match:
            property_info['acres'] = float(acres_match.group(1))
        
        # # Zoning
        # zoning_pattern = r"Zoning[:\s]+([^\n]+)"
        # zoning_match = re.search(zoning_pattern, self.text, re.IGNORECASE)
        # if zoning_match:
        #     property_info['zoning'] = zoning_match.group(1).strip()
        
        return property_info
    
    def extract_valuation(self) -> Dict:
        valuation = {}
        
        # Final value
        final_pattern = r"(?:Final|Reconciled|Concluded)[\s\w]*Value[:\s]*\$?\s*([\d,]+)"
        final_match = re.search(final_pattern, self.text, re.IGNORECASE)
        if final_match:
            valuation['final_value'] = int(final_match.group(1).replace(',', ''))
        
        # Sales comparison value
        sales_pattern = r"Sales Comparison[^$]*\$\s*([\d,]+)"
        sales_match = re.search(sales_pattern, self.text, re.IGNORECASE)
        if sales_match:
            valuation['sales_comparison_value'] = int(sales_match.group(1).replace(',', ''))
        
        # Income approach value
        income_pattern = r"Income Approach[^$]*\$\s*([\d,]+)"
        income_match = re.search(income_pattern, self.text, re.IGNORECASE)
        if income_match:
            valuation['income_approach_value'] = int(income_match.group(1).replace(',', ''))
        
        # Effective date
        date_pattern = r"(?:Effective Date|Date of Value)[:\s]+([A-Za-z]+\s+\d{1,2},\s+\d{4})"
        date_match = re.search(date_pattern, self.text, re.IGNORECASE)
        if date_match:
            valuation['effective_date'] = date_match.group(1).strip()
        
        return valuation
    
    def extract_financials(self) -> Dict:
        financials = {}
        
        # Potential Gross Income
        pgi_pattern = r"Potential Gross Income[:\s]*\$?\s*([\d,]+)"
        pgi_match = re.search(pgi_pattern, self.text, re.IGNORECASE)
        if pgi_match:
            financials['potential_gross_income'] = int(pgi_match.group(1).replace(',', ''))
        
        # Vacancy
        vacancy_pattern = r"Vacancy[^$]*\$?\s*([\d,]+)"
        vacancy_match = re.search(vacancy_pattern, self.text, re.IGNORECASE)
        if vacancy_match:
            financials['vacancy'] = int(vacancy_match.group(1).replace(',', ''))
        
        # Vacancy Rate
        vacancy_rate_pattern = r"Vacancy[^\d]*([\d.]+)%"
        vacancy_rate_match = re.search(vacancy_rate_pattern, self.text)
        if vacancy_rate_match:
            financials['vacancy_rate'] = float(vacancy_rate_match.group(1))
        
        # Effective Gross Income
        egi_pattern = r"Effective Gross Income[:\s]*\$?\s*([\d,]+)"
        egi_match = re.search(egi_pattern, self.text, re.IGNORECASE)
        if egi_match:
            financials['effective_gross_income'] = int(egi_match.group(1).replace(',', ''))
        
        # Total Expenses
        expenses_pattern = r"Total Expenses[:\s]*\$?\s*([\d,]+)"
        expenses_match = re.search(expenses_pattern, self.text, re.IGNORECASE)
        if expenses_match:
            financials['total_expenses'] = int(expenses_match.group(1).replace(',', ''))
        
        # Net Operating Income
        noi_pattern = r"Net Operating Income[:\s]*\$?\s*([\d,]+)"
        noi_match = re.search(noi_pattern, self.text, re.IGNORECASE)
        if noi_match:
            financials['net_operating_income'] = int(noi_match.group(1).replace(',', ''))
        
        # Cap Rate
        cap_pattern = r"(?:Cap|Capitalization)\s+Rate[:\s]*([\d.]+)%"
        cap_match = re.search(cap_pattern, self.text, re.IGNORECASE)
        if cap_match:
            financials['cap_rate'] = float(cap_match.group(1))
        
        # Expense Ratio
        expense_ratio_pattern = r"Expense Ratio[^:]*:\s*([\d.]+)%"
        expense_ratio_match = re.search(expense_ratio_pattern, self.text, re.IGNORECASE)
        if expense_ratio_match:
            financials['expense_ratio'] = float(expense_ratio_match.group(1))
        
        return financials
    
    def extract_expenses(self) -> Dict:
        expenses = {}
        
        expense_categories = [
            ('management', r"Management[:\s]*\$?\s*([\d,]+)"),
            ('utilities', r"Utilities[:\s]*\$?\s*([\d,]+)"),
            ('maintenance', r"(?:Repair|Maintenance)[:\s]*\$?\s*([\d,]+)"),
            ('property_taxes', r"Property Tax(?:es)?[:\s]*\$?\s*([\d,]+)"),
            ('insurance', r"Insurance[:\s]*\$?\s*([\d,]+)"),
            ('reserves', r"Reserves[:\s]*\$?\s*([\d,]+)"),
        ]
        
        for category, pattern in expense_categories:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                
                if amount_str:
                    try:
                        expenses[category] = int(amount_str)
                    except ValueError:
                        print(f"Warning: Could not convert expense amount for {category}: '{amount_str}'")
        return expenses
    
    def extract_comparables(self) -> List[Dict]:
        comparables = []

        comp_pattern = r"(?:Comparable|Sale)\s*#?\s*(\d+)[^\n]*\n((?:.*\n){1,20})"
        matches = re.finditer(comp_pattern, self.text, re.IGNORECASE)
        
        for match in matches:
            comp_num = match.group(1)
            comp_text = match.group(2)
            comp_data = {'id': int(comp_num)}
            
            # Extract address
            address_pattern = r"(?:Address|Location)[:\s]*([^\n]+)"
            addr_match = re.search(address_pattern, comp_text, re.IGNORECASE)
            if addr_match:
                comp_data['address'] = addr_match.group(1).strip()
            
            # Extract price
            price_pattern = r"\$\s*([\d,]+)"
            price_match = re.search(price_pattern, comp_text)
            if price_match:
                comp_data['price'] = int(price_match.group(1).replace(',', ''))
            
            # Extract units
            units_pattern = r"(\d+)\s+[Uu]nit"
            units_match = re.search(units_pattern, comp_text)
            if units_match:
                comp_data['units'] = int(units_match.group(1))
            
            # Extract price per unit
            ppu_pattern = r"(?:Price|Sale)\s+per\s+Unit[:\s]*\$?\s*([\d,]+)"
            ppu_match = re.search(ppu_pattern, comp_text, re.IGNORECASE)
            if ppu_match:
                comp_data['price_per_unit'] = int(ppu_match.group(1).replace(',', ''))
            
            # Extract date
            date_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
            date_match = re.search(date_pattern, comp_text)
            if date_match:
                comp_data['date'] = date_match.group(1)
            
            if len(comp_data) > 1:  # Has more than just ID
                comparables.append(comp_data)
        return comparables
    
    def extract_unit_mix(self) -> List[Dict]:
        unit_mix = []
        
        # Pattern for unit mix lines
        unit_pattern = r"(\d+)\s+(?:each\s+)?(\d+)\s*BR\s*/\s*(\d+(?:\.\d+)?)\s*BA[^\d]*\$?\s*([\d,]+)"
        matches = re.finditer(unit_pattern, self.text, re.IGNORECASE)
        
        for match in matches:
            unit_data = {
                'count': int(match.group(1)),
                'bedrooms': int(match.group(2)),
                'bathrooms': float(match.group(3)),
                'rent': int(match.group(4).replace(',', ''))
            }
            unit_mix.append(unit_data)
        return unit_mix
    
    def parse(self) -> Dict:
        print("Extracting text from PDF...")
        self.extract_text()
        
        if not self.text:
            raise ValueError("Could not extract text from PDF")
      
        self.data['property'] = self.extract_property_info()
        self.data['valuation'] = self.extract_valuation()
        self.data['financials'] = self.extract_financials()
        self.data['expenses'] = self.extract_expenses()
        self.data['comparables'] = self.extract_comparables()
        self.data['unit_mix'] = self.extract_unit_mix()
        return self.data
    
    def save_json(self, output_path: str):
        with open(output_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"Data saved to {output_path}")
    
    def save_csv(self, output_dir: str):
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Save comparables
        if self.data.get('comparables'):
            df = pd.DataFrame(self.data['comparables'])
            df.to_csv(output_dir / 'comparables.csv', index=False)
            print(f"Comparables saved to {output_dir / 'comparables.csv'}")
        
        # Save unit mix
        if self.data.get('unit_mix'):
            df = pd.DataFrame(self.data['unit_mix'])
            df.to_csv(output_dir / 'unit_mix.csv', index=False)
            print(f"Unit mix saved to {output_dir / 'unit_mix.csv'}")
        
        # Save financials as CSV
        if self.data.get('financials'):
            df = pd.DataFrame([self.data['financials']])
            df.to_csv(output_dir / 'financials.csv', index=False)
    
    def print_summary(self):
        print("\n" + "="*60)
        print("APPRAISAL REPORT SUMMARY")
      
        
        if 'property' in self.data:
            print("\n📍 PROPERTY INFORMATION:")
            for key, value in self.data['property'].items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
        
        if 'valuation' in self.data:
            print("\n💰 VALUATION:")
            for key, value in self.data['valuation'].items():
                if isinstance(value, int):
                    print(f"  {key.replace('_', ' ').title()}: ${value:,}")
                else:
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        
        if 'financials' in self.data:
            print("\n📊 FINANCIALS:")
            for key, value in self.data['financials'].items():
                if isinstance(value, int):
                    print(f"  {key.replace('_', ' ').title()}: ${value:,}")
                elif isinstance(value, float):
                    print(f"  {key.replace('_', ' ').title()}: {value}%")
        
        if 'comparables' in self.data:
            print(f"\n🏘️  COMPARABLES: {len(self.data['comparables'])} found")
        
        if 'unit_mix' in self.data:
            print(f"\n🏠 UNIT MIX: {len(self.data['unit_mix'])} unit types")
        
        print("\n" + "="*60 + "\n")


class OCRAppraisalParser(AppraisalReportParser):
    
    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        try:
            import pytesseract
            from pdf2image import convert_from_path
            self.pytesseract = pytesseract
            self.convert_from_path = convert_from_path
            self.ocr_available = True
        except ImportError:
            self.ocr_available = False
    
    def extract_text_ocr(self) -> str:
        if not self.ocr_available:
            print("OCR not available, falling back to regular extraction")
            return super().extract_text()
        images = self.convert_from_path(self.pdf_path)
        
        text = ""
        for i, image in enumerate(images, 1):
            print(f"Processing page {i}/{len(images)}...")
            page_text = self.pytesseract.image_to_string(image)
            text += page_text + "\n"
        self.text = text
        return text
    
    def extract_text(self) -> str:
        text = super().extract_text()
        if len(text.strip()) < 100 and self.ocr_available:
            print("Little text found, trying OCR...")
            text = self.extract_text_ocr()
        return text

if __name__ == "__main__":
    import sys
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "Appraisal-Report.pdf"
    parser = OCRAppraisalParser(pdf_path)   # falls back to OCR for scanned PDFs
    data = parser.parse()
    parser.print_summary()
    parser.save_json("appraisal_data.json")
    parser.save_csv("appraisal_tables")
    