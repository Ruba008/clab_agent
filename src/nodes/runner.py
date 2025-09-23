from nodes.orchestrator import response_filter
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
from tools.models import llm_management
from typing import Any, Dict
import subprocess
import webbrowser

console = Console(force_terminal=True)


def deploy_and_graph_topology(topology_file: str):
    console.print(Rule("[bold cyan] Starting topology deployment [/bold cyan]"))
    deploy_command = ["sudo", "containerlab", "deploy", "-t", topology_file]
    console.print(f"▶️  Executing: {' '.join(deploy_command)}")
    
    try:
        process = subprocess.Popen(
            deploy_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, 
            text=True,
            encoding='utf-8'
        )
        
        stdout_data, _ = process.communicate()
        
        if stdout_data:
            console.print(stdout_data.strip())
        
        if process.returncode != 0:
            console.print(f"[bold red]✗ Deployment failed with exit code {process.returncode}[/bold red]")
            return stdout_data

        console.print(f"[bold green]✓ Deployment of topology '{topology_file}' completed successfully![/bold green]")

    except FileNotFoundError:
        console.print("[bold red]✗ Error: The 'sudo' or 'containerlab' command was not found. Please ensure they are installed and in your PATH.[/bold red]")
        return "Command not found: 'sudo' or 'containerlab'."
    except Exception as e:
        console.print(f"[bold red]✗ An unexpected error occurred during deployment: {e}[/bold red]")
        return str(e)

    console.print(Rule("[bold cyan] Starting graph server [/bold cyan]"))
    graph_command = ["containerlab", "graph", "-t", topology_file]
    
    graph_process = None
    
    try:
        console.print(f"▶️  Executing in background: {' '.join(graph_command)}")
        graph_process = subprocess.Popen(graph_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(2)
        
        url = "http://127.0.0.1:50080"
        console.print(f"📈 Opening the topology graph in your browser at [link={url}]{url}[/link]")
        webbrowser.open(url)

    except Exception as e:
        console.print(f"[bold red]✗ Failed to start graph server: {e}[/bold red]")
        console.print("[bold yellow]Tip: Try running 'containerlab graph -t your_file.clab.yaml' manually.[/bold yellow]")

    cleanup_lab_on_enter(topology_file)

    if graph_process:

        graph_process.terminate() 
        console.print("[bold yellow]Servidor de grafos finalizado.[/bold yellow]")

    return None



def safe_docsum_conversion(data):
    if isinstance(data, DocSum):
        return data
    if data is None:
        return DocSum(docList=[])
    if isinstance(data, dict):
        try:
            if 'docList' in data:
                for doc in data['docList']:
                    if isinstance(doc, dict) and 'codeblocks' in doc:
                        if len(doc['codeblocks']) > 3:
                            console.print(f"[bold yellow] ⚠️  Truncating {len(doc['codeblocks'])} codeblocks to 3 for document: {doc.get('title', 'Unknown')}")
                            doc['codeblocks'] = doc['codeblocks'][:3]  
            return DocSum(**data)
        except Exception as e:
            console.print(f"[bold red] ✗ Error converting dict to DocSum: {e}")
            return DocSum(docList=[])

    if hasattr(data, 'docList'):
        try:
            doc_data = {'docList': []}
            for doc in data.docList:
                doc_dict = doc.__dict__ if hasattr(doc, '__dict__') else doc
                if isinstance(doc_dict, dict) and 'codeblocks' in doc_dict:
                    if len(doc_dict['codeblocks']) > 3:
                        console.print(f"[bold yellow] ⚠️  Truncating {len(doc_dict['codeblocks'])} codeblocks to 3")
                        doc_dict['codeblocks'] = doc_dict['codeblocks'][:3]
                doc_data['docList'].append(doc_dict)
            return DocSum(**doc_data)
        except Exception as e:
            console.print(f"[bold red] ✗ Error converting object with docList: {e}")
            return DocSum(docList=[])

    return DocSum(docList=[])

def string_to_yaml_file(yaml_string: str, output_file: str) -> Dict[str, Any]:
    
    try:
        parsed_data = yaml.safe_load(yaml_string)
        
        file_path = Path(output_file)
        action = "Replaced" if file_path.exists() else "Created"
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(yaml_string)
        
        console.print(f"[bold green] ✓ YAML {action.lower()}: {output_file}")
        return parsed_data
        
    except yaml.YAMLError as e:
        console.print(f"[bold red] ✗ Error YAML parser: {e}")
        raise
    except IOError as e:
        console.print(f"[bold red] ✗ Error writing the file: {e}")
        raise

def cleanup_lab_on_enter(topology_file: str, input_bool: bool = True):
    
    if input_bool:
        console.print(Rule("[bold yellow]Lab activate[/bold yellow]"))
        console.print("The topology graph has been opened in your browser.")
        console.print("Press [bold]Enter[/bold] in this terminal to [bold red]stop and remove[/bold red] all containers from the lab.")

        input()

        console.print(Rule("[bold red]Starting Lab Cleanup[/bold red]"))

    try:
        with open(topology_file, 'r') as f:
            lab_data = yaml.safe_load(f)
            lab_name = lab_data.get('name')

        if not lab_name:
            console.print("[bold red]✗ Could not find lab name in YAML file.[/bold red]")
            return

        client = docker.from_env()
        label_filter = f"clab-lab-name={lab_name}"
        
        lab_containers = client.containers.list(all=True, filters={"label": [label_filter]})

        if not lab_containers:
            console.print(f"[bold green]✓ No containers found for lab '{lab_name}'. Nothing to do.[/bold green]")
            return

        console.print(f"Found {len(lab_containers)} container(s) for lab '{lab_name}'.")

        for container in lab_containers:
            try:
                if container.status == 'running':
                    console.print(f"Stopping container: {container.name}...")
                    container.stop()
                    console.print(f"[bold green]✓ Stopped:[/bold green] {container.name}")
            except Exception as e:
                console.print(f"[bold red]✗ Error stopping {container.name}: {e}[/bold red]")

        for container in lab_containers:
            try:
                console.print(f"Removing container: {container.name}...")
                container.remove()
                console.print(f"[bold green]✓ Removed:[/bold green] {container.name}")
            except Exception as e:
                console.print(f"[bold red]✗ Error removing {container.name}: {e}[/bold red]")

        console.print(Rule("[bold green]Cleanup Completed[/bold green]"))

    except FileNotFoundError:
        console.print(f"[bold red]✗ Topology file not found: {topology_file}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]✗ An unexpected error occurred during cleanup: {e}[/bold red]")

def extract_and_pull_docker_images(yaml_string: str) -> List[str]:
    try:
        
        client = docker.from_env()
        
        image_pattern = r'^\s*image:\s*(.+)$'
        
        images_found = []
        pulled_images = []
        
        for line in yaml_string.split('\n'):
            match = re.search(image_pattern, line.strip())
            if match:
                image_name = match.group(1).strip().strip('"').strip("'")
                if image_name:
                    images_found.append(image_name)
        
        console.print(f"Images found: {images_found}")
        
        for image_name in images_found:
            try:
                console.print(f"[bold yellow] Verifying image: {image_name}")

                try:
                    local_image = client.images.get(image_name)
                    console.print(f"[bold green] ✓ Image {image_name} already exists locally.")
                except Exception:
                    console.print(f"[bold red] ✗ Image {image_name} not found locally.")
                
                console.print(f"[bold yellow] Pulling: {image_name}")
                image = client.images.pull(image_name)
                console.print(f"[bold green] ✓ Successfully pulled: {image_name}")
                pulled_images.append(image_name)
                
            except Exception as e:
                console.print(f"[bold red] ✗ Image not found in registry: {image_name} - {e}")
        
        return pulled_images
        
    except Exception as e:
        console.print(f"[bold red] ✗ Error connecting to Docker: {e}")
        raise


def runner(state: State) -> State:
    
    llm = llm_management("")
    llm_correction = ChatOllama(model="qwen2.5-coder:3b", temperature=0.05)
    
    with open(file="nodes/instructions/runner_instruction.txt", mode="r") as file:
    
        instruction = file.read().replace('{', '{{').replace('}', '}}')

        console.print("[bold green] 🧠​ Generating the .yaml ...")
        
        doclist = state["search_result"].docList if state.get("search_result") and state["search_result"] and hasattr(state["search_result"], "docList") else ""
        
        console.print(doclist)
        
        search_result = safe_docsum_conversion(state.get("search_result"))
        
        prompt = PromptTemplate(
                input_variables=["instruction", "question"],
                template=
                "INSTRUCTION:\n{instruction}\n" +
                "CLIENT QUESTION (THE OBJECTIVE): {question}\n" +
                "=== SEARCH RESULT ===\n\n" +
                "".join([
                    f"DOCUMENT {i+1}:\n"
                    f"Code (Syntax) Examples:\n" + 
                    "\n".join([f"\n{codeblock.replace('{', '{{').replace('}', '}}')}\n" for codeblock in doc.codeblocks]) + 
                    f"\n{'='*50}\n\n"
                    for i, doc in enumerate(search_result.docList)
            ])
        )
        
        
        chain = prompt | llm | response_filter
        
        yaml_content: str = chain.invoke({
            "instruction": instruction,
            "question": state["question_explained"]
        }, config={"callbacks": [SimpleThinkingCallback()]}) if chain else ""

        output_filename = "output.clab.yaml"
        string_to_yaml_file(yaml_content, output_filename)
        pulled_images = extract_and_pull_docker_images(yaml_content)
        
        deployment_error = deploy_and_graph_topology(output_filename)
        
        if deployment_error:
            while(deployment_error):
                
                cleanup_lab_on_enter(output_filename, input_bool=False)
                
                console.print("[bold green] 🧠​ Verifying the .yaml...")
                if deployment_error:
                    console.print(f"[bold red] ✗ Deployment error found:\n{deployment_error}[/bold red]")
                else:
                    console.print("[bold green] ✓ Deployment successful![/bold green]")

                
                prompt_correction = PromptTemplate(
                        input_variables=["instruction", "question"],
                        template=
                        "Correct the Containerlab YAML if it has any syntax error. Return ONLY the corrected YAML without any explanation.\n\n"
                        "CLIENT QUESTION (THE OBJECTIVE): {question}\n\n" +
                        "YAML TO CORRECT:\n{yaml_content}\n\n"
                        "Errors found during deployment:\n{errors}\n\n"
                )
                
                chain = prompt_correction | llm_correction | response_filter
                
                yaml_content: str = chain.invoke({
                    "yaml_content": yaml_content,
                    "question": state["question_explained"],
                    "errors": deployment_error
                }, config={"callbacks": [SimpleThinkingCallback()]}) if chain else ""
                
                string_to_yaml_file(yaml_content, output_filename)
                pulled_images = extract_and_pull_docker_images(yaml_content)
                deployment_error = deploy_and_graph_topology(output_filename)
        
        console.print(Rule("[bold blue]Conteúdo do YAML Gerado[/bold blue]"))
        console.print(yaml_content)
        console.print(Rule())
        
        

    return state