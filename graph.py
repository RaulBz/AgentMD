# graph.py
from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from config import Config
from tools import fetch_doctors_tool, retrieve_reviews_tool

# Start a chat with automatic function calling enabled.
class ChatState(TypedDict):
    """State representing the customer's order conversation."""

    # The chat conversation. This preserves the conversation history
    # between nodes. The `add_messages` annotation indicates to LangGraph
    # that state is updated by appending returned messages, not replacing
    # them.
    messages: Annotated[list, add_messages]

    # The customer's in-progress order.
    order: list[str]

    # Flag indicating that the order is placed and completed.
    finished: bool

def human_node(state: ChatState) -> ChatState:
    """Display the last model message to the user, and receive the user's input."""
    last_msg = state["messages"][-1]
    print("Model:", last_msg.content)

    user_input = input("User: ")

    # If it looks like the user is trying to quit, flag the conversation
    # as over.
    if user_input in {"q", "quit", "exit", "goodbye"}:
        state["finished"] = True

    return state | {"messages": [("user", user_input)]}


def maybe_exit_human_node(state: ChatState) -> Literal["chatbot", "__end__"]:
    """Route to the chatbot, unless it looks like the user is exiting."""
    if state.get("finished", False):
        return END
    else:
        return "chatbot"

def maybe_route_to_tools(state: ChatState) -> Literal["tools", "human"]:
    """Route between human or tool nodes, depending if a tool call is made."""
    if not (msgs := state.get("messages", [])):
        raise ValueError(f"No messages found when parsing state: {state}")
        print('A')

    # Only route based on the last message.
    msg = msgs[-1]

    # When the chatbot returns tool_calls, route to the "tools" node.
    if hasattr(msg, "tool_calls") and len(msg.tool_calls) > 0:
        return "tools"
        print('T')
    else:
        return "human"
        print('HFi')

def chatbot_with_tools(state: ChatState, llm_with_tools) -> ChatState:
    """The chatbot with tools. A simple wrapper around the model's own chat interface."""
    defaults = {"order": [], "finished": False}

    if state["messages"]:
        new_output = llm_with_tools.invoke([Config.SYSINT]+ state["messages"])
    else:
        new_output = AIMessage(content=Config.WELCOME_MSG)

    # Set up some defaults if not already set, then pass through the provided state,
    # overriding only the "messages" field.
    return defaults | state | {"messages": [new_output]}


def build_graph(llm_with_tools):
    tools = [fetch_doctors_tool, retrieve_reviews_tool]
    tool_node = ToolNode(tools)
    graph_builder = StateGraph(ChatState)
    graph_builder.add_node("chatbot", lambda state: chatbot_with_tools(state, llm_with_tools))
    graph_builder.add_node("human", human_node)
    graph_builder.add_node("tools", tool_node)
    # Chatbot may go to tools, or human.
    graph_builder.add_conditional_edges("chatbot", maybe_route_to_tools)
    # Human may go back to chatbot, or exit.
    graph_builder.add_conditional_edges("human", maybe_exit_human_node)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    graph = graph_builder.compile()
    return graph




