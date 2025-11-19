"""
AI-Enhanced Document Extraction using Gemini API
Intelligently extracts key-value data with contextual understanding.
"""

import re
import pandas as pd
import PyPDF2
import json
import os
from typing import List, Dict

# New Import for loading environment variables
from dotenv import load_dotenv

# Google GenAI SDK Imports
from google import genai
from google.genai.errors import APIError

# --- Load API Key from .env file ---
# This is where the GEMINI_API_KEY is loaded from the .env file
load_dotenv() 

class AIDocumentExtractor:
    """
    Uses Gemini AI to intelligently extract and structure document data
    """
    
    def __init__(self, pdf_path: str, use_ai: bool = True):
        self.pdf_path = pdf_path
        self.text_content = ""
        self.use_ai = use_ai
        
    def extract_text_from_pdf(self) -> str:
        """Extract raw text from PDF"""
        # ... (unchanged PyPDF2 logic) ...
        text = ""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file) 
                for page in pdf_reader.pages:
                    page_text = page.extract_text() 
                    if page_text:
                        text += page_text + "\n" 
                self.text_content = text
                return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def extract_with_gemini(self) -> List[Dict]:
        """
        Use Gemini API to intelligently extract structured data using JSON mode.
        The client automatically picks up the API key from the environment.
        """
        
        # --- GEMINI API SETUP ---
        # The client will automatically find the GEMINI_API_KEY 
        # because of the load_dotenv() call at the top.
        try:
            # Note: No api_key argument is needed here!
            client = genai.Client()
        except Exception as e:
            print("Error initializing Gemini client. The GEMINI_API_KEY environment variable is likely missing or incorrect.")
            print(f"Details: {e}")
            return []

        # ... (unchanged prompt and schema) ...
        prompt = f"""You are a data extraction expert. Extract ALL information from the following document into a structured key-value format.

DOCUMENT TEXT:
{self.text_content}

INSTRUCTIONS:
1. Extract **EVERY** piece of information - nothing should be omitted.
2. Create logical key-value pairs (e.g., "First Name" : "Vijay").
3. For each key-value pair, add relevant **CONTEXT** from the document in a "comments" field.
4. Context should be the **EXACT** original sentences from the document that provide additional information.
5. Preserve original wording - do not paraphrase.
6. Format dates as DD-MMM-YY (e.g., 15-Mar-89).
7. The output **MUST** be a JSON array that strictly adheres to the provided schema. Do not add any extra text or markdown wrappers like ```json.

Extract ALL information systematically covering:
- Personal details (name, DOB, age, blood group, nationality)
- Professional history (all jobs, dates, salaries, designations)
- Education (schools, colleges, degrees, scores, years)
- Certifications (names, scores, years)
- Technical skills"""

        json_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The field name, e.g., 'First Name', 'Employer Name'"},
                    "value": {"type": "string", "description": "The extracted value, e.g., 'Vijay', 'Google Inc.'"},
                    "comments": {"type": "string", "description": "The exact original contextual sentence(s) from the document related to the key-value pair."}
                },
                "required": ["key", "value", "comments"]
            }
        }
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=json_schema,
                    temperature=0.0
                ),
            )
            
            extracted_data = json.loads(response.text)
            return extracted_data
                
        except APIError as e:
            print(f"Error with Gemini API: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response from Gemini: {e}")
            # print(f"Raw response text: {getattr(response, 'text', 'N/A')}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during the API call: {e}")
            return []
    
    def process_document(self) -> pd.DataFrame:
        """Main processing pipeline"""
        # ... (unchanged processing logic) ...
        self.extract_text_from_pdf()
        
        if self.use_ai:
            extracted_data = self.extract_with_gemini()
        else:
            extracted_data = self.rule_based_extraction()
        
        df = pd.DataFrame(extracted_data)
        
        if not df.empty:
            df = df[['key', 'value', 'comments']]
            df.insert(0, '#', range(1, len(df) + 1))
            df.columns = ['#', 'Key', 'Value', 'Comments']
        
        return df
    
    def rule_based_extraction(self) -> List[Dict]:
        """Fallback rule-based extraction if AI is not available"""
        return []
    
    def save_to_excel(self, output_path: str = 'Output.xlsx'):
        """Save extracted data to Excel with formatting"""
        df = self.process_document()
        
        if df.empty:
             print("No data extracted. Skipping Excel save.")
             return df
        
        # ... (unchanged Excel saving logic) ...
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Extracted Data')
            
            workbook = writer.book
            worksheet = writer.sheets['Extracted Data']
            
            worksheet.column_dimensions['A'].width = 5
            worksheet.column_dimensions['B'].width = 35
            worksheet.column_dimensions['C'].width = 30
            worksheet.column_dimensions['D'].width = 100
            
            from openpyxl.styles import Alignment
            for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, 
                                            min_col=4, max_col=4):
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
        
        print(f"Data successfully extracted and saved to {output_path}")
        print(f"Total records extracted: {len(df)}")
        return df


# Main execution
if __name__ == "__main__":
    import sys
    
    pdf_path = "Data Input.pdf" if len(sys.argv) < 2 else sys.argv[1]
    output_path = "Output.xlsx" if len(sys.argv) < 3 else sys.argv[2]
    use_ai = True if len(sys.argv) < 4 else sys.argv[3].lower() == 'true' 
    
    print("Initializing AI Document Extractor...")
    
    if not os.path.exists(pdf_path):
        print(f"Error: The specified PDF file was not found at path: {pdf_path}")
    else:
        extractor = AIDocumentExtractor(pdf_path, use_ai=use_ai)
        
        print("Extracting data from document...")
        result_df = extractor.save_to_excel(output_path)
        
        print("\n" + "="*80)
        print("EXTRACTION COMPLETE")
        print("="*80)
        print(f"\nPreview of extracted data:")
        print(result_df.head(10).to_string())
        print(f"\n... ({len(result_df)} total records)")