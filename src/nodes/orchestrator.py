from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda
from langchain.schema import BaseMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from tools.intent_classifier import detect_intent
from nodes.schema import State, PlanModel, SimpleThinkingCallback
import base64
import re, time, torch
import secrets
import tools.db as db
from rich.console import Console
from rich.tree import Tree
from rich.rule import Rule
from rich.live import Live
from tools.models import intent_explain
import ollama


# Stylization for rich console output
console = Console(force_terminal=True)
timeline_tree_orchestrator = Tree("⏳​ Orchestrator Timeline", guide_style="bold white")

# Initialize the LLM
try:
    llm = ChatOllama(model="qwen3:latest",
                    temperature=0.05,
                    format="json",
                    disable_streaming=False,
                    keep_alive=0)
except Exception as e:
    print(f"Error initializing LLM: {e}")



# Essential for the output structuration
parser_orch = JsonOutputParser(pydantic_object=PlanModel)

def print_timeline_orchestrator():
    console.print(Rule("[bold blue]🧠​ Orchestrator Module[/]"))
    console.print(timeline_tree_orchestrator)
    time.sleep(3)
    console.clear()
    

            
def response_filter(msg) -> str:
    if isinstance(msg, BaseMessage):
        text = msg.content
    else:
        text = str(msg)
    
    response = re.sub(r"<think>.*?</think>", "", str(text), flags=re.DOTALL)
    
    return response.strip()
    
def create_planner(state: State) -> State:
    
    """
    Plan creation
    Session creation
    Intent detection
    Context retrieval
    Response from the LLM is parsed and added to the state
    """

    timeline_tree_orchestrator.add(f"[green]✓[/green] LLM Initialized.")
    print_timeline_orchestrator()
    
    
    #Creating a unique session ID
    state["session"] = base64.urlsafe_b64encode(secrets.token_bytes(16)).rstrip(b"=").decode("ascii")

    state["question_explained"] = intent_explain(state["question"])
    
    #Context retrieval
    with console.status("[bold yellow] Capturing context...", spinner="dots"):
        
        context = db.query_context([state["question"]], state["session"])
      
    timeline_tree_orchestrator.add(f"[green]✓[/green] Context retrieved.")
    print_timeline_orchestrator()
   
   
    #Intent detection
    with console.status("[bold yellow] Detecting user's intent...", spinner="dots"):
    
        state["intent"] = detect_intent(user_input=state["question"])
    
    timeline_tree_orchestrator.add(f"[green]✓[/green] User intent detected: {state['intent']}.") 
    print_timeline_orchestrator()
    
    filter_node = RunnableLambda(response_filter)

    with open(file="nodes/instructions/orchestrator_instruction.txt", mode="r") as file:
        
        
       
        #Extracting the instruction from the file and adapting it for the prompt template
        with console.status("[bold yellow] Analysing...", spinner="dots"):
            instruction = file.read().replace('{', '{{').replace('}', '}}')
            
            prompt = PromptTemplate(
                input_variables=["intent", "user_input", "instruction", "context"],
                partial_variables={"format_instructions": parser_orch.get_format_instructions()},
                template="USER INTENT: {intent}\n" +
                "Return ONLY one valid JSON object that matches this schema. No prose, no markdown, no comments, no backticks.\n" 
                "USER INPUT: {user_input}\n" + 
                "INSTRUCTION:\n{instruction}\n" +
                "CONTEXT:\n{context}"
            )
            
        timeline_tree_orchestrator.add(f"[green]✓[/green] Context retrieved.")          
        print_timeline_orchestrator()
        
        console.print("[bold green] 🧠​ Generating the plan...")
        # Prompt -> LLM -> Formatation
        chain = prompt | llm | filter_node | parser_orch if llm else None

        result: PlanModel = chain.invoke({
            "intent": state["intent"],
            "user_input": state["question_explained"],
            "instruction": instruction,
        "context": context,
        }, config={"callbacks": [SimpleThinkingCallback()]}) if chain else PlanModel()
        
        state["plan"] = result
        
        console.clear()
        
        timeline_tree_orchestrator.add(f"[green]✅[/green] Plan ready.") 
        print_timeline_orchestrator()
        
    return state