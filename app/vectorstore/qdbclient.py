from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore


def get_qdrant_store():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = QdrantVectorStore.from_texts(
        ["init text"],
        embedding=embeddings,
        url="http://qdrant:6333", 
        collection_name="documents",
    )
    return vector_store
