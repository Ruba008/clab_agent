from pydantic import BaseModel, Field, model_validator
from typing import TypedDict, List, Literal, Optional

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
    
    plan: List[TaskModel] = Field(default_factory=list)

class State(TypedDict):
    
    session: str
    question: str
    intent: str
    plan: PlanModel
    response: str
    search_result: Optional[SearchResult]