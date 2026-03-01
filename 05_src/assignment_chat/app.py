"""Gradio chat interface."""

from assignment_chat.main import get_graph
from langchain_core.messages import HumanMessage, AIMessage
import gradio as gr
from dotenv import load_dotenv

from utils.logger import get_logger

_logs = get_logger(__name__)

load_dotenv(".secrets")

graph = get_graph()


def chef_chat(message: str, history: list[dict]) -> str:
    langchain_messages = []
    for msg in history:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
    langchain_messages.append(HumanMessage(content=message))

    state = {"messages": langchain_messages}
    response = graph.invoke(state)
    return response["messages"][-1].content


chat = gr.ChatInterface(
    fn=chef_chat,
    type="messages",
    title="Chef Amico",
    description="Your friendly Italian chef assistant! Ask me about recipes, cooking tips, or unit conversions.",
)

if __name__ == "__main__":
    _logs.info("Starting Chef Amico Chat App...")
    chat.launch()
