from nodes.orchestrator import llm, response_filter
from nodes.schema import State, SearchResult, DocSum, SimpleThinkingCallback, TaskModel, PlanModel
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from sentence_transformers.cross_encoder import CrossEncoder
from langchain_ollama import ChatOllama
from typing import Dict, List
import tools.db as db
import json, re, torch, hashlib, time, docker, yaml
from rich.console import Console
from rich.rule import Rule
from rich.tree import Tree
from pathlib import Path
from tools.models import intent_explain

console = Console(force_terminal=True)

# Initialize the LLM
try:
    llm_runner = ChatOllama(model="qwen3:latest",
                    temperature=0.05,
                    disable_streaming=False)
except Exception as e:
    print(f"Error initializing LLM: {e}")



def runner(state: State) -> State:
    
    with open(file="nodes/instructions/runner_instruction.txt", mode="r") as file:
    
        instruction = file.read().replace('{', '{{').replace('}', '}}')

        
        prompt = PromptTemplate(
                input_variables=["search_result", "instruction", "question"],
                template=
                "INSTRUCTION:\n{instruction}\n" +
                "CLIENT QUESTION (THE OBJECTIVE): {question}\n" +
                "SEARCH RESULT: {search_result}\n"
        )
        
        chain = prompt | llm_runner | response_filter if llm else None
        
        print(str(state["search_result"]))
        
        yaml_content: str = chain.invoke({
            "search_result": str(state["search_result"]),
            "instruction": instruction,
            "question": state["question_explained"]
        }, config={"callbacks": [SimpleThinkingCallback()]}) if chain else ""
        
        print("\n\n" + yaml_content) 
        
        
    
    return state