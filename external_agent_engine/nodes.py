import os
import sqlite3
from datetime import datetime
import yfinance as yf
import ollama
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun
from external_agent_engine.graph_state import WorkflowState

# We will use your existing local model preference
MODEL_NAME = "llama3"

def researcher_node(state: WorkflowState) -> dict:
    """
    Worker 1: The Multi-Tool Researcher
    Goal: Scrape DDG for news AND yfinance for exact quantitative numbers.
    """
    print("⚙️ [SYSTEM] Researcher Node Activated...")
    objective = state.get("user_objective", "No objective provided.")
    
    # 1. Qualitative Search (News)
    print("🧠 [SYSTEM] Formulating optimal news query...")
    query_prompt = f"Convert this into a news search query (3-5 words). Objective: {objective}. Reply ONLY with the query."
    try:
        query_response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': query_prompt}])
        search_query = query_response['message']['content'].strip(' "\'')
    except:
        search_query = "MSFT latest news"
        
    print("🌐 [SYSTEM] Scraping live news articles...")
    search_tool = DuckDuckGoSearchRun()
    try:
        news_data = search_tool.invoke(search_query)
    except:
        news_data = "No news found."

    # 2. Quantitative Search (Hard Numbers)
    print("📈 [SYSTEM] Fetching exact market data via yfinance...")
    try:
        print("🔍 [SYSTEM] Dynamically extracting ticker symbol...")
        ticker_prompt = f"Extract the stock ticker symbol from this objective: '{objective}'. Reply ONLY with the 1-5 letter ticker symbol (e.g., AAPL, TSLA, MSFT). Do not include any other words, symbols, or punctuation."
        
        try:
            ticker_response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': ticker_prompt}])
            ticker_symbol = ticker_response['message']['content'].strip(' "\'\n').upper()
            
            # Defensive programming: If the LLM disobeys and writes a paragraph, fallback to the S&P 500
            if len(ticker_symbol) > 5 or " " in ticker_symbol:
                print(f"⚠️ [WARNING] LLM failed strict extraction. Defaulting to SPY. Raw output: {ticker_symbol}")
                ticker_symbol = "SPY"
        except Exception as e:
            print(f"⚠️ [WARNING] Ticker extraction failed: {e}")
            ticker_symbol = "SPY"
            
        print(f"🎯 [SYSTEM] Target acquired: {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol)
        
        # 1. The Bulletproof Method: Pull the last day's exact trading row
        hist = ticker.history(period="1d")
        
        if not hist.empty:
            # Grab the final closing price and volume from the dataframe
            current_price = round(hist['Close'].iloc[-1], 2)
            volume = int(hist['Volume'].iloc[-1])
        else:
            # 2. The Fallback: If history fails, try multiple info keys
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose', 'N/A')))
            volume = info.get('volume', info.get('regularMarketVolume', 'N/A'))

        market_data = f"{ticker_symbol} Current Price: ${current_price} | Trading Volume: {volume} shares"
    except Exception as e:
        market_data = f"Market data unavailable: {e}"

    # 3. Combine Data Streams into the LLM
    print("⏳ [SYSTEM] Compiling Multi-Source research...")
    prompt = f"""
    You are an expert financial researcher. Your objective is: {objective}.
    
    Here is the exact market data pulled from the stock exchange:
    <market_data>
    {market_data}
    </market_data>
    
    Here is the recent news scraped from the web:
    <news_data>
    {news_data}
    </news_data>
    
    Using ONLY the data above, gather key bullet points. 
    You MUST include the exact current stock price from the <market_data>.
    """
    
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{'role': 'user', 'content': prompt}]
        )
        structured_data = response['message']['content']
    except Exception as e:
        structured_data = f"Error during data structuring: {e}"

    current_workspace = state.get("workspace_data", {})
    current_workspace["raw_research"] = structured_data
    
    return {
        "workspace_data": current_workspace,
        "next_action": "draft_report"
    }

