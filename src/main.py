from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph
from typing import Dict, TypedDict
from nodes.orchestrator import Orchestrator

orchestrator1 = Orchestrator()

orchestrator1.create_planner("Algo nada a ver")