import json
from typing import Dict, List
from langchain_ollama.llms import OllamaLLM

import db

from nodes.orchestrator import State, llm, Command, SearchResult

from langchain_core.prompts import ChatPromptTemplate

results: List[Dict] = []

def search(state: State):
    
    #scrapy_docs = scrapy_clab_documentation()

    try:
        with open(file="/home/ruba/Documents/laas/clab_agent/src/nodes/instructions/search_instruction.txt") as file:
            
            while (True):
            
                instruction = file.read().strip().replace('{', '{{').replace('}', '}}')

                prompt = ChatPromptTemplate([
                        ("system", "Instruction: {instruction}\n\nIntent:{intent}"),
                        ("human", "Tasks: {tasks}")
                    ])
                
                messages = prompt.format_messages(
                    instruction=instruction,
                   # documentation=scrapy_docs,
                    tasks=str(state["plan"]),
                    intent=state["intent"]
                )
                
                response = llm.invoke(messages)
                
                print(response) 
                
                start = response.find("{{") if response.find("{{") else response.find("{")
                
                if start == -1:
                    continue
                else:
                    break
                
            end = response.rfind("}}") if response.find("}}") else response.rfind("}")
            json_response_str = response[start:end+1].replace('{{', '{').replace('}}', '}').replace('\n', '')
            
            json_list: SearchResult = json.loads(json_response_str)
            
                
            state["search_result"] = json_list
            
    except Exception as e:
        print(f"Researcher Instruction File Error. Error {e}")    
        exit()   

    return state

