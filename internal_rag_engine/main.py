import os
import glob
import shutil
import sys

# Import Configuration & Logging
from config import logger, MODEL_NAME, INPUT_DIR

# Import Database operations
from database import init_db, insert_financial_data

# Import Modules and Error Classes
from internal_rag_engine.extractor import process_document_to_chunks
from internal_rag_engine.retriever import build_vector_store
from internal_rag_engine.analyzer import analyze_financial_text, clean_and_parse_json
from internal_rag_engine.reporter import build_html_report
from internal_rag_engine.broadcaster import generate_briefing_script, create_audio_briefing
from internal_rag_engine.schema import ExtractionError, AnalysisError

# Create an archive directory for completed files
ARCHIVE_DIR = "archive"
os.makedirs(ARCHIVE_DIR, exist_ok=True)

def process_single_document(file_path):
    """Handles the complete RAG pipeline for a single file."""
    filename = os.path.basename(file_path)
    logger.info(f"--- Starting Enterprise RAG processing for: {filename} ---")
    
    # Phase 1: Universal Extraction & Chunking
    chunks = process_document_to_chunks(file_path)
    if not chunks:
        raise ExtractionError(f"Could not extract or chunk text from document.")
    
    # Phase 2: Vector Embedding
    success = build_vector_store(chunks, document_name=filename)
    if not success:
        raise ExtractionError("Failed to build vector embeddings for document.")
    
    # Phase 3: AI Analysis (RAG) & Validation
    logger.info(f"Offloading targeted context to local LLM ({MODEL_NAME})...")
    
    # Notice we now just pass the filename, so the analyzer can search the DB!
    raw_llm_json = analyze_financial_text(filename, model_name=MODEL_NAME)
    
    logger.info("Applying defensive sanitization and Pydantic validation...")
    clean_python_dictionary = clean_and_parse_json(raw_llm_json)
    
    # Phase 4: Storage
    logger.info("Persisting validated metrics to SQLite database...")
    insert_financial_data(clean_python_dictionary)
    
    # Phase 5: Reporting
    logger.info("Compiling dynamic HTML report views...")
    build_html_report(clean_python_dictionary)
    
    # Phase 6: Broadcasting
    logger.info("Generating Executive Audio Briefing Script...")
    script_text = generate_briefing_script(clean_python_dictionary, model_name=MODEL_NAME)
    if script_text:
        audio_filename = f"{clean_python_dictionary.get('ticker', 'UNKNOWN')}_Briefing.wav"
        logger.info("Synthesizing offline text-to-speech audio file...")
        create_audio_briefing(script_text, output_filename=audio_filename)
        
    logger.info(f"✅ Successfully completed processing for {filename}")

def main():
    logger.info("🚀 Starting Automated Batch Processing Pipeline...")
    init_db()
    
    # Grab all PDF files currently sitting in the inbox folder
    pdf_files = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in '{INPUT_DIR}/' directory. Waiting for new files...")
        return

    logger.info(f"Found {len(pdf_files)} documents in inbox. Starting batch job.")
    
    success_count = 0
    
    # Loop through each file one by one
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        try:
            process_single_document(pdf_path)
            
            # If successful, move the PDF to the archive folder
            shutil.move(pdf_path, os.path.join(ARCHIVE_DIR, filename))
            success_count += 1
            
        except ExtractionError as e:
            logger.error(f"Extraction Phase Failed for {filename}: {e}")
        except AnalysisError as e:
            logger.error(f"Analysis/Validation Phase Failed for {filename}: {e}")
        except Exception as pipeline_error:
            # Catches catastrophic errors but lets the loop continue to the next file!
            logger.critical(f"Unexpected error processing {filename}: {pipeline_error}", exc_info=True)
            
    logger.info(f"🏁 Batch job complete. Successfully processed {success_count}/{len(pdf_files)} documents.")

if __name__ == "__main__":
    main()