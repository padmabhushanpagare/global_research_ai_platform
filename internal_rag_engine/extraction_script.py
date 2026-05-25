import os
import json
from pypdf import PdfReader
import ollama

def extract_text_from_pdf(pdf_path):
    """Extracts raw text from a local PDF file."""
    if not os.path.exists(pdf_path):
        return f"Error: File not found at {pdf_path}"
    
    reader = PdfReader(pdf_path)
    text = ""
    # For a portfolio project, processing the first few pages 
    # (or the Executive Summary/Financial Highlights section) is ideal
    for page in reader.pages[:5]: 
        text += page.extract_text() + "\n"
    return text

def analyze_financial_text(text):
    """Sends text to local Ollama model and enforces a JSON response structure."""
    
    system_prompt = """
    You are an expert equity research analyst. Your task is to extract key financial metrics from the text.
    You must respond ONLY with a raw JSON object. Do not include markdown formatting blocks (like ```json).

    The JSON object must strictly follow this structure:
    {
        "ticker": "Stock symbol (e.g., TSLA)",
        "quarter": "Fiscal period (e.g., Q1 2026)",
        "revenue_billions": 0.0,
        "eps": 0.0,
        "guidance": "A summary of concrete future business targets (e.g., delivery numbers, factory expansions, or margin outlooks). DO NOT copy the legal Safe Harbor disclaimer or forward-looking statements boilerplate text.",
        "sentiment": "Bullish, Bearish, or Neutral",
        "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"]
    }
    """
    
    user_prompt = f"Extract the metrics from this financial text:\n\n{text}"
    
    try:
        # Calling your local Ollama instance
        response = ollama.chat(
            model='llama3', # Match this to the model you downloaded
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            options={
                'temperature': 0.1 # Low temperature ensures highly factual, consistent data extraction
            }
        )
        
        return response['message']['content']
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"
    
import re
import json

def clean_and_parse_json(raw_llm_output):
    """Sanitizes raw text from local LLMs into valid Python dictionaries."""
    # 1. Strip away any conversational prefixes/suffixes outside the curly braces
    json_match = re.search(r'\{.*\}', raw_llm_output, re.DOTALL)
    if not json_match:
        raise ValueError("No JSON block found in LLM output.")
    
    json_str = json_match.group(0)
    
    # 2. Fix the specific EPS syntax anomaly if it occurs
    # Converts: "eps": 0.15 (basic), 0.13 (diluted), -> "eps": 0.15
    if "(basic)" in json_str:
        json_str = re.sub(r'([0-9.]+)\s*\(basic\).*?,', r'\1,', json_str)
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse sanitized string: {json_str}")
        raise e

# --- Execution ---
if __name__ == "__main__":
    # 1. Place a sample financial PDF in your directory (e.g., an earnings transcript)
    # For testing, you can also just paste raw text into a sample variable
    pdf_filename = "tsla-20260331-gen.pdf" 
    
    print("Reading PDF...")
    raw_financial_text = extract_text_from_pdf(pdf_filename)
    
    print("Processing with local LLM via Ollama (this might take a few seconds)...")
    json_output = analyze_financial_text(raw_financial_text)
    
    print("\n--- Extracted Financial Structured Data ---")
    print(json_output)