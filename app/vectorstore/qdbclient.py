import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")


def get_qdrant_store():
    vector_store = QdrantVectorStore.from_texts(
        ["init text"],
        embedding=embeddings_model,
        url="http://qdrant:6333",
        collection_name="documents",
    )
    return vector_store


def retriever_qdrant_store():
    retriever = QdrantVectorStore.from_existing_collection(
        url="http://qdrant:6333",
        collection_name="documents",
        embedding=embeddings_model,
    )
    return retriever
