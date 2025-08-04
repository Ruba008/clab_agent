from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import base64
import secrets
from typing import Dict, TypedDict, List
import chromadb
import logging
import db

class Step(TypedDict):
    task: int
    description: str
    group: List[str]

class Plan(TypedDict):
    step: List[Step]

class Orchestrator():
    session: str
    llm: OllamaLLM
    
    def __init__(self) -> None:

        """ID and collection creation"""
        
        self.session = base64.urlsafe_b64encode(secrets.token_bytes(16)).rstrip(b"=").decode("ascii")
        db.create_session(self.session)
        print("Session Initialized: " + str(self.session))
        
        self.llm = OllamaLLM(model="llama3.1")

    def create_planner(self, user_input: str):
        
        """Create planner for the user request"""
        
        with open(file="./nodes/instructions/orchestrator_system.txt") as file:
            instruction = file.read()
            prompt = ChatPromptTemplate([
                ("system", instruction),
                ("human", "{user_input}")
            ])
        
        print(instruction)
        
        chat = prompt.invoke({
            "user_input": user_input
        })
        
        response = self.llm.invoke(chat)
        
        print("Response: " + response)
        

        
        
        
        