"""
Streamlit UI for AI-Powered Document Extraction (Gemini API)
"""
import streamlit as st
import pandas as pd
import os
from io import BytesIO
import json
import PyPDF2 # Retaining PyPDF2 import as it was the previous fix

import re
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from typing import List, Dict

# Load environment variables from .env file
load_dotenv() 

class AIDocumentExtractor:
    """
    Core class to handle PDF text extraction and Gemini API calls for structured data.
    """

    def __init__(self, uploaded_file: BytesIO, use_ai: bool = True):
        self.uploaded_file = uploaded_file
        self.text_content = ""
        self.use_ai = use_ai
        
    def extract_text_from_pdf(self) -> str:
        """Extract raw text from PDF using the uploaded file object"""
        text = ""
        # The file pointer needs to be reset for PyPDF2 to read it correctly
        self.uploaded_file.seek(0) 
        try:
            pdf_reader = PyPDF2.PdfReader(self.uploaded_file) 
            for page in pdf_reader.pages:
                page_text = page.extract_text() 
                if page_text:
                    text += page_text + "\n"
            self.text_content = text
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return ""
    
    # Caching the expensive AI call prevents re-running if inputs don't change
    @st.cache_data(show_spinner="Running Gemini AI Extraction...")
    def extract_with_gemini(_self) -> List[Dict]:
        """
        Uses Gemini API (Flash model) for structured key-value extraction using JSON mode.
        """
        try:
            client = genai.Client()
        except Exception:
            # Handled at the UI level: API key check
            return []

        prompt = f"""You are a data extraction expert. Extract ALL information from the following document into a structured key-value format.

DOCUMENT TEXT:
{_self.text_content}

INSTRUCTIONS:
1. Extract **EVERY** piece of information - nothing should be omitted.
2. Create logical key-value pairs (e.g., "First Name" : "Vijay").
3. For each key-value pair, add relevant **CONTEXT** from the document in a "comments" field.
4. Context in "comments" should be the **EXACT** original sentences from the document that provide additional information. Do not modify or summarize these sentences.
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
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                    "comments": {"type": "string"}
                },
                "required": ["key", "value", "comments"]
            }
        }
        
        try:
            # Using the faster and more available gemini-2.5-flash model
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
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
            # The 503 error is typically handled here
            st.error(f"Gemini API Error: Please check your GEMINI_API_KEY and model configuration. Details: {e}")
            return []
        except json.JSONDecodeError:
            st.error("AI response was not valid JSON. Try again or modify the prompt instructions.")
            return []
        except Exception as e:
            st.error(f"An unexpected error occurred during AI processing: {e}")
            return []
    
    def process_document(self) -> pd.DataFrame:
        """Main processing pipeline"""
        self.extract_text_from_pdf()
        
        if self.use_ai and self.text_content:
            extracted_data = self.extract_with_gemini()
        else:
            extracted_data = [] 
        
        df = pd.DataFrame(extracted_data)
        
        if not df.empty:
            df = df[['key', 'value', 'comments']]
            df.insert(0, '#', range(1, len(df) + 1))
            df.columns = ['#', 'Key', 'Value', 'Comments']
        
        return df


# --- UI Utilities ---

def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    """Converts a pandas DataFrame to an Excel file in memory."""
    output = BytesIO()
    # Use xlsxwriter engine to ensure compatibility and styling options
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer: 
        df.to_excel(writer, index=False, sheet_name='Extracted Data')
    processed_data = output.getvalue()
    return processed_data

def check_api_key():
    """Checks for the presence of the Gemini API Key."""
    return os.getenv("GEMINI_API_KEY")

# --- Streamlit App Setup ---

st.set_page_config(
    page_title="AI Document Extractor",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📄 AI-Powered Document Key-Value Extractor")
st.caption("Leveraging structured data extraction from PDFs using Gemini Flash.")

if not check_api_key():
    st.error("🚨 **GEMINI_API_KEY not found!** Please create a `.env` file with your key or set it as an environment variable to run the extraction.")

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Using key="pdf_uploader" to access the uploaded file via st.session_state.pdf_uploader
    uploaded_file = st.file_uploader(
        "Upload a PDF Document", 
        type="pdf", 
        accept_multiple_files=False,
        key="pdf_uploader"
    )
    
    # Using key="use_ai_checkbox" to access its state
    use_ai = st.checkbox(
        "Enable Gemini AI Extraction", 
        value=True, 
        key="use_ai_checkbox", # <-- Added key for session state access
        help="Toggle AI-based extraction (default: On)"
    )
    
    # Process button
    if st.button("✨ Extract Data", key="extract_button", type="primary"):
        if not uploaded_file:
            st.warning("Please upload a PDF file to begin extraction.")
            st.stop()
        if not check_api_key() and use_ai:
            st.error("Cannot run AI extraction without the GEMINI_API_KEY.")
            st.stop()
        
        # Trigger the extraction run
        st.session_state['run_extraction'] = True
    
    # Clear button
    if st.button("🔄 Clear Results"):
        if 'extracted_df' in st.session_state:
            del st.session_state['extracted_df']
        if 'run_extraction' in st.session_state:
            del st.session_state['run_extraction']
        if 'extractor_instance' in st.session_state:
            del st.session_state['extractor_instance']
        st.cache_data.clear() # Clear the cache for fresh runs
        st.rerun()

# --- Main Content Area: Execution Logic ---

if 'run_extraction' in st.session_state and st.session_state['run_extraction']:
    try:
        # 1. Create extractor instance using values retrieved via session state keys
        extractor = AIDocumentExtractor(
            st.session_state.pdf_uploader, # Access file using key
            use_ai=st.session_state.use_ai_checkbox # Access checkbox value using key
        )
        
        # 2. Store the extractor object in session state to avoid NameError
        st.session_state['extractor_instance'] = extractor 

        with st.spinner("Extracting data... This may take a moment depending on document size and complexity."):
            result_df = extractor.process_document()
            
        if not result_df.empty:
            st.success(f"✅ Extraction Complete! Found **{len(result_df)}** key-value pairs.")
            st.session_state['extracted_df'] = result_df
            st.session_state['run_extraction'] = False 

        else:
            st.warning("No structured data could be extracted by the AI model. Check the console for details.")
            st.session_state['run_extraction'] = False 
    
    except Exception as e:
        st.error(f"An error occurred during file processing: {e}")
        st.session_state['run_extraction'] = False 
        
# Display results if available
if 'extracted_df' in st.session_state and not st.session_state['extracted_df'].empty:
    df = st.session_state['extracted_df']
    
    st.subheader("📊 Extracted Key-Value Pairs")
    st.dataframe(
        df, 
        use_container_width=True, 
        height=400,
        column_config={
            "#": st.column_config.NumberColumn(width="small"),
            "Key": st.column_config.TextColumn(width="medium"),
            "Value": st.column_config.TextColumn(width="medium"),
            "Comments": st.column_config.TextColumn(width="large")
        }
    )
    
    # Download Button
    excel_data = convert_df_to_excel(df)
    st.download_button(
        label="⬇️ Download Extracted Data as Excel",
        data=excel_data,
        file_name="Output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key='download_excel'
    )

    # Raw Text for Debugging (FIXED NameError: 'extractor')
    with st.expander("Peek at the Raw Text Content"):
        # 3. Retrieve the extractor object from session state
        if 'extractor_instance' in st.session_state:
            extractor_instance = st.session_state['extractor_instance']
            if extractor_instance.text_content:
                 st.text_area("Document Text", extractor_instance.text_content, height=300)
            else:
                 st.info("Raw text was empty or not generated (check PDF readability).")
        else:
            st.info("Upload a document and click 'Extract Data' to see the raw text.")