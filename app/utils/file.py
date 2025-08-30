import os
import aiofiles
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


async def save_to_disk(file: bytes, path: str) -> bool:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    async with aiofiles.open(path, "wb") as out_file:
        await out_file.write(file)

    return True


async def make_vector_embedding(input: str):
    loader = PyPDFLoader(input)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    return chunks
