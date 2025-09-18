from nodes.orchestrator import create_planner, State
from nodes.researcher import search
from nodes.runner import runner
from nodes.schema import PlanModel
from tools import db
from langgraph.graph import StateGraph, START, END
import config.logger_config as logger_config, logging
from rich.console import Console
from rich.traceback import install

"""
Main function to run the program. 
"""


install()

logger_config.loggerConfiguration()
logger = logging.getLogger(__name__)

console = Console(force_terminal=True)


if __name__ == "__main__":

    """
    Initilizing the state graph.
    Question is taken as input from the user
    Nodes and edges are added to the graph
    """
    
    console.clear()
    
    graph_builder = StateGraph(State)
    
    question = input("Welcome! What do you want to do?\n")
    
    
    #Initializing the state
    state: State = {
        "session": "",
        "question_explained": "",
        "question": question,
        "intent": "",
        "plan": PlanModel(),
        "response": "",
        "search_result": None
    }
    
    #Nodes
    graph_builder.add_node("Orchestrator", create_planner)
    graph_builder.add_node("Researcher", search)
    graph_builder.add_node("Runner", runner)
    
    #Edges
    graph_builder.add_edge(START, "Orchestrator")
    graph_builder.add_edge("Orchestrator", "Researcher")
    graph_builder.add_edge("Researcher", "Runner")
    graph_builder.add_edge("Runner", END)
    
    
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