import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def chatwithopenaimodel():
    llm = ChatOpenAI(
        model="gpt-4o-mini", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
    )
    return llm
