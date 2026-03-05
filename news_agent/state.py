from typing import Annotated, List, TypedDict, Union
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # messages is Annotated with operator.add so history accumulates automatically
    messages: Annotated[List[BaseMessage], operator.add]
    query: str
    country: Union[str, None]
    category: Union[str, None]
    search_results: List[dict]
    summary: str
    archived: bool
    decision: str