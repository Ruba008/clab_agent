import chromadb
from chromadb.api import ClientAPI

client = chromadb.HttpClient(host="localhost", port=8000)

def create_session(id: str):
    collection = client.create_collection(name=f"clab{id}")
    print(f"Collection {collection.name} created.")
    