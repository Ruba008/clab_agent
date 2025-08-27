from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from tools.intent_classifier import detect_intent
from typing import TypedDict, List
import base64
import secrets
import db
import json

llm = OllamaLLM(model="llama3.1")

class Task(TypedDict):
    task: int
    description: str
    group: str
    
class Command(TypedDict):
    command: str
    dependencies: str
    
class SearchResult(TypedDict):
    teorical_search: str
    technical_search: List[Command]

class State(TypedDict):
    
    question: str
    intent: str
    plan: List[Task]
    task_number: int
    description: str
    group: str
    responses: str
    search_result: SearchResult


def create_planner(state: State):
    
    session = base64.urlsafe_b64encode(secrets.token_bytes(16)).rstrip(b"=").decode("ascii")
    db.create_session(session)

    context = db.query_context(session_id=session, user_input=state["question"])
    intent = detect_intent(user_input=state["question"])
    
    state["intent"] = intent
    
    try:
        with open(file="/home/ruba/Documents/laas/clab_agent/src/nodes/instructions/orchestrator_instruction.txt") as file:
            instruction = file.read().replace('{', '{{').replace('}', '}}')
            
            prompt = ChatPromptTemplate([
                ("system", "INSTRUCTION: {instruction}\n\n INTENT: {intent}\n\n"),
                ("human", "CUSTOMER REQUEST: {user_input}\n\n"),
                ("ai", "CONTEXT: {context}")
            ])
            
            messages = prompt.format_messages(
                intent=intent,
                user_input=state["question"],
                instruction=instruction,
                context=context if context else "No context found."
            )
            
            response = llm.invoke(messages)
            
            db.add_context(
                session_id=session,
                user_input=state["question"],
                response=response
            )
            
            start = response.find("[")
            end = response.rfind("]")
            json_response_str = response[start:end+1].replace('{{', '{').replace('}}', '}').replace('\n', '')
            
            json_list: list[Task] = json.loads(json_response_str)
            
            state["plan"] = json_list
            
    except Exception as e:
        print(f"Orchestrator Instruction File Error. Error: {e}")
        exit()
        
    return state
    