# main.py
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import ChatBioGPT, fetch_doctors_tool, retrieve_reviews_tool
from graph import build_graph
from config import Config
from google.api_core import retry

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# LLM setup
if Config.LLM_MODEL == "gemini-1.5-flash-latest":
    llm = ChatGoogleGenerativeAI(model=Config.LLM_MODEL, google_api_key=GOOGLE_API_KEY)
elif Config.LLM_MODEL == "ChatBioGPT":
    if not HF_API_TOKEN:
        raise ValueError("HF_API_TOKEN not found in .env file")
    llm = ChatBioGPT(api_token=HF_API_TOKEN)

tools = [fetch_doctors_tool, retrieve_reviews_tool]
llm_with_tools = llm.bind_tools(tools)

retry_policy = {"retry": retry.Retry(predicate=retry.if_transient_error)}

graph = build_graph(llm_with_tools)

output = graph.invoke({"messages": []})