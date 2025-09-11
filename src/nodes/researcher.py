import json
from typing import Dict, List
import re
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import tools.db as db
from nodes.orchestrator import llm, response_filter
from nodes.schema import State, SearchResult, DocSum, SimpleThinkingCallback
import json

results: List[Dict] = []


# Essential for the output structuration
parser = JsonOutputParser(pydantic_object=SearchResult)
parser_docsum = JsonOutputParser(pydantic_object=DocSum)

def search(state: State):
    
    print(state)

    try:
         with open(file="/home/ruba/Documents/laas/clab_agent/src/nodes/instructions/summarizer_instruction.txt") as file:
                db.connect_collection(None, "scrapy")
                
                sum_instruction = file.read().strip().replace('{', '{{').replace('}', '}}')
                
                documentation = db.query([str(state["plan"])]).get("documents")
            
                doc: List[str] = [re.sub(r'\\+', r'\\', str(page)) for page in documentation[0]] if documentation and documentation[0] is not None else []
                doc = [page.replace("\\n", "\n") for page in doc]
                
                doc1: str = doc[0]
                doc2: str = doc[1]
                doc3: str = doc[2]
                
                
                # Summarizing
                prompt_docs = PromptTemplate(
                    input_variables=["doc1", "doc2", "doc3", "sum_instruction", "format_instruction"],
                    template=(
                        "== BEGIN INSTRUCTION ==\n\n{sum_instruction}\n\n" +
                        "OUTPUT FORMAT (HARD RULES)\n{format_instruction}\n\n" +
                        "INPUTS (3 docs):\n\n" + 
                        "DOCUMENTATION NUMBER 1\n-- BEGIN DOCUMENTATION 1 --\n\n{doc1}\n\n-- END DOCUEMENTATION 1 --\n\n" + 
                        "DOCUMENTATION NUMBER 2\n-- BEGIN DOCUMENTATION 2 --\n\n{doc2}\n\n-- END DOCUEMENTATION 2 --\n\n" + 
                        "DOCUMENTATION NUMBER 3\n-- BEGIN DOCUMENTATION 3 --\n\n{doc3}\n\n-- END DOCUEMENTATION 3 --\n\n" +
                        "== END INSTRUCTION =="
                    )
                )
                
                chain = prompt_docs | llm | response_filter |parser_docsum
                
                doc_sum: DocSum = chain.invoke({
                    "sum_instruction": sum_instruction,
                    "doc1": doc1,
                    "doc2": doc2,
                    "doc3": doc3,
                    "format_instruction": parser_docsum.get_format_instructions()
                }, config={"callbacks": [SimpleThinkingCallback()]})
                
                print(doc_sum)
                
    except Exception as e:
        print(f"Researcher Summarizer File Error.\nError {e}")    
        exit()   


    try:
        with open(file="nodes/instructions/search_instruction.txt") as file:
            
            instruction = file.read().strip().replace('{', '{{').replace('}', '}}')

            prompt = PromptTemplate(
                input_variables=["intent", "instruction", "documentation1", "documentation2", "documentation3"],
                partial_variables={"format_instructions": parser.get_format_instructions()},
                template=(
                            "USER INTENT: {intent}\n"
                            "TASKS JSON: {tasks}\n"
                            "INSTRUCTION (hard rules):\n{instruction}\n"
                        )
            )
            
            
            chain = prompt | llm | parser
            
            result: SearchResult = chain.invoke({
                "instruction": instruction,
                "tasks": json.dumps(state["plan"], ensure_ascii=False),
                "intent": state["intent"]
            })

            state["search_result"] = result
            
    except Exception as e:
        print(f"Researcher Instruction File Error.\nError {e}")    
        exit()   

    return state

