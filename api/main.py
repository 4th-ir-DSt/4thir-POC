from fastapi import FastAPI, UploadFile, File
from Agedetect import *
from HandDetector import *
from LoanAnalyzer import *
from Medicaldocanalyzer import *

app = FastAPI()

@app.post("/detect-age/")
async def detect_age_from_image(file: UploadFile = File(...)):
    # Read and convert the uploaded image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    image_array = np.array(image)
    
    # Detect age
    age = detect_age(image_array)
    
    if age is None:
        return {"error": "No face detected in the image"}
    
    return {"age": age}

@app.post("/detect-text/", response_model=DetectionResponse)
async def process_file(file: UploadFile = File(...)):
    """Process uploaded file (PDF or image) and return detected text with translation."""
    try:
        content = await file.read()
        file_extension = Path(file.filename).suffix.lower()
        
        german_text = ""
        detection_time = 0
        all_text_annotations = []

        if file_extension == '.pdf':
            # Handle PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(content)
                temp_pdf.flush()
                
                images = convert_pdf_to_images(temp_pdf.name)
                for image in images:
                    text, time_taken, annotations = await detect_text(image)
                    if text:
                        german_text += text + "\n"
                        if annotations:
                            all_text_annotations.extend(annotations)
                    detection_time += time_taken
                
                os.unlink(temp_pdf.name)
        else:
            # Handle image
            german_text, detection_time, all_text_annotations = await detect_text(content)

        if not german_text:
            raise HTTPException(status_code=400, detail="No text detected in the file")

        # Calculate confidence and translate text
        confidence_level = compute_overall_confidence(all_text_annotations)
        translated_text = await translate_text(german_text)

        return DetectionResponse(
            original_text=german_text,
            translated_text=translated_text,
            detection_time=round(detection_time, 1),
            confidence_level=round(confidence_level * 100, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/api/analyze-loan-documents/", response_model=LoanSummaryResponse)
async def analyze_loan_documents(files: List[UploadFile] = File(...)):
    """
    Endpoint to analyze loan documents and generate a summary.
    
    Parameters:
    - files: List of PDF files containing loan documents
    
    Returns:
    - JSON object containing the summary and number of processed documents
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
        
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Extract text from PDFs
    extracted_text = extract_text_from_pdfs(files)
    
    # Generate loan summary
    loan_summary = generate_loan_summary(extracted_text)
    
    return LoanSummaryResponse(
        summary=loan_summary,
        document_count=len(files)
    )
@app.post("/api/analyze-medical-documents/", response_model=AnalysisResponse)
async def analyze_medical_documents(files: List[UploadFile] = File(...)):
    """
    Endpoint to analyze medical documents and generate analysis.
    
    Parameters:
    - files: List of PDF files containing medical documents
    
    Returns:
    - JSON object containing the summary, template analysis, and number of processed documents
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
        
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Extract text from PDFs
    extracted_text = extract_text_from_pdfs(files)
    
    # Generate summary and template analysis
    summary = process_summary(extracted_text)
    template_analysis = process_template(extracted_text)
    
    return AnalysisResponse(
        summary=summary,
        template_analysis=template_analysis,
        document_count=len(files)
    )
