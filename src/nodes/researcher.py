from nodes.orchestrator import llm, response_filter
from nodes.schema import State, SearchResult, DocSum, SimpleThinkingCallback, TaskModel, PlanModel
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from sentence_transformers.cross_encoder import CrossEncoder
from typing import Dict, List
import tools.db as db
import json, re, torch, hashlib

results: List[Dict] = []


# Essential for the output structuration
parser = JsonOutputParser(pydantic_object=SearchResult)
parser_docsum = JsonOutputParser(pydantic_object=DocSum)

def search(state: State):
    

    try:
         with open(file="/home/ruba/Documents/laas/clab_agent/src/nodes/instructions/summarizer_instruction.txt") as file:
                model_cross: CrossEncoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
                
                db.connect_collection(None, "scrapy")
                
                sum_instruction: str = file.read().strip().replace('{', '{{').replace('}', '}}')
                
                docs_query = db.query([state["question"]]).get("documents")

                docs: List[str] = [re.sub(r'\\+', r'\\', str(page)) for page in docs_query[0]] if docs_query and docs_query[0] is not None else []
                docs = [page.replace("\\n", "\n").replace('{', '{{').replace('}', '}}') for page in docs]
                
                pairs = []
                
                plan = state["plan"] if isinstance(state["plan"], PlanModel) else PlanModel(**state["plan"])
                
                tasks_list = plan.tasks_list
                
                for task in tasks_list:
                    task_description = task.description
                    print(f"Task Description: {task_description}")
                    if task.group == "runner":
                        pairs.extend([[task_description, doc] for doc in docs])

                scores = model_cross.predict(pairs)
                
                
                doc_by_pair = [doc for _, doc in pairs]  # cada elemento em 'pairs' é [task_description, doc]
                scored_docs = list(zip(map(float, scores), doc_by_pair))
                
                def norm_key(txt: str) -> str:
                    norm = re.sub(r"\s+", " ", txt).strip()
                    return hashlib.sha1(norm.encode("utf-8")).hexdigest()
                
                best_per_doc = {}
                for s, d in scored_docs:
                    k = norm_key(d)
                    if k not in best_per_doc or s > best_per_doc[k][0]:
                        best_per_doc[k] = (s, d)
                
                top3 = sorted(best_per_doc.values(), key=lambda x: x[0], reverse=True)[:3]
                top3_docs = [d for s, d in top3]
                
                del model_cross
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                
                # Summarizing
                prompt_docs = PromptTemplate(
                    input_variables=["sum_instruction"] + [f"doc{i}" for i in range(1, len(top3_docs) + 1)],
                    partial_variables={"format_instructions": parser_docsum.get_format_instructions()},
                    template=(
                        "INSTRUCTION: {sum_instruction}\n\n"
                        "INPUTS (3 docs):\n" +
                        "".join(
                            f"<DOC id='{i}'>\n{doc}\n</DOC>\n\n"
                            for i, doc in enumerate(docs, start=1)
                        )
                    )
                )

                
                chain = prompt_docs | llm | response_filter |parser_docsum
                
                doc_sum = chain.invoke({
                    "sum_instruction": sum_instruction,
                    **{f"doc{i}": doc for i, doc in enumerate(docs, start=1)},
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

