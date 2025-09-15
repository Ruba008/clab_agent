import chromadb, logging
from typing import List
from chromadb.api import ClientAPI
from typing import Literal, overload, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma

# =============================================================================
# CHROMADB CONFIGURATION
# =============================================================================


# Embbeded client initialisation
client = chromadb.PersistentClient(path="./chroma_embedded")
print("✅ ChromaDB started.")
        
def query_context(input_txt: List[str], session_id: str):
    """
    Used to realise consulting by semantic comparation
    """
    
    try:
        
        # Capturing collection (it must be created)
        collection = client.get_or_create_collection(name="clab" + session_id)
        
        # Embbeding Consulting from input_text 
        result = collection.query(
            query_texts=input_txt,
            include=["documents"],
            n_results=10 # it will take 10 documents (ContainerLab pages)
        )
        
        return result
        
    except Exception as e:
        print(f"Impossible to query the scrapy. Error: {e}")
        
def query_scrapy(input_txt: List[str]):
    """
    Used to realise consulting by semantic comparation
    """
    
    try:
        
        # Capturing collection (it must be created)
        collection = client.get_collection(name="clab_web")
        
        # Embbeding Consulting from input_text 
        result = collection.query(
            query_texts=input_txt,
            include=["documents"],
            n_results=10 # it will take 10 documents (ContainerLab pages)
        )
        
        return result
        
    except Exception as e:
        print(f"Impossible to query the scrapy. Error: {e}")
    
def add_scrapy(document: List[Document], embeddings: HuggingFaceEmbeddings, ids: List[str]):
   
    """
    Used to add a scrapy of Containerlab Documentation
    """
   
    try:
        client.delete_collection(name="clab_web")
        print("Existing clab_web collection deleted")
    except Exception as e:
        print(f"Collection clab_web didn't exist or couldn't be deleted: {e}")
    
    try:
        collection = client.create_collection(name="clab_web")
        
        # Storing the 
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
        if collection_type == "context": 
            client.delete_collection(name=f"clab{session_id}")
        else: 
            client.delete_collection(name="clab_web")
        print(f"Collection {collection.name} deleted sucessfully.\n")
    except Exception as e:
        print(f"Impossible to delete the collection.\nError: {e}\n")