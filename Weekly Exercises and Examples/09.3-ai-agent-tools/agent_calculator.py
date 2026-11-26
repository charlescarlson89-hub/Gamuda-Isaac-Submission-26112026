import os
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise SystemExit("GEMINI_API_KEY is missing. Check your .env file.")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    api_key=GEMINI_API_KEY,
)

@tool
def calculate_compound_interest(
    principal: float,
    annual_rate_percent: float,
    years: int,
) -> str:
    """Calculate compound interest with annual compounding.

    principal: Initial investment amount.
    annual_rate_percent: Annual percentage rate, such as 8 for 8%.
    years: Number of whole years invested.
    """
    if not (0 <= principal <= 1_000_000_000):
        return "Principal must be between 0 and 1 billion."

    if not (0 <= annual_rate_percent <= 100):
        return "Annual rate must be between 0% and 100%."

    if not (0 <= years <= 100):
        return "Years must be between 0 and 100."

    amount = principal * (1 + annual_rate_percent / 100) ** years
    interest = amount - principal

    return (
        f"Final amount: {amount:.2f}. "
        f"Interest earned: {interest:.2f}."
    )

agent = create_agent(
    model=llm,
    tools=[calculate_compound_interest],
    system_prompt=(
        "You are a helpful assistant. "
        "Use the calculate_compound_interest tool for compound-interest "
        "questions, and base your answer on its result. "
        "Keep your answer short."
    ),
)

question = HumanMessage(
    content=(
        "What's the result of an investment of $10,000 "
        "growing at 8% annually for 5 years with compound interest?"
    )
)

response = agent.invoke({"messages": [question]})

for message in response["messages"]:
    if message.type == "tool":
        print("Tool result:", message.content)

final_message = response["messages"][-1]
print("AI:", final_message.text)