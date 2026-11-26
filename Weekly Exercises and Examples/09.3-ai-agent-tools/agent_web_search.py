import os
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from typing import Dict, Any

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", 
api_key=GEMINI_API_KEY)


@tool("web_search", description="Search the web for information.")
def tool2(query: str) -> Dict[str, Any] | str:
    try:
        return tavily_client.search(query)
    except Exception as e:
        return f"Error: {e}"
    
    