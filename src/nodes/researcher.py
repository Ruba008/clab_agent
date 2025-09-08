import json
from typing import Dict, List
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import tools.db as db
from nodes.orchestrator import llm
from nodes.schema import State, SearchResult
import json

results: List[Dict] = []


# Essential for the output structuration
parser = JsonOutputParser(pydantic_object=SearchResult)

def search(state: State):

    try:
        with open(file="/home/ruba/Documents/laas/clab_agent/src/nodes/instructions/search_instruction.txt") as file:
            
            instruction = file.read().strip().replace('{', '{{').replace('}', '}}')
            db.connect_collection(None, "scrapy")
            documentation = db.query([str(state["plan"])]).get("documents")
            
            doc = documentation[0] if documentation != None else "No documentation found."

            prompt = PromptTemplate(
                input_variables=["intent", "instruction", "documentation1", "documentation2", "documentation3"],
                template=(
                            "SYSTEM ROLE (do not ignore): You are the Researcher module...\n"
                            "USER INTENT: {intent}\n"
                            "TASKS JSON: {tasks}\n"
                            "INSTRUCTION (hard rules):\n{instruction}\n"
                            "<<EMBEDDED CONTAINERLAB DOC 1>>\n{documentation1}\n<<END>>\n"
                            "<<EMBEDDED CONTAINERLAB DOC 2>>\n{documentation2}\n<<END>>\n"
                            "<<EMBEDDED CONTAINERLAB DOC 3>>\n{documentation3}\n<<END>>\n"
                        )
            )
            
            
            chain = prompt | llm | parser
            
            result: SearchResult = chain.invoke({
                "instruction": instruction,
                "documentation1": doc[0],
                "documentation2": doc[1],
                "documentation3": doc[2],
                "tasks": json.dumps(state["plan"], ensure_ascii=False),
                "intent": state["intent"]
            })
            

            state["search_result"] = result
            
    except Exception as e:
        print(f"Researcher Instruction File Error.\nError {e}")    
        exit()   

    return state

