import os
import chromadb
from chromadb.utils import embedding_functions
from config import logger

# 1. Initialize persistent local storage for your vectors
# This creates a folder named 'vector_db' to save your embeddings forever
CHROMA_DATA_PATH = "vector_db"
os.makedirs(CHROMA_DATA_PATH, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# 2. Define the Embedding Model
# 'all-MiniLM-L6-v2' is open-source, runs locally, and is highly optimized for semantic search
try:
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
except Exception as e:
    logger.critical(f"Failed to load embedding model. Ensure sentence-transformers is installed. Error: {e}")
    raise e

# 3. Create or load the 'collection' (think of this as a database table)
collection = chroma_client.get_or_create_collection(
    name="financial_documents",
    embedding_function=sentence_transformer_ef
)

def build_vector_store(chunks, document_name):
    """Encodes text chunks into vectors and saves them to the local Chroma database."""
    if not chunks:
        logger.warning(f"No chunks provided for {document_name}. Skipping embedding.")
        return False

    logger.info(f"🧠 Embedding {len(chunks)} chunks for {document_name}...")
    
    # Generate unique IDs and metadata for each chunk so we can track their source
    ids = [f"{document_name}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": document_name, "chunk_index": i} for i in range(len(chunks))]
    
    try:
        # The .add() function automatically mathematically encodes the text and stores it!
        collection.upsert(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"✅ Successfully stored embeddings for {document_name} in Vector DB.")
        return True
    except Exception as e:
        logger.error(f"Failed to build vector store for {document_name}: {e}")
        return False

def retrieve_multi_query_context(document_name=None):
    """Executes targeted, independent semantic searches to guarantee metric extraction."""
    
    # 1. Targeted Sub-Queries (Notice the updated EPS string)
    queries = {
        "revenue": "total revenue quarterly revenue sales billions GAAP non-GAAP",
        "eps": "Consolidated Statements of Operations earnings per share diluted EPS GAAP EPS basic net income per share",
        "guidance": "future outlook guidance operational targets next year expectation",
        "quarter": "fiscal quarter Q1 Q2 Q3 Q4 period ended"
    }
    
    from config import logger
    
    logger.info("Executing Multi-Query Semantic Search...")
    unique_chunks = set() 
    
    try:
        where_filter = {"source": document_name} if document_name else None

        for metric, search_string in queries.items():
            results = collection.query(
                query_texts=[search_string],
                n_results=4, # 🔴 UPGRADE from 2 to 5 to catch adjacent tables
                where=where_filter
            )
            
            if results['documents'] and results['documents'][0]:
                for chunk in results['documents'][0]:
                    unique_chunks.add(chunk)
                    
        if not unique_chunks:
            logger.warning("No relevant context found across any sub-queries.")
            return ""
            
        context = "\n\n...[CONTINUED CONTEXT]...\n\n".join(list(unique_chunks))
        logger.info(f"✅ Multi-Query complete. Retrieved {len(unique_chunks)} highly targeted unique chunks.")
        
        return context
        
    except Exception as e:
        logger.error(f"Failed to execute Multi-Query retrieval: {e}")
        return ""
    
def retrieve_chat_context(query, document_name, n_results=4):
    """Retrieves context specifically for ad-hoc user chat questions."""
    logger.info(f"🔍 Ad-hoc chat search for: '{query}'")
    try:
        where_filter = {"source": document_name} if document_name else None
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        if results['documents'] and results['documents'][0]:
            return "\n\n---\n\n".join(results['documents'][0])
        return ""
    except Exception as e:
        logger.error(f"Chat retrieval failed: {e}")
        return ""