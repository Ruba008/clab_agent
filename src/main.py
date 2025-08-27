from concurrent.futures import process
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from typing import Dict, TypedDict, List, Union, Any

from nodes.orchestrator import create_planner
from nodes.researcher import search
class State(TypedDict):
    question: str
    intent: str
    plan: List[Any]
    task_number: int
    description: str
    group: str
    responses: str
    search_result: Dict[str, Union[str, List[Any]]]

from langgraph.graph import StateGraph, START, END

from IPython.display import Image, display
    
if __name__ == "__main__":
    
    graph_builder = StateGraph(State)
    
    question = input("Welcome! What do you want to do?\n")
    
    state: State = {
        "question": question,
        "intent": "",
        "plan": [],
        "task_number": 0,
        "description": "",
        "group": "",
        "responses": "",
        "search_result": {"technical_search": "", "teorical_search": []}
    }
    
    
    graph_builder.add_node("Orchestrator", create_planner)
    graph_builder.add_node("Researcher", search)
    
    graph_builder.add_edge(START, "Orchestrator")
    graph_builder.add_edge("Orchestrator", "Researcher")
    graph_builder.add_edge("Researcher", END)
    
    graph = graph_builder.compile()
    
    final_state = graph.invoke(state)
    
    print(final_state)
    
    png_data = graph.get_graph().draw_mermaid_png()
    
    try:
        with open("graph.png", "wb") as f:
            f.write(png_data)
        print("'graph.png' saved")
    except Exception as e:
        pass
    
    #graph_builder.add_node("Orchestrator", Orchestrator.create_planner)
    