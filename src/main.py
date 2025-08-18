from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph
from typing import Dict, TypedDict, List
from nodes.orchestrator import Orchestrator

class AgentState(TypedDict):
    task_number: int
    description: str
    group: List[str]

orchestrator = Orchestrator()

while True:

    question = input("Welcome! What do you want to do?\n")
    orchestrator.create_planner(question)
    
