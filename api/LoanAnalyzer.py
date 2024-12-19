from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import fitz
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Loan Document Analyzer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

class LoanSummaryResponse(BaseModel):
    summary: str
    document_count: int

def extract_text_from_pdfs(files: List[UploadFile]) -> str:
    """Extract text from multiple PDF files."""
    extracted_texts = []
    
    for file in files:
        try:
            # Read the uploaded file content
            content = file.file.read()
            
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            
            # Extract text from each page
            text = ""
            for page in doc:
                text += page.get_text()
                
            extracted_texts.append(text)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing PDF file {file.filename}: {str(e)}")
        
        finally:
            file.file.seek(0)  # Reset file pointer
            
    return " ".join(extracted_texts)

def get_completion(prompt: str) -> str:
    """Get completion from OpenAI API."""
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a loan officer creating a concise, professional summary of loan application documents. Focus on key information and present it in a clear, structured format."
                },
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

def generate_loan_summary(extracted_text: str) -> str:
    """Generate a comprehensive but concise loan summary."""
    prompt = f"""
    Create a concise, professional summary (1-2 pages) of the following loan application. If the content is in English, generate the summary in English using the English structure. If the content is in German, generate the summary in German with the German structure provided below.

    English Structure:
    1. Applicant Overview
    - Full name and contact details
    - Employment status (brief description)
    - Key financial indicators (e.g., income, major assets)

    2. Loan Request
    - Requested loan amount
    - Purpose of the loan
    - Proposed loan terms (if specified)

    3. Documentation Verification
    - List of submitted documents
    - Highlight any missing critical documents
    - Confirm the validity of identity documents

    4. Financial Assessment
    - Monthly income
    - Debt-to-income ratio
    - Major assets and liabilities
    - Summary of credit score/history

    5. Risk Analysis
    - Strengths of the application
    - Potential concerns or risks
    - Mitigating factors, if any

    6. Recommendation
    - Clear recommendation (approval or denial)
    - If approved, suggest terms
    - If denied, outline key reasons

    German Structure:
    [Previous German structure remains the same...]

    Document content: {extracted_text}
    """
    return get_completion(prompt)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
