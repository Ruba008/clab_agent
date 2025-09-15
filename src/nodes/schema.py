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
    model_config = ConfigDict(populate_by_name=True)  # v2: permite popular por nome e alias
    tasks_list: List[TaskModel] = Field(default_factory=list, alias="plan")

    @model_validator(mode="before")
    def _normalize(cls, v):
        if isinstance(v, dict) and "tasks_list" not in v and "plan" in v:
            v["tasks_list"] = v.get("plan", [])
        return v


class Doc(BaseModel):
    title: str = Field(description="Title of the document")
    subtitles: List[str] = Field(description="List of subtitles in the document")
    explain: str = Field(description="Combine ALL explanatory text between headers into ONE coherent paragraph")
    codeblocks: List[str] = Field(description="List of code blocks in the document")

class DocSum(BaseModel):
    docList: List[Doc] = Field(default_factory=list, description="List of summarized documents")
    

class State(TypedDict):
    
    session: str
    question: str
    intent: str
    plan: PlanModel
    response: str
    search_result: Optional[SearchResult]
    
class SimpleThinkingCallback(BaseCallbackHandler):
    def __init__(self, width: int = 80, height: int = 10, title: str = "💭 Model Thinking") -> None:
        self.width = width
        self.height = height
        self.title = title

        # Máx. chars em memória (apenas para não crescer infinito)
        self.max_chars = 50000

        self._buf = deque()         # guarda todos os chars (limitado por max_chars)
        self._live = None
        self._start_depth = 0
        self._in_think = False
        self._trimmed_once = False
        self._started = False

    # --- util: quebra em linhas visuais e recorta as últimas N linhas ---
    def _wrap_and_clip(self, text: str):
        # largura interna ~ largura do painel menos bordas laterais
        inner_width = max(8, self.width - 2)
        # altura interna (linhas visíveis de texto). Com height=10 => 8 linhas
        content_rows = max(1, self.height - 2)

        wrapped: list[str] = []
        # preserva quebras de linha explícitas e faz soft-wrap por largura
        for line in text.splitlines() or [""]:
            if line == "":
                wrapped.append("")  # mantém linhas vazias
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

        # prefixo "…" quando houve truncamento (scroll)
        if trimmed and visible:
            if visible[0]:
                visible[0] = "…" + visible[0][1:]
            else:
                visible[0] = "…"

        return "\n".join(visible)

    def _render(self):
        text = "".join(self._buf)
        clipped = self._wrap_and_clip(text)
        txt = Text(clipped, no_wrap=True, overflow="crop")  # já pré-wrap
        return Panel(
            txt,
            title=self.title,
            width=self.width,
            height=self.height,   # OBS: 10 => 8 linhas de texto visíveis
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

        # append char a char (permite atualizar “ao vivo”)
        for ch in token:
            self._buf.append(ch)
            # limite de memória
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
            console.print()  # quebra de linha final opcional