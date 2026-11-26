import requests
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

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    api_key=GEMINI_API_KEY,
)




@tool("web_search", description="Search the web for information.")
def tool2(query: str) -> Dict[str, Any] | str:
    try:
        return tavily_client.search(query)
    except Exception as e:
        return f"Error: {e}"


@tool(
    "exchange_rate",
    description="Get the latest available USD to MYR exchange rate.",
)
def tool3() -> Dict[str, Any] | str:
    try:
        response = requests.get(
            "https://api.frankfurter.dev/v2/rate/USD/MYR",
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return "Could not retrieve the exchange rate. Please try again later."
    except ValueError:
        return "The exchange-rate API returned an invalid response."


tools = [tool2, tool3]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="You are a helpful assistant."
)

question = HumanMessage(
    content=(
        "What is the current exchange rate from US dollars to Malaysian Ringgit? "
        "Use the exchange_rate tool and include the date of the returned rate."
    )
)

response = agent.invoke({"messages": [question]})

final_message = response["messages"][-1]
print(final_message.text)