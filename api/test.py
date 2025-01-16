from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import fitz
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
import json

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
    summary: Dict[str, Any]
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

def get_completion(prompt: str) -> Dict[str, Any]:
    """Get completion from OpenAI API and parse into JSON."""
    try:
        # Add explicit JSON instructions in the system prompt
        system_prompt = """You are a precise loan analysis AI. 
        Generate a structured JSON response about the loan application. 
        Ensure the JSON is valid and contains detailed, professional insights.
        Your response will be parsed and used for critical financial decision-making."""

        completion = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Updated to latest model
            response_format={"type": "json_object"},  # Enforce JSON response
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=4000  # Increased token limit for comprehensive analysis
        )
        
        # Parse the JSON response
        response_text = completion.choices[0].message.content
        return json.loads(response_text)
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse OpenAI response into JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

def generate_loan_summary(extracted_text: str) -> Dict[str, Any]:
    """Generate a comprehensive loan summary as a structured JSON."""
    prompt = f"""Conduct a precise, professional loan application analysis based on the following document:

DOCUMENT CONTENT: {extracted_text}

ANALYSIS REQUIREMENTS:
1. Provide a comprehensive financial profile
2. Include precise numerical assessments
3. Offer a clear loan recommendation
4. Justify the recommendation with specific evidence

JSON STRUCTURE REQUIRED:
{{
    "analysis": {{
        "total_annual_income": "Exact income value",
        "income_sources": ["List of income streams"],
        "credit_score": "Numerical credit score",
        "debt_to_income_ratio": "Percentage calculation",
        "total_assets": "Total asset value",
        "financial_strengths": ["List of strengths"],
        "risk_factors": ["List of potential risks"]
    }},
    "recommendation": {{
        "decision": "APPROVE or DENY",
        "confidence_level": "HIGH/MEDIUM/LOW",
        "recommended_loan_amount": "Proposed loan amount",
        "suggested_terms": "Specific loan terms"
    }},
    "justification": {{
        "primary_reasons": ["Detailed reasons for decision"],
        "supporting_evidence": "Specific document details",
        "risk_mitigation_strategies": ["Strategies to address risks"]
    }}
}}

CRITICAL INSTRUCTIONS:
- Use actual values from the document
- Maintain professional and objective tone
- Ensure all statements are document-sourced
- Provide context for significant observations"""

    return get_completion(prompt)

@app.post("/api/loan-summary", response_model=LoanSummaryResponse)
async def analyze_loan_documents(files: List[UploadFile] = File(...)):
    """Endpoint to process loan application documents and return a structured summary."""
    try:
        # Extract text from uploaded PDFs
        extracted_text = extract_text_from_pdfs(files)
        
        # Generate loan summary based on extracted text
        loan_summary = generate_loan_summary(extracted_text)
        
        # Return the summary and document count in the response
        return LoanSummaryResponse(
            summary=loan_summary,
            document_count=len(files)
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing loan documents: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}