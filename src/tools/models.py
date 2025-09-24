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
    """
    Convert a client's natural language question into a technical Containerlab reformulation.
    
    This function uses a local LLM to analyze the user's question and reformulate it using
    proper Containerlab terminology and keywords. It ensures the output is structured
    consistently with technical reformulation and relevant keywords.
    """
    
    # Initialize local LLM with relatively low temperature for consistent technical output
    llm = ChatOllama(model="qwen2.5:3b")
    output_parser = StrOutputParser()

    
    # Create comprehensive prompt template with Containerlab-specific instructions
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
    """
    Detect user intent using Google Cloud Dialogflow.
    
    This function connects to a pre-configured Dialogflow project to classify
    the user's input into predefined intent categories. It uses a static
    session for consistency across multiple requests.
    
    Args:
        user_input (str): User's natural language input to classify
        
    Returns:
        str: Display name of the detected intent from Dialogflow
        
    Raises:
        google.api_core.exceptions.NotFound: If project or agent not found
        google.auth.exceptions.DefaultCredentialsError: If authentication fails
        
    Note:
        Requires Google Cloud credentials to be configured in the environment
        (via GOOGLE_APPLICATION_CREDENTIALS or default service account)
    """
    
    # Google Cloud project configuration
    PROJECT_ID = "" # Dialogflow project ID
    SESSION_ID = "" # Static session for consistent context
    LANG = "en" # Language code for input processing
    
    
    # Initialize Dialogflow clients
    # AgentsClient manages the Dialogflow agent configuration
    agent = dialogflow.AgentsClient().get_agent(request={"parent": f"projects/{PROJECT_ID}"})
    
    # SessionsClient handles the actual intent detection requests
    client = dialogflow.SessionsClient()
    
    # Construct session path for the request
    session = client.session_path(PROJECT_ID, SESSION_ID)
    
    # Create text input object with language specification
    text_input = dialogflow.TextInput(text=user_input, language_code=LANG)
    
    # Wrap text input in query input object 
    query_input = dialogflow.QueryInput(text=text_input)
    
    # Send intent detection request to Dialogflow
    resp = client.detect_intent(request={"session": session, "query_input": query_input})
    
    # Extract and return the detected intent's display name
    return resp.query_result.intent.display_name



def llm_management(response_format: Literal["json", ""]):
    """
    Checks if Ollama server is running
    Starts the server if not running
    Loads the specified model with configuration
    Provides visual feedback throughout the process
    """
    
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

    