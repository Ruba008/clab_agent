import chromadb
from chromadb.api import ClientAPI
from typing import Literal, overload, Optional

# Taking the client
client = chromadb.HttpClient(host="localhost", port=8000)
    
@overload
def connect_collection(session_id: None ,collection_type: Literal["scrapy"]):
    ...
        
@overload
def connect_collection(session_id: str, collection_type: Literal["context"]):
    ...

def connect_collection(session_id: Optional[str], collection_type: Literal["context", "scrapy"]):
    """
    Connect to collections scrapy like and context like
    """
    
    global collection
    
    try: 
        if collection_type == "context": collection = client.get_or_create_collection(name=f"clab{session_id}")
        else: collection = client.get_or_create_collection(name="clab_web")
        print(f"Collection {collection.name} connected.\n")
    except Exception as e:
        print(f"Impossible to connect in the collection.\nError: {e}\n")
        
def query(input_txt: list[str]):
    """
    Used to realise consulting by semantic comparation
    """
    
    result = collection.query(
        query_texts=input_txt,
        include=["documents"],
        n_results=3
    )
    
    return result

@overload
def add_context(session_id: None, user_input: None, url: str, response: str, collection_type: Literal["scrapy"]):
    ...

@overload
def add_context(session_id: str, user_input: str, url: None, response: str, collection_type: Literal["context"]):
    ...

def add_context(session_id: Optional[str],
                user_input: Optional[str], 
                url: Optional[str], 
                response: str, 
                collection_type: Literal["context", "scrapy"]
                ):
    
    collection = client.get_or_create_collection(name=f"clab{session_id}") if collection_type == "context" else client.get_or_create_collection(name="clab_web")
    
    try:    
        if (collection_type == "context"):
            collection.add(
                documents=[response],
                metadatas=[{"user_input": user_input}],
                ids=[f"{session_id}-{user_input}"]
            )
        else:
            collection.add(
                documents=[response],
                metadatas=[{"url": url}],
                ids=[f"{collection_type}-{url}"]
            )
        print(f"Context added sucessfully in {collection.name} collection.\n")
        
    except Exception as e:
        print(f"Impossible to add the context in the collection.\nError: {e}\n")


def delete_collection(session_id: Optional[str], collection_type: Literal["scrapy", "context"]):
    collection = client.get_or_create_collection(name=f"clab{session_id}") if collection_type == "context" else client.get_or_create_collection(name="clab_web")
    
    try:    
        if collection_type == "context": client.delete_collection(name=f"clab{session_id}")
        else: client.delete_collection(name="clab_web")
        print(f"Collection {collection.name} deleted sucessfully.\n")
    except Exception as e:
        print(f"Impossible to delete the collection.\nError: {e}\n")
    