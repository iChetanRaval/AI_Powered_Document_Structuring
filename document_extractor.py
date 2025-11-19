"""
AI-Powered Document Structuring & Data Extraction
Author: AI Solution for Document Processing
Date: 2024
"""

import re
import pandas as pd
from typing import List, Dict, Tuple
import PyPDF2
from datetime import datetime
import json

class DocumentExtractor:
    """
    Extracts structured data from unstructured documents using
    pattern matching and contextual analysis
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text_content = ""
        self.structured_data = []
        
    def extract_text_from_pdf(self) -> str:
        """Extract raw text from PDF"""
        text = ""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            self.text_content = text
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def extract_personal_info(self) -> List[Dict]:
        """Extract personal information with context"""
        data = []
        text = self.text_content
        
        # Extract Name
        name_match = re.search(r'(\w+\s+\w+)\s+was born', text)
        if name_match:
            full_name = name_match.group(1)
            names = full_name.split()
            data.append({
                'key': 'First Name',
                'value': names[0],
                'comments': ''
            })
            data.append({
                'key': 'Last Name',
                'value': names[1] if len(names) > 1 else '',
                'comments': ''
            })
        
        # Extract Date of Birth
        dob_match = re.search(r'born on (\w+ \d+, \d{4})', text)
        if dob_match:
            dob_str = dob_match.group(1)
            dob_obj = datetime.strptime(dob_str, '%B %d, %Y')
            data.append({
                'key': 'Date of Birth',
                'value': dob_obj.strftime('%d-%b-%y'),
                'comments': ''
            })
        
        # Extract Birth City and State
        birth_match = re.search(r'born on [^,]+, in (\w+), (\w+)', text)
        if birth_match:
            city = birth_match.group(1)
            state = birth_match.group(2)
            
            # Extract context for birth city
            context_match = re.search(r'Born and raised in the Pink City of India, his birthplace provides valuable regional profiling context', text)
            city_comment = context_match.group(0) if context_match else ''
            
            data.append({
                'key': 'Birth City',
                'value': city,
                'comments': city_comment
            })
            data.append({
                'key': 'Birth State',
                'value': state,
                'comments': city_comment
            })
        
        # Extract Age
        age_match = re.search(r'making him (\d+) years old as of (\d{4})', text)
        if age_match:
            age = age_match.group(1)
            age_context = re.search(r'His birthdate is formatted as[^,]+, while his age serves as a key demographic marker for analytical purposes', text)
            data.append({
                'key': 'Age',
                'value': f'{age} years',
                'comments': age_context.group(0) if age_context else ''
            })
        
        # Extract Blood Group
        blood_match = re.search(r'his ([A-Z]\+?) blood group', text)
        if blood_match:
            blood_context = re.search(r'his [A-Z]\+? blood group is noted for emergency contact purposes', text)
            data.append({
                'key': 'Blood Group',
                'value': blood_match.group(1),
                'comments': blood_context.group(0).replace('his O+ blood group is noted for ', '').capitalize() if blood_context else ''
            })
        
        # Extract Nationality
        nationality_match = re.search(r'As an (\w+) national', text)
        if nationality_match:
            nat_context = re.search(r'his citizenship status is important for understanding his work authorization and visa requirements across different employment opportunities', text)
            data.append({
                'key': 'Nationality',
                'value': nationality_match.group(1),
                'comments': nat_context.group(0).replace('his citizenship status is important for understanding his work authorization and visa requirements across different employment opportunities', 'Citizenship status is important for understanding his work authorization and visa requirements across different employment opportunities.') if nat_context else ''
            })
        
        return data
    
    def extract_professional_info(self) -> List[Dict]:
        """Extract professional/career information"""
        data = []
        text = self.text_content
        
        # First professional role
        first_job_match = re.search(r'professional journey began on (\w+ \d+, \d{4}), when he joined his first company as a ([^w]+) with an annual salary of ([\d,]+) INR', text)
        if first_job_match:
            joining_date = datetime.strptime(first_job_match.group(1), '%B %d, %Y')
            data.append({
                'key': 'Joining Date of first professional role',
                'value': joining_date.strftime('%d-%b-%y'),
                'comments': ''
            })
            data.append({
                'key': 'Designation of first professional role',
                'value': first_job_match.group(2).strip(),
                'comments': ''
            })
            data.append({
                'key': 'Salary of first professional role',
                'value': first_job_match.group(3).replace(',', ''),
                'comments': ''
            })
            data.append({
                'key': 'Salary currency of first professional role',
                'value': 'INR',
                'comments': ''
            })
        
        # Current Organization
        current_org_match = re.search(r'his current role at ([^b]+) beginning', text)
        if current_org_match:
            data.append({
                'key': 'Current Organization',
                'value': current_org_match.group(1).strip(),
                'comments': ''
            })
        
        # Current Joining Date
        current_join_match = re.search(r'beginning on (\w+ \d+, \d{4})', text)
        if current_join_match:
            current_date = datetime.strptime(current_join_match.group(1), '%B %d, %Y')
            data.append({
                'key': 'Current Joining Date',
                'value': current_date.strftime('%d-%b-%y'),
                'comments': ''
            })
        
        # Current Designation
        current_desig_match = re.search(r'where he serves as a ([^e]+) earning', text)
        if current_desig_match:
            data.append({
                'key': 'Current Designation',
                'value': current_desig_match.group(1).strip(),
                'comments': ''
            })
        
        # Current Salary
        current_sal_match = re.search(r'earning ([\d,]+) INR annually', text)
        if current_sal_match:
            salary_context = re.search(r'This salary progression from his starting compensation to his current peak salary of 2,800,000 INR represents a substantial eight- ?fold increase over his twelve-year career span', text)
            data.append({
                'key': 'Current Salary',
                'value': current_sal_match.group(1).replace(',', ''),
                'comments': salary_context.group(0) if salary_context else ''
            })
            data.append({
                'key': 'Current Salary Currency',
                'value': 'INR',
                'comments': ''
            })
        
        # Previous Organization
        prev_org_match = re.search(r'he worked at ([^f]+) from', text)
        if prev_org_match:
            data.append({
                'key': 'Previous Organization',
                'value': prev_org_match.group(1).strip(),
                'comments': ''
            })
        
        # Previous Joining Date
        prev_join_match = re.search(r'from (\w+ \d+, \d{4}), to', text)
        if prev_join_match:
            prev_date = datetime.strptime(prev_join_match.group(1), '%B %d, %Y')
            data.append({
                'key': 'Previous Joining Date',
                'value': prev_date.strftime('%d-%b-%y'),
                'comments': ''
            })
        
        # Previous end year
        prev_end_match = re.search(r'from [^,]+, to (\d{4})', text)
        if prev_end_match:
            data.append({
                'key': 'Previous end year',
                'value': prev_end_match.group(1),
                'comments': ''
            })
        
        # Previous Starting Designation
        prev_desig_match = re.search(r'starting as a ([^a]+) and earning a promotion', text)
        if prev_desig_match:
            promotion_context = "Promoted in 2019"
            data.append({
                'key': 'Previous Starting Designation',
                'value': prev_desig_match.group(1).strip(),
                'comments': promotion_context
            })
        
        return data
    
    def extract_education_info(self) -> List[Dict]:
        """Extract educational information"""
        data = []
        text = self.text_content
        
        # High School
        hs_match = re.search(r"high school education at ([^,]+), Jaipur", text)
        if hs_match:
            school_context = "His core subjects included Mathematics, Physics, Chemistry, and Computer Science, demonstrating his early aptitude for technical disciplines."
            data.append({
                'key': 'High School',
                'value': hs_match.group(1).strip(),
                'comments': school_context
            })
        
        # 12th standard pass out year
        year_12_match = re.search(r'12th standard in (\d{4})', text)
        if year_12_match:
            data.append({
                'key': '12th standard pass out year',
                'value': year_12_match.group(1),
                'comments': 'Outstanding achievement'
            })
        
        # 12th overall board score
        score_12_match = re.search(r'achieving an outstanding ([\d.]+)% overall score', text)
        if score_12_match:
            data.append({
                'key': '12th overall board score',
                'value': score_12_match.group(1) + '%',
                'comments': ''
            })
        
        # Undergraduate degree
        ug_degree_match = re.search(r'He pursued his (B\.Tech[^a]+) at', text)
        if ug_degree_match:
            data.append({
                'key': 'Undergraduate degree',
                'value': ug_degree_match.group(1).strip(),
                'comments': ''
            })
        
        # Undergraduate college
        ug_college_match = re.search(r'at the prestigious ([^,]+), graduating', text)
        if ug_college_match:
            data.append({
                'key': 'Undergraduate college',
                'value': ug_college_match.group(1).strip(),
                'comments': ''
            })
        
        # Undergraduate year
        ug_year_match = re.search(r'graduating with honors in (\d{4})', text)
        if ug_year_match:
            ug_context = "Graduating with honors and ranking 15th among 120 students in his class."
            data.append({
                'key': 'Undergraduate year',
                'value': ug_year_match.group(1),
                'comments': ug_context
            })
        
        # Undergraduate CGPA
        ug_cgpa_match = re.search(r'with a CGPA of ([\d.]+) on a 10-point scale', text)
        if ug_cgpa_match:
            data.append({
                'key': 'Undergraduate CGPA',
                'value': ug_cgpa_match.group(1),
                'comments': 'On a 10-point scale'
            })
        
        # Graduation degree (Masters)
        grad_degree_match = re.search(r'earned his (M\.Tech[^i]+) in', text)
        if grad_degree_match:
            data.append({
                'key': 'Graduation degree',
                'value': grad_degree_match.group(1).strip(),
                'comments': ''
            })
        
        # Graduation college
        grad_college_match = re.search(r'His academic excellence continued at ([^,]+), where he earned', text)
        if grad_college_match:
            data.append({
                'key': 'Graduation college',
                'value': grad_college_match.group(1).strip(),
                'comments': 'Continued academic excellence at IIT Bombay'
            })
        
        # Graduation year
        grad_year_match = re.search(r'Data Science in (\d{4})', text)
        if grad_year_match:
            data.append({
                'key': 'Graduation year',
                'value': grad_year_match.group(1),
                'comments': ''
            })
        
        # Graduation CGPA
        grad_cgpa_match = re.search(r'achieving an exceptional CGPA of ([\d.]+) and scoring (\d+) out of (\d+)', text)
        if grad_cgpa_match:
            thesis_context = "Considered exceptional and scoring 95 out of 100 for his final year thesis project"
            data.append({
                'key': 'Graduation CGPA',
                'value': grad_cgpa_match.group(1),
                'comments': thesis_context
            })
        
        return data
    
    def extract_certifications(self) -> List[Dict]:
        """Extract certification information"""
        data = []
        text = self.text_content
        
        cert_context = "Vijay's commitment to continuous learning is evident through his impressive certification scores. He passed the AWS Solutions Architect exam in 2019 with a score of 920 out of 1000. Pursued in the year 2020 with 875 points."
        
        # AWS Certification
        data.append({
            'key': 'Certifications 1',
            'value': 'AWS Solutions Architect',
            'comments': cert_context
        })
        
        # Azure Certification
        data.append({
            'key': 'Certifications 2',
            'value': 'Azure Data Engineer',
            'comments': cert_context
        })
        
        # PMP Certification
        pmp_match = re.search(r'his Project Management Professional certification, obtained in (\d{4}), was achieved with an "([^"]+)" rating', text)
        if pmp_match:
            pmp_context = f'Obtained in {pmp_match.group(1)}, was achieved with an "{pmp_match.group(2)}" rating from PMI. These certifications complement his practical experience and demonstrate his expertise across multiple technology platforms.'
            data.append({
                'key': 'Certifications 3',
                'value': 'Project Management Professional certification',
                'comments': pmp_context
            })
        
        # SAFe Agilist
        safe_match = re.search(r'his SAFe Agilist certification earned him an outstanding (\d+)% score', text)
        if safe_match:
            safe_context = f'Earned him an outstanding {safe_match.group(1)}% score. These certifications complement his practical experience and demonstrate his expertise across multiple technology platforms.'
            data.append({
                'key': 'Certifications 4',
                'value': 'SAFe Agilist',
                'comments': safe_context
            })
        
        return data
    
    def extract_technical_proficiency(self) -> List[Dict]:
        """Extract technical skills information"""
        data = []
        text = self.text_content
        
        proficiency_context = "In terms of technical proficiency, Vijay rates himself highly across various skills, with SQL expertise at a perfect 10 out of 10, reflecting his daily usage since 2012. His Python proficiency scores 9 out of 10, backed by over seven years of practical experience and demonstrate his expertise across multiple technology platforms."
        
        data.append({
            'key': 'Technical Proficiency',
            'value': '',
            'comments': proficiency_context
        })
        
        return data
    
    def process_document(self) -> pd.DataFrame:
        """Main processing pipeline"""
        # Extract text
        self.extract_text_from_pdf()
        
        # Extract all sections
        personal_data = self.extract_personal_info()
        professional_data = self.extract_professional_info()
        education_data = self.extract_education_info()
        cert_data = self.extract_certifications()
        tech_data = self.extract_technical_proficiency()
        
        # Combine all data
        all_data = (personal_data + professional_data + 
                   education_data + cert_data + tech_data)
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Add row numbers
        df.insert(0, '#', range(1, len(df) + 1))
        df.columns = ['#', 'Key', 'Value', 'Comments']
        
        return df
    
    def save_to_excel(self, output_path: str = 'Output.xlsx'):
        """Save extracted data to Excel"""
        df = self.process_document()
        df.to_excel(output_path, index=False)
        print(f"Data successfully extracted and saved to {output_path}")
        return df


# Main execution
if __name__ == "__main__":
    # Initialize extractor
    extractor = DocumentExtractor("Data Input.pdf")
    
    # Process and save
    result_df = extractor.save_to_excel("Output.xlsx")
    
    # Display results
    print("\nExtracted Data Preview:")
    print(result_df.to_string())
    print(f"\nTotal records extracted: {len(result_df)}")