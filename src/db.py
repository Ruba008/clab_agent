import chromadb
from chromadb.api import ClientAPI
from typing import Literal, overload, Optional

client = chromadb.HttpClient(host="localhost", port=8000)
    
@overload
def connect_collection(session_id: None ,collection_type: Literal["scrapy"]):
    ...
        
@overload
def connect_collection(session_id: str, collection_type: Literal["context"]):
    ...

def connect_collection(session_id: Optional[str], collection_type: Literal["context", "scrapy"]):
    global collection
    
    try: 
        if collection_type == "context": collection = client.get_or_create_collection(name=f"clab{session_id}")
        else: collection = client.get_or_create_collection(name="clab_web")
        print(f"Collection {collection.name} connected.\n")
    except Exception as e:
        print(f"Impossible to connect in the collection.\nError: {e}\n")
        
def query_context(user_input: str):
    context = collection.query(
        query_texts=[user_input],
        include=["documents", "metadatas"],
        n_results=10
    )
    
    return context['documents'][0] if context['documents'] else None
    
def add_context(session_id: str, user_input: str, response: str):
    try:    
        collection.add(
            documents=[response],
            metadatas=[{"user_input": user_input}],
            ids=[f"{session_id}-{user_input}"]
        )
        print(f"Context added sucessfully in {collection.name} collection.\n")
    except Exception as e:
        print(f"Impossible to add the context in the collection.\nError: {e}\n")

def delete_collection(session_id: Optional[str], collection_type: Literal["scrapy", "context"]):
    try:    
        if collection_type == "context": client.delete_collection(name=f"clab{session_id}")
        else: client.delete_collection(name="clab_web")
        print(f"Collection {collection.name} deleted sucessfully.\n")
    except Exception as e:
        print(f"Impossible to delete the collection.\nError: {e}\n")
    