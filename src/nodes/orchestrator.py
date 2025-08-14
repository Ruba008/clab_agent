from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from tools.intent_classifier import detect_intent
import base64
import secrets
from typing import Dict, TypedDict, List
import chromadb
import logging
import db
import json

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

    def create_planner(self, user_input: str) -> str:
        
        """Create planner for the user request"""
        
        intent = detect_intent(user_input=user_input)
        
        with open(file="/home/ruba/Documents/laas/clab_agent/src/nodes/instructions/IA_Agent_Instructions_EN.txt") as file:
            instruction = file.read()
            
            prompt = ChatPromptTemplate([
                ("system", "Instruction: {instruction}\n\n INTENT: {intent}"),
                ("human", "Customer request: {user_input}")
            ])
            
            messages = prompt.format_messages(
                intent=intent,
                user_input=user_input,
                instruction=instruction
            )
            
            response = self.llm.invoke(messages)
            
            start = response.find("[")
            end = response.rfind("]")
            json_response = response[start:end+1].replace('{{', '{').replace('}}', '}')
            
            json_response = json.loads(json_response)

            return json_response