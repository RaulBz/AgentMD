# mainFastAPI.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from config import Config
from typing import Literal
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# FastAPI app setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Tool definitions
@tool
def fetch_doctors_tool(specialty: str, city: str, max_results: int = Config.DOCTOR_FETCH_MAX_RESULTS) -> str:
    """
    Uses Selenium to fetch top doctors for a specialty and city.
    Returns a formatted string with doctor information.
    """
    base_url = Config.DOCTOR_SEARCH_URL.rsplit("/search/", 1)[0]
    search_url = f"{base_url}/best-doctors/on/{city.lower()}/{specialty.lower()}/"
    print(f"Fetching data from: {search_url}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(search_url)
        doctor_containers = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "doctor-container"))
        )
        doctors = []
        for doctor in doctor_containers[:max_results]:
            try:
                name = doctor.find_element(By.CLASS_NAME, "search-item-doctor-name").text
                specialty = doctor.find_element(By.CLASS_NAME, "search-item-specialty-text").text
                location = doctor.find_element(By.CLASS_NAME, "doctor-address").text if doctor.find_elements(By.CLASS_NAME, "doctor-address") else "Location not provided"
                profile_url = doctor.find_element(By.CLASS_NAME, "search-item-doctor-name").get_attribute("href")
                if not profile_url.startswith("https://"):
                    profile_url = f"https://www.ratemds.com{profile_url}"
                rating = doctor.find_element(By.CLASS_NAME, "star-rating").get_attribute("title") if doctor.find_elements(By.CLASS_NAME, "star-rating") else "No rating"
                reviews = doctor.find_element(By.CLASS_NAME, "reviews").text.strip("()") if doctor.find_elements(By.CLASS_NAME, "reviews") else "No reviews"
                doctors.append({"name": name, "specialty": specialty, "location": location, "rating": rating, "reviews": reviews, "profile_url": profile_url})
            except Exception as e:
                print(f"Error extracting doctor: {e}")
                continue
        if not doctors:
            return f"No doctors found for '{specialty}' in {city}."
        response = f"Top {max_results} {specialty.capitalize()}s in {city.capitalize()}, Ontario:\n"
        for idx, doc in enumerate(doctors, 1):
            response += f"{idx}. {doc['name']}\n   Specialty: {doc['specialty']}\n   Location: {doc['location']}\n   Rating: {doc['rating']} ({doc['reviews']} reviews)\n   Profile: {doc['profile_url']}\n\n"
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
    print(f"Fetching reviews from: {search_url}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(search_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "rating-comment-body")))
        time.sleep(2)
        reviews = []
        rating_containers = driver.find_elements(By.CLASS_NAME, "rating-comment-body")
        for i, container in enumerate(rating_containers, 1):
            try:
                review_text = container.find_element(By.TAG_NAME, "p").text
                if review_text:
                    reviews.append(review_text)
            except Exception as e:
                print(f"Error extracting review {i}: {e}")
        all_reviews = "Extracted Reviews:\n" + "=" * 50 + "\n"
        for i, review in enumerate(reviews, 1):
            all_reviews += f"Review {i}:\n{review}\n" + "-" * 50 + "\n"
        all_reviews += f"Total reviews extracted: {len(reviews)}"
        return all_reviews
    except Exception as e:
        return f"Error fetching reviews: {e}"
    finally:
        driver.quit()

# LLM setup (supports ChatBioGPT or Gemini)
class ChatBioGPT:
    def __init__(self, api_token, model="microsoft/biogpt"):
        self.url = f"https://api-inference.huggingface.co/models/{model}"
        self.headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
        self.tools = None

    def invoke(self, messages):
        prompt = ""
        for msg in messages:
            if isinstance(msg, tuple) and msg[0] == "system":
                prompt += f"System: {msg[1]}\n"
            elif isinstance(msg, tuple) and msg[0] == "user":
                prompt += f"User: {msg[1]}\n"
            elif hasattr(msg, "content"):
                prompt += f"{msg.content}\n"
        payload = {"inputs": prompt, "parameters": {"max_length": 200, "temperature": 0.7}}
        response = requests.post(self.url, headers=self.headers, json=payload)
        if response.status_code == 200:
            text = response.json()[0]["generated_text"]
            return AIMessage(content=text)
        return AIMessage(content=f"Error: API call failed ({response.status_code})")

    def bind_tools(self, tools):
        self.tools = tools
        return self

if Config.LLM_MODEL == "gemini-1.5-flash-latest":
    llm = ChatGoogleGenerativeAI(model=Config.LLM_MODEL, google_api_key=GOOGLE_API_KEY)
elif Config.LLM_MODEL == "ChatBioGPT":
    if not HF_API_TOKEN:
        raise ValueError("HF_API_TOKEN not found in .env file")
    llm = ChatBioGPT(api_token=HF_API_TOKEN)

tools = [fetch_doctors_tool, retrieve_reviews_tool]
llm_with_tools = llm.bind_tools(tools)

# State definition
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
    order: list[str]
    finished: bool

# Graph nodes
def chatbot_with_tools(state: ChatState) -> ChatState:
    """The chatbot with tools. A simple wrapper around the model's own chat interface."""
    defaults = {"order": [], "finished": False}
    if not state["messages"]:
        new_output = AIMessage(content=Config.WELCOME_MSG)
    else:
        sys_message = SystemMessage(content=Config.SYSINT[1])
        messages = [sys_message] + state["messages"]
        new_output = llm_with_tools.invoke(messages)
    return defaults | state | {"messages": state["messages"] + [new_output]}

tool_node = ToolNode(tools)

# Routing logic
def maybe_route_to_tools(state: ChatState) -> Literal["tools", "__end__"]:
    """Route between human or tool nodes, depending if a tool call is made."""
    if not (msgs := state.get("messages", [])):
        raise ValueError("No messages found in state")
    msg = msgs[-1]
    if hasattr(msg, "tool_calls") and len(msg.tool_calls) > 0:
        return "tools"
    return END

# Graph setup
graph_builder = StateGraph(ChatState)
graph_builder.add_node("chatbot", chatbot_with_tools)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", maybe_route_to_tools)
graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()

# In-memory state (simplified session management)
chat_sessions = {}

# FastAPI endpoints
@app.get("/", response_class=HTMLResponse)
async def get_chat(request: Request):
    session_id = request.cookies.get("session_id", "default")
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {"messages": [], "order": [], "finished": False}
    state = chat_sessions[session_id]
    if not state["messages"]:
        state = graph.invoke(state)
        chat_sessions[session_id] = state
    messages = [(msg.type, msg.content) for msg in state["messages"]]
    return templates.TemplateResponse("index.html", {"request": request, "messages": messages})

import logging

# Add this near the top of mainFastAPI.py, after imports, if not already present
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace the existing @app.post("/chat") with this
@app.post("/chat", response_class=HTMLResponse)
async def post_chat(request: Request, message: str = Form(...)):
    session_id = request.cookies.get("session_id", "default")
    logger.info(f"POST /chat - Session ID: {session_id}, Received message: {message}")
    
    # Initialize session if it doesn't exist
    if session_id not in chat_sessions:
        logger.info(f"Initializing new session for {session_id}")
        chat_sessions[session_id] = {"messages": [], "order": [], "finished": False}
    
    state = chat_sessions[session_id]
    logger.info(f"Current state before processing: {state}")
    
    try:
        if message.lower() in {"quit", "exit", "q"}:
            state["finished"] = True
            chat_sessions[session_id] = state
            messages = [(msg.type, msg.content) for msg in state["messages"]] + [("ai", "Goodbye.")]
            logger.info(f"User quit - Final messages: {messages}")
        else:
            state["messages"].append(HumanMessage(content=message))
            logger.info(f"Invoking graph with updated state: {state}")
            output = graph.invoke(state)
            chat_sessions[session_id] = output
            messages = [(msg.type, msg.content) for msg in output["messages"]]
            logger.info(f"Graph output - Updated messages: {messages}")
        
        # Render the template with the messages
        return templates.TemplateResponse("index.html", {"request": request, "messages": messages})
    
    except Exception as e:
        logger.error(f"Error in post_chat: {str(e)}")
        messages = [(msg.type, msg.content) for msg in state["messages"]] + [("ai", f"Error: {str(e)}")]
        return templates.TemplateResponse("index.html", {"request": request, "messages": messages})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)