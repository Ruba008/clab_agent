from pydantic import BaseModel, Field, model_validator
from typing import TypedDict, List, Literal, Optional
from langchain.callbacks.base import BaseCallbackHandler

class Command(BaseModel):
    command: str
    dependencies: Literal["Docker API", "ContainerLab"]
    
    @model_validator(mode="after")
    def commands_allowed(self):
        if "docker" in self.command and not ("docker pull" in self.command):
            raise ValueError("the ONLY docker command allowed: docker pull <img_name>")
        return self
            
    
class SearchResult(BaseModel):
    teorical_search: str
    technical_search: List[Command] = Field(default_factory=list)

class TaskModel(BaseModel):
    task: int
    description: str
    group: Literal["research", "runner"]
    
class PlanModel(BaseModel):
    tasks_list: List[TaskModel] = Field(default_factory=list)


class Doc(BaseModel):
    title: str
    subtitles: List[str]
    explain: str
    codeblocks: List[str]
    
class DocSum(BaseModel):
    docList: List[Doc] = Field(default_factory=list)
    

class State(TypedDict):
    
    session: str
    question: str
    intent: str
    plan: PlanModel
    response: str
    search_result: Optional[SearchResult]
    
class SimpleThinkingCallback(BaseCallbackHandler):
    def __init__(self) -> None:
        self.ignored_tokens = {"<think>", "</think>"}
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        
        if token not in self.ignored_tokens:
            print(token, end="", flush=True)