def writer_node(state: WorkflowState) -> dict:
    """
    Worker 2: The Writer
    Goal: Take the raw data from the workspace and write the final output.
    """
    print("⚙️ [SYSTEM] Writer Node Activated...")
    
    # Retrieve the data left behind by the Researcher Node
    raw_research = state.get("workspace_data", {}).get("raw_research", "")
    
    system_prompt = """
    You are an executive ghostwriter. Take the provided raw data and format it 
    into a polished, highly professional Executive Summary. Use markdown headers.
    """
    
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Raw Data:\n{raw_research}"}
            ]
        )
        final_draft = response['message']['content']
    except Exception as e:
        final_draft = f"Error during writing phase: {e}"

    # We append the final result to the message history and signal completion
    return {
        "messages": [AIMessage(content=final_draft)],
        "next_action": "review_draft" 
    }

def qa_node(state: WorkflowState) -> dict:
    """
    Worker 3: The Quality Assurance Reviewer
    Goal: Check the draft. If it's bad, send it back. If it's good, approve it.
    """
    print("⚙️ [SYSTEM] QA Reviewer Node Activated...")
    
    # Grab the draft the writer just created
    latest_draft = state["messages"][-1].content
    
    # We force the LLM to act as a strict editor
    system_prompt = """
    You are a strict Managing Editor. Review the provided draft. 
    It MUST contain 'Executive Summary' and use bullet points.
    If it is perfectly formatted, reply exactly with the word: APPROVED
    If it is missing things or poorly formatted, reply exactly with the word: REJECTED
    """
    
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': latest_draft}
            ],
            options={'temperature': 0.0} # Zero creativity allowed for the judge
        )
        decision = response['message']['content'].strip().upper()
    except Exception as e:
        decision = "APPROVED" # Fallback to prevent infinite error loops
        
    if "APPROVED" in decision:
        print("✅ [SYSTEM] Draft Approved by QA! Sending to Publisher...")
        return {"next_action": "publish"} 
    else:
        print("❌ [SYSTEM] Draft Rejected by QA! Sending back to Writer...")
        # If we reject it, we add a feedback message so the Writer knows what to fix
        feedback = HumanMessage(content="The Editor rejected this draft. Please rewrite it to be more professional and ensure you use markdown headers and bullet points.")
        return {
            "messages": [feedback], 
            "next_action": "draft_report" # Route it BACK to the writer!
        }
    
def publisher_node(state: WorkflowState) -> dict:
    """
    Worker 4: The Publisher
    Goal: Take the approved draft and physically save it to the local system.
    """
    print("⚙️ [SYSTEM] Publisher Node Activated...")
    
    # Grab the final approved draft
    final_draft = state["messages"][-1].content
    
    # Create a unique filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Executive_Report_{timestamp}.md"
    
    # Save it to the current directory
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_draft)
        print(f"📦 [SYSTEM] SUCCESS! Report securely published to: {filename}")
    except Exception as e:
        print(f"❌ [SYSTEM] Failed to publish report: {e}")
        
    # Route to the database archiver
    return {"next_action": "archive_data"} 
    
def database_node(state: WorkflowState) -> dict:
    """
    Worker 5: The Database Architect
    Goal: Archive the final report into a structured SQL database for future analysis.
    """
    print("⚙️ [SYSTEM] Database Node Activated...")
    
    final_draft = state["messages"][-1].content
    objective = state.get("user_objective", "Unknown Objective")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # 1. Connect to SQLite (This automatically creates the file if it doesn't exist)
        conn = sqlite3.connect("global_research_center.db")
        cursor = conn.cursor()
        
        # 2. Create the table structure if this is the first time running
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                objective TEXT,
                report_content TEXT
            )
        ''')
        
        # 3. Insert the new research report into the database
        cursor.execute('''
            INSERT INTO research_reports (timestamp, objective, report_content)
            VALUES (?, ?, ?)
        ''', (timestamp, objective, final_draft))
        
        # 4. Save and close
        conn.commit()
        conn.close()
        
        print("🗄️ [SYSTEM] SUCCESS! Report securely archived in SQL Database.")
    except Exception as e:
        print(f"❌ [SYSTEM] Database archiving failed: {e}")
        
    # Now the automation is truly finished
    return {"next_action": "end"}