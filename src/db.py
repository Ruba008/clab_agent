import chromadb
from chromadb.api import ClientAPI

client = chromadb.HttpClient(host="localhost", port=8000)

def create_session(id: str):
    global collection
    collection = client.create_collection(name=f"clab{id}")
    print(f"Collection {collection.name} created.")
    
def query_context(session_id: str, user_input: str):
    context = collection.query(
        query_texts=[user_input],
        include=["documents", "metadatas"],
        n_results=10
    )
    
    return context['documents'][0] if context['documents'] else None
    
def add_context(session_id: str, user_input: str, response: str):
    collection.add(
        documents=[response],
        metadatas=[{"user_input": user_input}],
        ids=[f"{session_id}-{user_input}"]
    )
    
    