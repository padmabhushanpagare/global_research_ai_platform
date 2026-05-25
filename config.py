import os
import logging
from dotenv import load_dotenv

# 1. Load environment variables from the .env file
load_dotenv()

# 2. Assign environment variables to Python variables
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
INPUT_DIR = os.getenv("INPUT_DIR", "inbox")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outbox")
DB_PATH = os.getenv("DB_PATH", "financial_data.db")

# 3. Ensure necessary directories exist automatically
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 4. Configure Enterprise Logging
# 4. Configure Enterprise Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        # ADDED encoding='utf-8' HERE 👇
        logging.FileHandler(os.getenv("LOG_FILE", "pipeline.log"), encoding='utf-8'),
        logging.StreamHandler() 
    ]
)

# Create a logger object we can import into other files
logger = logging.getLogger("FinancePipeline")

# --- Quick Test ---
if __name__ == "__main__":
    logger.info("System configuration loaded successfully.")
    logger.info(f"Target LLM Engine: {MODEL_NAME}")
    logger.warning("This is a test warning message.")