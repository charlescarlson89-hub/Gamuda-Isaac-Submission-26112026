from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

from config import get_settings
from provider_errors import safe_provider_error

settings = get_settings()

if not settings.configured:
    raise SystemExit("Please configure Kazu's private API key first.")

llm = ChatGoogleGenerativeAI(
    model="gemma-4-26b-a4b-it",
    api_key=settings.api_key,
    vertexai=False,
    temperature=0.0,
    max_tokens=1024,
    timeout=40,
    max_retries=0,
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant. Answer clearly and honestly."
    ),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | llm | StrOutputParser()

history = []

print("Chat started. Type 'quit' or 'exit' to stop.")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() in ("quit", "exit"):
        break

    if not user_input:
        print("Please enter a message.")
        continue

    try:
        response = chain.invoke({
            "input": user_input,
            "history": history,
        })

        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=response))

        print(f"AI: {response}\n")

    except Exception as error:
        _, _, message = safe_provider_error(error)
        print(message)

print("\n--- Conversation history ---")

for message in history:
    speaker = "You" if isinstance(message, HumanMessage) else "AI"
    print(f"{speaker}: {message.content}\n")

print("Chat ended.")