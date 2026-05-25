import streamlit as st
import requests

st.set_page_config(page_title="Global Research AI", page_icon="🏦", layout="wide")

st.sidebar.title("🏦 Research Platform")
st.sidebar.markdown("Select an engine to begin workflow:")
engine_choice = st.sidebar.radio("Active Engine", ["Engine A: Historical RAG", "Engine B: Live Market Agent"])

st.title("Global Research AI Platform")

# --- UI FOR ENGINE A (RAG) ---
if engine_choice == "Engine A: Historical RAG":
    st.subheader("📄 Internal Document Deep-Dive")
    st.markdown("Upload corporate filings (10-K, 10-Q) for rigid quantitative extraction.")
    
    uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"])
    if st.button("Extract Metrics") and uploaded_file is not None:
        with st.spinner("Vectorizing document and extracting JSON..."):
            # Send to Master API
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post("http://127.0.0.1:8000/api/rag-extract", files=files)
            
            if response.status_code == 200:
                data = response.json()
                
                # 🔴 NEW: Check the internal API status flag
                if data.get("status") == "success":
                    st.success(data.get("message", "Extraction successful."))
                    st.json(data.get("extracted_data", {}))
                else:
                    # If the API caught an error, display it safely in a red box
                    st.error(f"⚠️ Extraction Failed: {data.get('detail', 'Unknown backend error.')}")
                    
            else:
                st.error(f"API HTTP Error: {response.status_code}")

# --- UI FOR ENGINE B (LangGraph) ---
elif engine_choice == "Engine B: Live Market Agent":
    st.subheader("🌐 Autonomous Market Synthesis")
    st.markdown("Trigger agentic workflow for live market data and sentiment.")
    
    objective = st.text_input("Research Objective:", placeholder="e.g., Analyze institutional sentiment for AAPL.")
    
    if st.button("🚀 Execute Pipeline"):
        if objective:
            with st.spinner("Agents are researching, drafting, reviewing, and archiving..."):
                payload = {"objective": objective}
                response = requests.post("http://127.0.0.1:8000/api/live-research", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ " + data["message"])
                    st.markdown("---")
                    st.markdown(data.get("report", ""))
                else:
                    st.error("API Connection Failed.")