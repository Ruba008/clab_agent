from concurrent.futures import process
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from typing import Dict, TypedDict, List, Union, Any
from nodes.orchestrator import create_planner, State
from nodes.researcher import search
from nodes.schema import PlanModel
import tools.db as db
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display

"""
Main function to run the program. 
"""


if __name__ == "__main__":

    """
    Initilizing the state graph.
    Question is taken as input from the user
    Nodes and edges are added to the graph
    """
    
    graph_builder = StateGraph(State)
    
    question = input("Welcome! What do you want to do?\n")
    
    
    #Initializing the state
    state: State = {
        "session": "",
        "question": question,
        "intent": "",
        "plan": PlanModel(tasks_list=[]),
        "response": "",
        "search_result": None
    }
    
    #Nodes
    graph_builder.add_node("Orchestrator", create_planner)
    graph_builder.add_node("Researcher", search)
    
    #Edges
    graph_builder.add_edge(START, "Orchestrator")
    graph_builder.add_edge("Orchestrator", "Researcher")
    graph_builder.add_edge("Researcher", END)
    
    
    #Graph compilation and invocation
    graph = graph_builder.compile()
    final_state = graph.invoke(state)
    
    print(final_state)
    
    png_data = graph.get_graph().draw_mermaid_png()
    
    
    #Creating and saving the graph image
    try:
        with open("graph.png", "wb") as f:
            f.write(png_data)
        print("'graph.png' saved")
    except Exception as e:
        pass
    
    #Deleting the context collection after the session ends
    db.delete_collection(state["session"], "context")