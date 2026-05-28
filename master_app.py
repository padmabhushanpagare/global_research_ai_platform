import streamlit as st
import requests

st.set_page_config(page_title="Global Research AI", page_icon="🏦", layout="wide")

# --- 1. INITIALIZE SESSION STATE MEMORY ---
# This ensures our variables exist and survive tab switches
if "engine_a_data" not in st.session_state:
    st.session_state.engine_a_data = None
if "engine_b_message" not in st.session_state:
    st.session_state.engine_b_message = None
if "engine_b_report" not in st.session_state:
    st.session_state.engine_b_report = None

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
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post("http://127.0.0.1:8000/api/rag-extract", files=files)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    # Save to session state instead of just a local variable
                    st.session_state.engine_a_data = data.get("extracted_data", {})
                else:
                    st.error(f"⚠️ Extraction Failed: {data.get('detail', 'Unknown backend error.')}")
            else:
                st.error(f"API HTTP Error: {response.status_code}")

    # Display Engine A results if they exist in memory, regardless of when they were run
    if st.session_state.engine_a_data:
        st.success("Extraction successful.")
        st.json(st.session_state.engine_a_data)


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
                    # Save both the success message and the report to session state
                    st.session_state.engine_b_message = "✅ " + data["message"]
                    st.session_state.engine_b_report = data.get("report", "")
                else:
                    st.error("API Connection Failed.")

    # Display Engine B results if they exist in memory, regardless of when they were run
    if st.session_state.engine_b_report:
        st.success(st.session_state.engine_b_message)
        st.markdown("---")
        st.markdown(st.session_state.engine_b_report)