from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from config import get_settings
from provider_errors import safe_provider_error

settings = get_settings()

if not settings.configured:
    raise SystemExit("Please configure Kazu's private API key first.")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    api_key=settings.api_key,
    vertexai=False,
)

llm_with_url = llm.bind_tools([{"url_context": {}}])

URL = "https://blog.google/technology/ai/google-gemini-ai"

chain = llm_with_url | StrOutputParser()

try:
    response = chain.invoke([
        HumanMessage(
            content=f"Write a concise summary of this page: {URL}"
        )
    ])
    print(response)

except Exception as error:
    _, _, message = safe_provider_error(error)
    print(message)