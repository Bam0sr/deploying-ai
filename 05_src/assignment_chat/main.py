"""LangGraph chat agent."""

import os

os.environ["LANGSMITH_TRACING"] = "false"

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

from assignment_chat.prompts import return_instructions
from assignment_chat.tools_api import search_meal, random_meal
from assignment_chat.tools_rag import search_recipes
from assignment_chat.tools_utils import convert_cooking_units, adjust_servings
from utils.logger import get_logger

_logs = get_logger(__name__)

load_dotenv(".env")
load_dotenv(".secrets")

API_GATEWAY_URL = "https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1"

chat_agent = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    base_url=API_GATEWAY_URL,
    api_key="any_value",
    default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY", "")},
)

tools = [search_meal, random_meal, search_recipes, convert_cooking_units, adjust_servings]

instructions = return_instructions()


def call_model(state: MessagesState):
    """Call model with tools and current messages."""
    response = chat_agent.bind_tools(tools).invoke(
        [SystemMessage(content=instructions)] + state["messages"]
    )
    return {"messages": [response]}


def get_graph():
    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    return builder.compile()
