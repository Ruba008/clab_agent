import chromadb
from typing import List
from chromadb.api import ClientAPI
from typing import Literal, overload, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma

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
        
def query(input_txt: List[str]):
    """
    Used to realise consulting by semantic comparation
    """
    
    result = collection.query(
        query_texts=input_txt,
        include=["documents"],
        n_results=10
    )
    
    return result


def add_scrapy(document: List[Document], embeddings: HuggingFaceEmbeddings, ids: List[str]):
   
    try:
        client.delete_collection(name="clab_web")
        print("Existing clab_web collection deleted")
    except Exception as e:
        print(f"Collection clab_web didn't exist or couldn't be deleted: {e}")
    
    
    try:
        collection = client.create_collection(name="clab_web")
        
        vectorstore = Chroma(
            client=client,
            collection_name="clab_web",
            embedding_function=embeddings,
            collection_metadata={"lang": "en-US", "type": "scrapy"}
        )
        
        vectorstore.add_documents(documents=document, ids=ids)
        print(f"Successfully added {len(document)} documents to clab_web collection")
       
        final_count = collection.count()
        print(f"Final collection count: {final_count}")
        
    except Exception as e:
        print(f"Problem to create and add scrapy in web collection\nError: {e}")
        raise 

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
    