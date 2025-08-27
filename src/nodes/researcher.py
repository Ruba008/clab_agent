import json
from tools.scrapy_documentation import ClabSpider
from scrapy.crawler import CrawlerProcess
from scrapy import signals
from typing import Dict, List
from langchain_ollama.llms import OllamaLLM

from nodes.orchestrator import State, llm, Command, SearchResult

from langchain_core.prompts import ChatPromptTemplate

results: List[Dict] = []

def search(state: State):
    
    scrapy_docs = scrapy_clab_documentation()

    try:
        with open(file="/home/ruba/Documents/laas/clab_agent/src/nodes/instructions/search_instruction.txt") as file:
            instruction = file.read().strip().replace('{', '{{').replace('}', '}}')

            prompt = ChatPromptTemplate([
                    ("system", "Instruction: {instruction}\n\nINTENT:{intent}"),
                    ("human", "Tasks: {tasks}")
                ])
            
            messages = prompt.format_messages(
                instruction=instruction,
                documentation=scrapy_docs,
                tasks=str(state["plan"]),
                intent=state["intent"]
            )
            
            response = llm.invoke(messages)
            
            print(response) 
            
            start = response.find("{{") if response.find("{{") else response.find("{")
            end = response.rfind("}}") if response.find("}}") else response.rfind("}")
            json_response_str = response[start:end+1].replace('{{', '{').replace('}}', '}').replace('\n', '')
            
            json_list: SearchResult = json.loads(json_response_str)
            
            
            state["search_result"] = json_list
            
    except Exception as e:
        print(f"Researcher Instruction File Error. Error {e}")    
        exit()   

    print(state)

    return state


def collect_item(item):
        results.append(item)

def scrapy_clab_documentation() -> List[Dict]:
    
    results.clear()

    process = CrawlerProcess(settings={
        "LOG_LEVEL": "ERROR",
    })

    crawler = process.create_crawler(ClabSpider)
    crawler.signals.connect(collect_item, signal=signals.item_scraped)

    process.crawl(crawler)
    process.start()
    
    return results

