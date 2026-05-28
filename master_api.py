import asyncio
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import sys
import os
import shutil
from internal_rag_engine.extractor import process_document_to_chunks
from internal_rag_engine.retriever import build_vector_store
from internal_rag_engine.analyzer import analyze_financial_text, clean_and_parse_json

# Ensure Python can find our engine folders
sys.path.append(os.path.join(os.path.dirname(__file__), "external_agent_engine"))
sys.path.append(os.path.join(os.path.dirname(__file__), "internal_rag_engine"))

from external_agent_engine.graph import build_automation_graph

# --- EVENT-DRIVEN AUTOMATION ---

async def automated_morning_briefing():
    """The cron job that runs autonomously."""
    print("\n🌅 [SCHEDULER] Initiating automated morning briefings...")
    
    # The portfolio of assets we want to track automatically
    target_assets = ["TSLA", "NVDA"] 
    
    for ticker in target_assets:
        print(f"🤖 [SCHEDULER] Triggering Engine B for {ticker}...")
        objective = f"Analyze the latest news, institutional sentiment, and market data for {ticker}."
        
        try:
            # 1. Import the function instead of the variable
            from external_agent_engine.graph import build_automation_graph
            
            # 2. Call the function to compile the engine
            app = build_automation_graph()
            
            # 3. Run the agent in the background
            inputs = {"user_objective": objective, "workspace_data": {}}
            result = app.invoke(inputs) 
            
            print(f"✅ [SCHEDULER] {ticker} report compiled and archived.")
        except Exception as e:
            print(f"❌ [SCHEDULER] Failed to process {ticker}: {e}")
        
        # Pause for 5 seconds between assets to avoid rate-limiting the DuckDuckGo/yfinance APIs
        await asyncio.sleep(5) 
        
    print("🏁 [SCHEDULER] All morning briefings complete. Waiting for next cycle.\n")

# FastAPI Lifespan Manager (Starts the scheduler on boot)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⏱️ [SYSTEM] Booting Event-Driven Scheduler...")
    scheduler = AsyncIOScheduler()
    
    # ⚠️ FOR TESTING: Run every 2 minutes
    # (For Production: trigger='cron', hour=6, minute=0)
    scheduler.add_job(automated_morning_briefing, 'interval', minutes=30)
    
    scheduler.start()
    yield # The API runs while yielding
    
    print("🛑 [SYSTEM] Shutting down Scheduler...")
    scheduler.shutdown()

# --- APP INITIALIZATION ---
# Update your FastAPI app initialization to include the lifespan:
app = FastAPI(title="Global Research API", lifespan=lifespan)

# --- ENGINE B: LIVE MARKET AGENT ---
print("⚙️ [API] Booting up LangGraph Engine...")
automation_app = build_automation_graph()

class ResearchRequest(BaseModel):
    objective: str

@app.post("/api/live-research")
async def trigger_live_research(request: ResearchRequest):
    """Endpoint for LangGraph Market Synthesis"""
    initial_state = {
        "user_objective": request.objective,
        "messages": [],
        "workspace_data": {},
        "next_action": ""
    }
    try:
        final_state = automation_app.invoke(initial_state)
        return {
            "status": "success",
            "message": "Live research published and archived.",
            "report": final_state["messages"][-1].content
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# --- ENGINE A: INTERNAL RAG ---
@app.post("/api/rag-extract")
async def trigger_rag_extraction(file: UploadFile = File(...)):
    """Endpoint for Historical PDF Extraction"""
    
    # 1. Save the uploaded file temporarily so the PDF Extractor can read it
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"📄 [API] Processing uploaded document: {file.filename}")
        
        # 2. Extract Markdown and Chunk
        chunks = process_document_to_chunks(temp_file_path)
        if not chunks:
            return {"status": "error", "detail": "Failed to extract text from document."}
            
        # 3. Vectorize and save to ChromaDB
        build_vector_store(chunks, document_name=file.filename)
        
        # 4. Run the targeted RAG analysis
        print(f"🧠 [API] Running LLM Analysis on {file.filename}...")
        raw_llm_json = analyze_financial_text(document_name=file.filename)
        
        # 5. Clean and parse the output
        clean_data = clean_and_parse_json(raw_llm_json)
        
        return {
            "status": "success",
            "message": f"Successfully ingested and vectorized {file.filename}.",
            "extracted_data": clean_data # Pass the real data back to the UI!
        }
        
    except Exception as e:
        print(f"❌ [API] RAG Extraction Error: {e}")
        return {"status": "error", "detail": str(e)}
        
    finally:
        # 6. Always clean up the temporary file, even if an error occurs
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/")
def health_check():
    return {"status": "Global Research Master API is online."}