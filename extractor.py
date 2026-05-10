from google import genai
from google.genai import types
import os
import json
import base64
import pdfplumber
import re
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={'api_version': 'v1'}
)

def read_pdf_text(pdf_path):
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text(layout=True) + "\n"
        return text.strip()
    except Exception as e:
        print(f"pdfplumber error: {e}")
        return None

def extract_from_text(pdf_path):
    text = read_pdf_text(pdf_path)
    if not text or len(text.strip()) < 50:
        return None  # Fallback to Gemini if no text
        
    name_match = re.search(r"Name\s*:\s*([A-Z\s]+)", text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else "UNKNOWN_NAME"
    
    prn_match = re.search(r"University PRN\s*:\s*(\d+)", text)
    prn = prn_match.group(1).strip() if prn_match else "UNKNOWN_PRN"

    main_sem = "UNKNOWN_SEM"
    subject_search_text = text
    main_sem_match = re.search(r"Statement of Marks.*?Semester\s*:?\s*(\d+)", text, re.IGNORECASE | re.DOTALL)
    if main_sem_match:
        main_sem = main_sem_match.group(1)
        section_pattern = r"(?:Part\s+\d+\s+Semester\s+" + main_sem + r"|Semester\s+" + main_sem + r")"
        matches = list(re.finditer(section_pattern, text, re.IGNORECASE))
        if matches:
            start_idx = matches[-1].end()
            end_match = re.search(r"Sem\s*-\s*" + main_sem + r"\s*Result", text[start_idx:], re.IGNORECASE)
            end_idx = start_idx + end_match.start() if end_match else len(text)
            subject_search_text = text[start_idx:end_idx]

    dept_match = re.search(r"Branch\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    dept = dept_match.group(1).strip() if dept_match else "UNKNOWN_DEPT"

    subject_block_pattern = re.compile(
        r'(\d{5})[",\s]+(.*?)(?=\s*(?:CIE|TW|ESEx|PR|Sem|9\d{4})|\Z)', 
        re.DOTALL
    )
    
    # Matches Category, Max Marks, Obtained Marks, Status
    mark_status_pattern = re.compile(r'(CIE|TW|ESEx|PR)\s*\((\d+)\)\s*([\d$]+)\s*([A-Za-z$-]+|---)')
    
    blocks = list(subject_block_pattern.finditer(subject_search_text))
    
    subjects = []
    total_obtained = 0
    total_out_of = 0
    
    for i, block_match in enumerate(blocks):
        subject_name = block_match.group(2).strip().replace('"', '').replace(',', '').replace('\n', ' ')
        
        start_pos = block_match.end()
        end_pos = blocks[i+1].start() if i+1 < len(blocks) else len(subject_search_text)
        mark_block = subject_search_text[start_pos:end_pos]
        
        if "Paper / Subject Name" in subject_name or not subject_name: 
            continue
            
        for mark_match in mark_status_pattern.finditer(mark_block):
            category = mark_match.group(1).strip()
            max_mark_val = mark_match.group(2).strip()
            mark_val = mark_match.group(3).strip().replace('$', '')
            status_val = mark_match.group(4).strip().replace('$', '')
            
            score = 0
            if mark_val.isdigit():
                score = int(mark_val)
                total_obtained += score
                
            if max_mark_val.isdigit():
                total_out_of += int(max_mark_val)
                
            subjects.append({
                "name": subject_name,
                "category": category,
                "score": score,
                "status": status_val
            })
            
    if not subjects:
        return None # Failed to extract subjects, fallback to Gemini
        
    return {
        "metadata": {
            "name": name,
            "prn": prn,
            "dept": dept,
            "sem": main_sem
        },
        "subjects": subjects,
        "summary": {
            "total_obtained": total_obtained,
            "out_of": total_out_of,
            "percentage": round((total_obtained / total_out_of) * 100, 2) if total_out_of > 0 else 0.0
        }
    }

def extract_result_data(pdf_path):
    """
    Attempts to extract data using fast regex on text PDFs.
    Falls back to Gemini 1.5 Flash for image-based PDFs or if regex fails.
    """
    print(f"Attempting text extraction for {pdf_path}...")
    text_data = extract_from_text(pdf_path)
    
    if text_data:
        print("Success: Data extracted via text parsing.")
        return text_data
        
    print("Text extraction failed or incomplete. Falling back to Gemini extraction...")
    
    # Read the PDF file and prepare it for the API
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    prompt = """
    Analyze this university result sheet (it may be a scan or image). 
    Extract all student information accurately.
    1. Identify: Full Name, PRN, Department (e.g. CSE, Mechanical), and Semester.
    2. Extract all subjects in a list. For each subject include: 
       - Subject Name
       - Category (CIE, ESE, TW, or PR)
       - Obtained Marks
       - Status (PASS or FAIL)
    3. Extract the Grand Total and the 'Out Of' marks.

    Return the data ONLY as a valid JSON object with this exact structure:
    {
      "metadata": {"name": "", "prn": "", "dept": "", "sem": ""},
      "subjects": [{"name": "", "category": "", "score": 0, "status": ""}],
      "summary": {"total_obtained": 0, "out_of": 0, "percentage": 0.0}
    }
    """

    try:
        print(f"Sending request to Gemini (v2.0.0 SDK) for {os.path.basename(pdf_path)}...")
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[
                types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                prompt
            ]
        )
        # Strip potential markdown formatting from Gemini response
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"Extraction Error (Gemini): {e}")
        return None