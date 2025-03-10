import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from langgraph.prebuilt import ToolNode
import json
from google.api_core import retry
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from IPython.display import Image, display
from pprint import pprint
from langchain_core.messages.ai import AIMessage
from langchain_core.tools import tool
from typing import Literal
import time
from dotenv import load_dotenv
from config import Config

# Load environment variables from .env file
config = {'Model':"gemini-1.5-flash-latest"}
#config['Model'] = "ChatBioGPT"
# Access the API key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not GOOGLE_API_KEY or not HF_API_TOKEN:
    raise ValueError("API keys not found in .env file")



# ===========================
# CONFIGURE GEMINI MODEL
# ===========================

# The system instruction defines how the chatbot is expected to behave and includes
# rules for when to call different functions, as well as rules for the conversation, such
# as tone and what is permitted for discussion.

# Try using different models. The `pro` models perform the best, especially
# with tool-calling. The `flash` models are super fast, and are a good choice
# if you need to use the higher free-tier quota.
# Check out the features and quota differences here: https://ai.google.dev/pricing
import requests

class ChatBioGPT:
    def __init__(self, api_token, model="microsoft/biogpt"):
        self.url = f"https://api-inference.huggingface.co/models/{model}"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.tools = None  # Placeholder for tool binding compatibility

    def invoke(self, messages):
        # Convert message history to a single prompt
        prompt = ""
        for msg in messages:
            if isinstance(msg, tuple) and msg[0] == "system":
                prompt += f"System: {msg[1]}\n"
            elif isinstance(msg, tuple) and msg[0] == "user":
                prompt += f"User: {msg[1]}\n"
            elif hasattr(msg, "content"):
                prompt += f"{msg.content}\n"
        
        payload = {
            "inputs": prompt,
            "parameters": {"max_length": 200, "temperature": 0.7}
        }
        response = requests.post(self.url, headers=self.headers, json=payload)
        if response.status_code == 200:
            text = response.json()[0]["generated_text"]
            return AIMessage(content=text)  # Return in LangChain-compatible format
        else:
            return AIMessage(content=f"Error: API call failed ({response.status_code})")

    def bind_tools(self, tools):
        # Minimal tool-binding shim
        self.tools = tools
        return self



# Start a chat with automatic function calling enabled.
class OrderState(TypedDict):
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

def human_node(state: OrderState) -> OrderState:
    """Display the last model message to the user, and receive the user's input."""
    last_msg = state["messages"][-1]
    print("Model:", last_msg.content)

    user_input = input("User: ")

    # If it looks like the user is trying to quit, flag the conversation
    # as over.
    if user_input in {"q", "quit", "exit", "goodbye"}:
        state["finished"] = True

    return state | {"messages": [("user", user_input)]}


def maybe_exit_human_node(state: OrderState) -> Literal["chatbot", "__end__"]:
    """Route to the chatbot, unless it looks like the user is exiting."""
    if state.get("finished", False):
        return END
    else:
        return "chatbot"

@tool
def fetch_doctors_tool(specialty: str, city: str, max_results: int = 3) -> str:
    """
    Uses Selenium to fetch top doctors for a specialty and city.
    Returns a formatted string with doctor information.
    """
    base_url = "https://www.ratemds.com"
    search_url = f"{base_url}/best-doctors/on/{city}/{specialty}/"
    print(f"Fetching data from: {search_url}")

    # Set up Selenium WebDriver options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # Initialize WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Load the webpage
        driver.get(search_url)

        # Wait for doctor listings to load
        doctor_containers = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "doctor-container"))
        )

        # Extract information about the top doctors
        doctors = []
        for doctor in doctor_containers[:max_results]:
            try:
                name = doctor.find_element(By.CLASS_NAME, "search-item-doctor-name").text
                specialty = doctor.find_element(By.CLASS_NAME, "search-item-specialty-text").text
                
                # Handle location
                try:
                    location = doctor.find_element(By.CLASS_NAME, "doctor-address").text
                except:
                    location = "Location not provided"

                # Handle profile URL
                try:
                    profile_url = doctor.find_element(By.CLASS_NAME, "search-item-doctor-name").get_attribute("href")
                    if not profile_url.startswith("https://"):
                        profile_url = f"https://www.ratemds.com{profile_url}"
                except:
                    profile_url = "No profile URL"

                # Handle rating
                try:
                    rating_element = doctor.find_element(By.CLASS_NAME, "star-rating")
                    rating = rating_element.get_attribute("title")
                except:
                    rating = "No rating"

                # Handle reviews
                try:
                    reviews_element = doctor.find_element(By.CLASS_NAME, "reviews")
                    reviews = reviews_element.text.strip("()")
                except:
                    reviews = "No reviews"

                doctors.append({
                    "name": name,
                    "specialty": specialty,
                    "location": location,
                    "rating": rating,
                    "reviews": reviews,
                    "profile_url": profile_url,
                })
            except Exception as e:
                print(f"Error extracting data: {e}")
                continue

        # If no doctors were found, return a message
        if not doctors:
            return f"No doctors found for the specialty '{specialty}' in {city}."

        # Format the response
        response = f"Top {max_results} {specialty.capitalize()}s in {city.capitalize()}, Ontario:\n"
        for idx, doc in enumerate(doctors, start=1):
            response += (
                f"{idx}. {doc['name']}\n"
                f"   Specialty: {doc['specialty']}\n"
                f"   Location: {doc['location']}\n"
                f"   Rating: {doc['rating']} ({doc['reviews']} reviews)\n"
                f"   Profile: {doc['profile_url']}\n\n"
            )

        return response.strip()

    except Exception as e:
        return f"Error fetching doctors: {e}"

    finally:
        driver.quit()


