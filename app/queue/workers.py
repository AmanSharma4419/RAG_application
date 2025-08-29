from app.db.mongo import files_collection
from bson import ObjectId
from openai import OpenAI
from dotenv import load_dotenv
import fitz
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)
content = """
You are a Resume Roast Assistant.
Your role is to analyze a given resume and generate a brutally honest, witty,
and sarcastic roast about the candidate's skills, experience, and presentation.
Your roast should be sharp, funny, and slightly exaggerated — but avoid being
offensive, discriminatory, or inappropriate.

⚡️ Output Rules:
1. Always return the roast in **HTML format**.
2. Use <h1>, <h2>, <div class="roast">, and <p> tags for structured sections.
3. Highlight different parts of the resume like: Summary, Skills, Experience,
Education, Projects, Soft Skills, and Conclusion.
4. Use light red or pink styled divs (`class="roast"`) for roast sections,
making it look like a "burn card".
5. Keep it humorous, witty, and engaging while still readable.
6. End with a playful conclusion roast.

Make sure the HTML is clean, valid, and can be rendered directly in a browser.
"""


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def chat_with_openai(filepath: str):
    """Send extracted resume text to OpenAI for roasting."""
    try:
        file_content = extract_text_from_pdf(filepath)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": content
                },
                {"role": "user", "content": file_content},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return None, str(e)


def process_file(id: str):
    print("Processing file id:", id)
    file_doc = files_collection.find_one({"_id": ObjectId(id)})
    if not file_doc:
        print(f" File not found for id {id}")
        return {"error": f"File not found for id {id}"}

    filename = file_doc["filename"]
    filepath = f"/mnt/uploads/{id}/{filename}"  
    loader = PyPDFLoader(filepath)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
    chunk_overlap=100)
    splits = text_splitter.split_documents(documents)
    print(f"Total chunks: {len(splits)}")

    if not os.path.exists(filepath):
        print(f"File does not exist on disk: {filepath}")
        return {"error": f"File not found on disk: {filepath}"}

    print(f"Found file: {filepath}")

    try:
        roasted_reply = chat_with_openai(filepath)

        if not roasted_reply:
            raise Exception("OpenAI did not return a reply.")

        # ✅ Update MongoDB with roasted reply and status
        files_collection.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "status": "roasted",
                    "response": roasted_reply
                }
            }
        )

        print(f"🔥 Roasted reply saved for file {id}")
        return {"status": "roasted", "reply": roasted_reply}

    except Exception as e:
        print(f"Error while roasting: {e}")
        files_collection.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "status": "error",
                    "error": str(e)
                }
            }
        )
        return {"error": str(e)}
