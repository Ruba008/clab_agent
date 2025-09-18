from langchain_ollama import ChatOllama
from nodes.orchestrator import llm, response_filter
from nodes.schema import State, SearchResult, DocSum, SimpleThinkingCallback, TaskModel, PlanModel
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from sentence_transformers.cross_encoder import CrossEncoder
from typing import Dict, List
import tools.db as db
import json, re, torch, hashlib, time
from rich.console import Console
from rich.rule import Rule
from rich.tree import Tree
import ollama

results: List[Dict] = []

llm_research = ChatOllama(model="qwen3:latest",
                    temperature=0.2,
                    format="json",
                    disable_streaming=False,
                    keep_alive=0)


# Stylization for rich console output
console = Console(force_terminal=True)
timeline_tree_researcher = Tree("⏳​ Researcher Timeline", guide_style="bold white")



# Essential for the output structuration
parser = JsonOutputParser(pydantic_object=SearchResult)
parser_docsum = JsonOutputParser(pydantic_object=DocSum)



def print_timeline_researcher():
    console.print(Rule("[bold blue]🔍 Research Module[/]"))
    console.print(timeline_tree_researcher)
    time.sleep(3)
    console.clear()
    


def search(state: State) -> State:
    
    timeline_tree_researcher.add(f"[green]✓[/green] Search Module Initialized.")
    print_timeline_researcher()

    try:
         with open(file="/home/ruba/Documents/laas/clab_agent/src/nodes/instructions/summarizer_instruction.txt") as file: 
            


            with console.status("[bold yellow] Downloading CrossEncoder model...", spinner="dots"):
                # Loading the cross encoder model
                model_cross: CrossEncoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")

            timeline_tree_researcher.add(f"[green]✓[/green] CrossEncoder downloaded.")
            print_timeline_researcher()
            
            
            
            with console.status("[bold yellow] Consulting ContainerLab Documentation...", spinner="dots"):
                #Querying the scrapy collection
                sum_instruction: str = file.read().strip().replace('{', '{{').replace('}', '}}')            
                query_result = db.query_scrapy([state["question_explained"]]) 
                docs_query = query_result.get("documents") if query_result else None

            timeline_tree_researcher.add(f"[green]✓[/green] ContainerLab Documentation Consulted.")
            print_timeline_researcher()


            
            # Cleaning the documents
            docs: List[str] = [re.sub(r'\\+', r'\\', str(page)) for page in docs_query[0]] if docs_query and docs_query[0] is not None else []
            docs = [page.replace("\\n", "\n").replace('{', '{{').replace('}', '}}') for page in docs]
            
            
            # Scoring the documents according to the tasks of the plan        
            with console.status("[bold yellow] Ranking the best informations...", spinner="dots"):
    
                pairs = []
                plan = state["plan"] if isinstance(state["plan"], PlanModel) else PlanModel(**state["plan"])
                tasks_list = plan.tasks_list
                
                for task in tasks_list:
                    task_description = task.description
                    if task.group == "runner":
                        pairs.extend([[task_description, doc] for doc in docs])

                # If no runner tasks, we score all docs against the question
                scores = model_cross.predict(pairs)
                
                
                doc_by_pair = [doc for _, doc in pairs]  # cada elemento em 'pairs' é [task_description, doc]
                scored_docs = list(zip(map(float, scores), doc_by_pair))
                
                
                # Selecting the top 3 unique documents
                def norm_key(txt: str) -> str:
                    norm = re.sub(r"\s+", " ", txt).strip()
                    return hashlib.sha1(norm.encode("utf-8")).hexdigest()
                
                # After normalization, keep only the best score for each unique document
                best_per_doc = {}
                for s, d in scored_docs:
                    k = norm_key(d)
                    if k not in best_per_doc or s > best_per_doc[k][0]:
                        best_per_doc[k] = (s, d)
                
                top3 = sorted(best_per_doc.values(), key=lambda x: x[0], reverse=True)[:3]
                top3_docs = [d for s, d in top3]

            timeline_tree_researcher.add(f"[green]✓[/green] Best responses selected.")
            print_timeline_researcher()
            
            
            
            # Freeing memory
            del model_cross
            torch.cuda.empty_cache() if torch.cuda.is_available() else None



            console.print("[bold green] 🧠​ Summarizing the research...")
            
            
            
            # Summarizing
            prompt_docs = PromptTemplate(
                input_variables=["sum_instruction"] + [f"doc{i}" for i in range(1, len(top3_docs) + 1)],
                partial_variables={"format_instructions": parser_docsum.get_format_instructions()},
                template=(
                    "INSTRUCTION: {sum_instruction}\n\n"
                    "INPUTS (3 docs):\n" +
                    "".join(
                        f"<DOC id='{i}'>\n{doc}\n</DOC>\n\n"
                        for i, doc in enumerate(top3_docs, start=1)
                    )
                )
            )
                


            chain = prompt_docs | llm_research | response_filter | parser_docsum

            doc_sum: DocSum = chain.invoke({
                "sum_instruction": sum_instruction,
                **{f"doc{i}": doc for i, doc in enumerate(docs, start=1)},
                "format_instruction": parser_docsum.get_format_instructions()
            }, config={"callbacks": [SimpleThinkingCallback()]})
        
            state["search_result"] = doc_sum
        
        

            timeline_tree_researcher.add(f"[green]✅[/green] Research Summarized.")
            print_timeline_researcher()

    except Exception as e:
        print(f"Researcher Summarizer File Error.\nError {e}")    
        exit()
        
    return state
