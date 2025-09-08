from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from tools.intent_classifier import detect_intent
from nodes.schema import State, PlanModel
import base64
import secrets
import tools.db as db

# Initializing the LLM model


# Initializing the LLM structured    
llm = ChatOllama(model="llama3.1")

# Essential for the output structuration
parser = JsonOutputParser(pydantic_object=PlanModel)

def create_planner(state: State):
    
    """
    Plan creation
    Session creation
    Intent detection
    Context retrieval
    Response from the LLM is parsed and added to the state
    """
    
    #Creating a unique session ID
    state["session"] = base64.urlsafe_b64encode(secrets.token_bytes(16)).rstrip(b"=").decode("ascii")

    #Creating and connecting to the collection
    db.connect_collection(state["session"], "context")

    #Context retrieval
    context = db.query([state["question"]])
    
    #Intent detection
    state["intent"] = detect_intent(user_input=state["question"])

    
    try:
        with open(file="nodes/instructions/orchestrator_instruction.txt", mode="r") as file:
            
            #Extracting the instruction from the file and adapting it for the prompt template
            instruction = file.read().replace('{', '{{').replace('}', '}}')
            
            prompt = PromptTemplate(
                input_variables=["intent", "user_input", "instruction", "context"],
                partial_variables={"format_instructions": parser.get_format_instructions()},
                template="USER INTENT: {intent}\n" + 
                "USER INPUT: {user_input}\n" + 
                "INSTRUCTION:\n{instruction}\n" +
                "CONTEXT:\n{context}"
            )
            
            # Prompt -> LLM -> Formatation
            chain = prompt | llm | parser
            
            result: PlanModel = chain.invoke({
                "intent": state["intent"],
                "user_input": state["question"],
                "instruction": instruction,
                "context": context,
            })
            
            state["plan"] = result
            
    except Exception as e:
        print(f"Orchestrator Instruction File Error. Error: {e}")
        exit()
        
    return state