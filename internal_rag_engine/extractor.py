import os
import re
import pymupdf4llm
from config import logger

def extract_pdf_text(pdf_path):
    """
    Upgraded: Extracts PDF as clean Markdown to preserve financial tables.
    This prevents columns from collapsing into unreadable text walls.
    """
    try:
        logger.info(f"Extracting Markdown structure from {os.path.basename(pdf_path)}...")
        # This single line reads the PDF and preserves all tables, headers, and lists as Markdown!
        md_text = pymupdf4llm.to_markdown(pdf_path)
        return md_text
    except Exception as e:
        logger.error(f"Failed to extract Markdown from PDF {pdf_path}: {e}")
        return None

def extract_transcript_text(txt_path):
    """Extracts text from a raw transcript file."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Failed to read Transcript {txt_path}: {e}")
        return None

def chunk_text(text, chunk_size=1500, overlap=300):
    """
    Splits massive text into manageable overlapping chunks.
    Chunk size increased to 1500 to safely accommodate Markdown table syntax.
    """
    # Clean up excessive newlines but preserve Markdown table structures
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
        
    return chunks

def process_document_to_chunks(file_path):
    """Universal handler: Takes any supported file and returns chunked text/markdown."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        logger.info(f"Detected PDF format. Engaging Markdown Table Extractor...")
        raw_text = extract_pdf_text(file_path)
    elif ext in ['.txt', '.vtt', '.srt']:
        logger.info(f"Detected Transcript format.")
        raw_text = extract_transcript_text(file_path)
    else:
        logger.error(f"Unsupported file type: {ext}")
        return None
        
    if not raw_text:
        return None
        
    logger.info("Chunking document into overlapping segments...")
    chunks = chunk_text(raw_text)
    logger.info(f"Successfully generated {len(chunks)} chunks.")
    
    return chunks