@tool
def retrieve_reviews_tool(search_url: str) -> str:
    """
    The input is a string containing the url as a stringcorresponding to a doctor's profile to find all the reviews 
    about the doctor on the website combine them and return them as a string
    """
    print(f"Fetching data from: {search_url}")
    # Set up Selenium WebDriver options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")


    # Initialize WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(search_url)
        
        # Wait for at least one rating comment body to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "rating-comment-body"))
        )

        # Small delay to ensure all elements are loaded
        time.sleep(2)

        reviews = []
        # Get all review containers fresh each time
        rating_containers = driver.find_elements(By.CLASS_NAME, "rating-comment-body")

        print(f"Found {len(rating_containers)} review containers")
        
        for i, container in enumerate(rating_containers, 1):

            try:

                # Get the paragraph text from the current container
                review_text = container.find_element(By.TAG_NAME, "p").text
                if review_text:  # Only append non-empty reviews
                    reviews.append(review_text)
                    #print(f"Successfully extracted review {i}") # Implement a counter in the future for a one time less verbose output that mentions how many reviews were retrieved in total.
                else:
                    print(f"Review {i} was empty")
            except Exception as e:
                print(f"Error extracting review {i}: {str(e)}")
                continue

    finally:
        driver.quit()

    # Create formatted string for all_reviews
    all_reviews = "\nExtracted Reviews:\n" + "=" * 50 + "\n"
    for i, review in enumerate(reviews, 1):
        all_reviews += f"Review {i}:\n{review}\n" + "-" * 50 + "\n"
    all_reviews += f"Total reviews extracted: {len(reviews)}"

    return all_reviews


def maybe_route_to_tools(state: OrderState) -> Literal["tools", "human"]:
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

def chatbot_with_tools(state: OrderState) -> OrderState:
    """The chatbot with tools. A simple wrapper around the model's own chat interface."""
    defaults = {"order": [], "finished": False}

    if state["messages"]:
        new_output = llm_with_tools.invoke([Config.SYSINT]+ state["messages"])
    else:
        new_output = AIMessage(content=Config.WELCOME_MSG)

    # Set up some defaults if not already set, then pass through the provided state,
    # overriding only the "messages" field.
    return defaults | state | {"messages": [new_output]}
    
if Config.LLM_MODEL == "gemini-1.5-flash-latest":   
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=os.getenv("GOOGLE_API_KEY"))
# Replace the LLM initialization
# llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=GOOGLE_API_KEY)
elif Config.LLM_MODEL == "ChatBioGPT":
    llm = ChatBioGPT(api_token=HF_API_TOKEN)


# Define a retry policy. The model might make multiple consecutive calls automatically
# for a complex query, this ensures the client retries if it hits quota limits.
retry_policy = {"retry": retry.Retry(predicate=retry.if_transient_error)}
# Define the tools and create a "tools" node.
tools = [fetch_doctors_tool, retrieve_reviews_tool]
tool_node = ToolNode(tools)

# Attach the tools to the model so that it knows what it can call.
llm_with_tools = llm.bind_tools(tools)

graph_builder = StateGraph(OrderState)

# Add the nodes, including the new tool_node.
graph_builder.add_node("chatbot", chatbot_with_tools)
graph_builder.add_node("human", human_node)
graph_builder.add_node("tools", tool_node)

# Chatbot may go to tools, or human.
graph_builder.add_conditional_edges("chatbot", maybe_route_to_tools)
# Human may go back to chatbot, or exit.
graph_builder.add_conditional_edges("human", maybe_exit_human_node)

# Tools always route back to chat afterwards.
graph_builder.add_edge("tools", "chatbot")

graph_builder.add_edge(START, "chatbot")
graph_with_menu = graph_builder.compile()

output = graph_with_menu.invoke({"messages": []})
print('done')


