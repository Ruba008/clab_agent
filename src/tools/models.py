import time
import torch, subprocess, asyncio
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from google.cloud import dialogflow_v2 as dialogflow
from google.api_core.exceptions import NotFound
from rich.console import Console
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from typing import Literal
from langchain_core.output_parsers import StrOutputParser

console = Console(force_terminal=True)
 
def intent_explain(client_question: str) -> str:
    
    llm = ChatOllama(model="qwen2.5:3b")
    output_parser = StrOutputParser()

    prompt = PromptTemplate(
        input_variables=["client_question"],
        template="""Task: Convert the client's question into a technical reformulation for Containerlab. Use only valid Containerlab keywords. The output must be exactly two lines.

        Containerlab keywords are: name, mgmt, topology, nodes, links, network, ipv4-subnet, ipv6-subnet, ipv4-gw, ipv6-gw, kind, image, startup-config, binds, ports, env, exec, cmd, mgmt-ipv4, mgmt-ipv6, labels, cpu, memory, runtime, network-mode, sysctls, dns, publish, group, license, endpoints, mtu, vars.
        
        Example:
        CLIENT QUESTION:
        I need to connect two Docker containers on the same network so they can talk to each other.
        CORRECT OUTPUT:
        Technical reformulation: Define a Containerlab topology with two nodes of kind 'linux' connected via endpoints in links section.
        Keywords: topology, nodes, kind, linux, links, endpoints, image, name

        Now, perform the task:
        CLIENT QUESTION:
        {client_question}
        CORRECT OUTPUT:"""
    )
    
    chain = prompt | llm | output_parser
    
    result = chain.invoke({
            "client_question": client_question
    })
    
    return result



def detect_intent(user_input: str) -> str:
    PROJECT_ID = "intent-classifier-dhrd"
    SESSION_ID = "teste1"
    LANG = "en"
    
    
    agent = dialogflow.AgentsClient().get_agent(request={"parent": f"projects/{PROJECT_ID}"})
    client = dialogflow.SessionsClient()
    session = client.session_path(PROJECT_ID, SESSION_ID)
    text_input = dialogflow.TextInput(text=user_input, language_code=LANG)
    query_input = dialogflow.QueryInput(text=text_input)
    resp = client.detect_intent(request={"session": session, "query_input": query_input})
    
    return resp.query_result.intent.display_name

def llm_management(response_format: Literal["json", ""]):
    
    
    console.print("[yellow] Verifying Ollama server status ...[/yellow]")
    try:
        subprocess.run(["ollama", "ps"], capture_output=True, text=True, check=True)
        console.print("[bold green]✓ Ollama server already in execution .[/bold green]")
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[bold yellow]! Ollama server not found ...[/bold yellow]")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5) 
        console.print("[bold green]✓ Ollama server started.[/bold green]")


    with console.status("[bold yellow] Loading model LLM (qwen3:latest)...[/bold yellow]", spinner="dots"):
        llm = ChatOllama(model="qwen3:latest",
                         temperature=0.05,
                         format=response_format,
                         
                         num_ctx=10000)
        
    console.print("[bold green]✓ LLM loaded sucessfully.[/bold green]")  
    return llm

    