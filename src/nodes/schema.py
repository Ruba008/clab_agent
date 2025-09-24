from collections import deque
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import TypedDict, List, Literal, Optional
from langchain.callbacks.base import BaseCallbackHandler
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
import textwrap

console = Console(force_terminal=True)

class Command(BaseModel):
    """
    Validate that Docker commands are restricted to safe operations.
        
    Only allows 'docker pull' commands to prevent potential security risks
    from arbitrary Docker command execution.
    """
    
    command: str
    dependencies: Literal["Docker API", "ContainerLab"]
    
    @model_validator(mode="after")
    def commands_allowed(self):
        if "docker" in self.command and not ("docker pull" in self.command):
            raise ValueError("the ONLY docker command allowed: docker pull <img_name>")
        return self
            
    
class SearchResult(BaseModel):
    """
    Container for search results including both theoretical and technical components.
    
    This model structures search results to separate conceptual information
    from actionable technical commands.
    """
    
    teorical_search: str
    technical_search: List[Command] = Field(default_factory=list)

class TaskModel(BaseModel):
    """
    Represents an individual task within a workflow plan.
    
    Tasks are categorized into groups to organize the workflow execution
    and track progress through different phases.
    """
    
    task: int
    description: str
    group: Literal["research", "runner"]
    
class PlanModel(BaseModel):
    """
    Represents a complete execution plan containing multiple tasks.
    
    This model handles both 'tasks_list' and 'plan' field names for backward
    compatibility, automatically normalizing the input data.
    """
    
    model_config = ConfigDict(populate_by_name=True)  # v2: permite popular por nome e alias
    tasks_list: List[TaskModel] = Field(default_factory=list, alias="plan")

    @model_validator(mode="before")
    def _normalize(cls, v):
        """
        Normalize input data to handle both 'plan' and 'tasks_list' field names.
        
        This validator ensures backward compatibility by accepting data with
        either field name and normalizing it to the expected structure.
        """
        
        if isinstance(v, dict) and "tasks_list" not in v and "plan" in v:
            v["tasks_list"] = v.get("plan", [])
        return v


class Doc(BaseModel):
    """
    Represents a processed document with structured content extraction.
    
    This model standardizes document representation for consistent processing
    of technical documentation, limiting code blocks to prevent memory issues.
    """
    
    title: str = Field(description="Title of the document")
    subtitles: List[str] = Field(description="List of subtitles in the document")
    explain: str = Field(description="Combine ALL explanatory text between headers into ONE coherent paragraph")
    codeblocks: List[str] = Field(description="List of code blocks in the document", max_length=3)
    
class DocSum(BaseModel):
    """
    Container for multiple processed documents.
    
    This model aggregates multiple Doc instances to represent a complete
    set of documentation or search results.
    """
    
    docList: List[Doc] = Field(default_factory=list, description="List of summarized documents")
    

class State(TypedDict):
    """
    System state container using TypedDict for runtime type checking.
    
    This represents the complete state of the system at any point in the
    workflow execution, containing all necessary data for processing.
    
    Attributes:
        session (str): Session identifier for tracking
        question (str): Original user question/request
        question_explained (str): Processed/expanded version of the question
        intent (str): Classified user intent
        plan (PlanModel): Execution plan with tasks
        response (str): System response/output
        search_result (Optional[DocSum]): Search results from documentation
    """
    
    session: str
    question: str
    question_explained: str
    intent: str
    plan: PlanModel
    response: str
    search_result: Optional[DocSum]
    
class SimpleThinkingCallback(BaseCallbackHandler):
    """
    Real-time callback handler for visualizing LLM thinking process.
    
    This callback provides live visual feedback of the LLM's output generation
    process, displaying a scrolling panel with the model's current output.
    It filters out <think> tags to show only the actual response content.
    """
    
    
    def __init__(self, width: int = 80, height: int = 10, title: str = "💭 Model Thinking") -> None:
        self.width = width
        self.height = height
        self.title = title

        self.max_chars = 50000

        self._buf = deque()        
        self._live = None
        self._start_depth = 0
        self._in_think = False
        self._trimmed_once = False
        self._started = False

    def _wrap_and_clip(self, text: str):
        
        inner_width = max(8, self.width - 2)
        
        content_rows = max(1, self.height - 2)

        wrapped: list[str] = []
       
        for line in text.splitlines() or [""]:
            if line == "":
                wrapped.append("")  
            else:
                wrapped.extend(
                    textwrap.wrap(
                        line,
                        width=inner_width,
                        replace_whitespace=False,
                        drop_whitespace=False,
                        break_long_words=True,
                        break_on_hyphens=False,
                    )
                )

        trimmed = len(wrapped) > content_rows
        visible = wrapped[-content_rows:] if trimmed else wrapped

   
        if trimmed and visible:
            if visible[0]:
                visible[0] = "…" + visible[0][1:]
            else:
                visible[0] = "…"

        return "\n".join(visible)

    def _render(self):
        text = "".join(self._buf)
        clipped = self._wrap_and_clip(text)
        txt = Text(clipped, no_wrap=True, overflow="crop")  
        return Panel(
            txt,
            title=self.title,
            width=self.width,
            height=self.height,   
            padding=0,
        )

    def _start_live(self):
        if self._live is None:
            self._live = Live(self._render(), console=console, refresh_per_second=24, transient=True)
            self._live.start()
            self._started = True

    def on_llm_start(self, *args, **kwargs) -> None:
        self._start_depth += 1
        if self._start_depth == 1:
            self._buf.clear()
            self._in_think = False
            self._trimmed_once = False
            self._live = None
            self._started = False

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        t = token.strip()
        if t == "<think>":
            self._in_think = True
            return
        if t == "</think>":
            self._in_think = False
            return
        if self._in_think:
            return

        if not self._started:
            self._start_live()

        
        for ch in token:
            self._buf.append(ch)
            
            if len(self._buf) > self.max_chars:
                self._buf.popleft()
                self._trimmed_once = True

        if self._live:
            self._live.update(self._render())

    def on_llm_end(self, *args, **kwargs) -> None:
        self._start_depth = max(0, self._start_depth - 1)
        if self._start_depth == 0 and self._live:
            self._live.update(self._render())
            self._live.stop()
            self._live = None
            self._started = False
            console.print()  