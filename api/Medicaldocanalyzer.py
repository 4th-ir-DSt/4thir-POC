from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import fitz
import os
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Medical Document Analyzer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_KEY")

class AnalysisResponse(BaseModel):
    summary: str
    template_analysis: str
    document_count: int

def initialize_llm():
    """Initialize OpenAI LLM with API key."""
    return OpenAI(api_key=OPENAI_API_KEY, temperature=0.3)

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
            raise HTTPException(
                status_code=400, 
                detail=f"Error processing PDF file {file.filename}: {str(e)}"
            )
        
        finally:
            file.file.seek(0)  # Reset file pointer
            
    return " ".join(extracted_texts)

def process_summary(extracted_text: str) -> str:
    """Generate a summary using Langchain and OpenAI."""
    try:
        prompt_template = """
        Summarize the following text in concise and clear language:
        {text}
        """
        prompt = PromptTemplate(input_variables=["text"], template=prompt_template)
        llm = initialize_llm()
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run(text=extracted_text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )

def process_template(extracted_text: str) -> str:
    """Generate a template analysis using Langchain and OpenAI."""
    try:
        prompt_template = """
        The first visit date was {first_visit_date} and the last visit date was {last_visit_date}. 
        Analyze the following text:
        {text}
        """
        # Placeholder dates - in a real application, you'd extract these from the documents
        first_visit_date = "placeholder for first visit date"
        last_visit_date = "placeholder for last visit date"
        
        prompt = PromptTemplate(
            input_variables=["first_visit_date", "last_visit_date", "text"],
            template=prompt_template
        )
        llm = initialize_llm()
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run(
            first_visit_date=first_visit_date,
            last_visit_date=last_visit_date,
            text=extracted_text
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating template analysis: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

