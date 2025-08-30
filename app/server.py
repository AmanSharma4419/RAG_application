from fastapi import FastAPI, HTTPException, UploadFile

from app.utils.openai_calls import chatwithopenaimodel
from .utils.file import save_to_disk
from app.schemas.file import FileSchema
from app.db.mongo import files_collection
from pymongo.errors import PyMongoError
from .queue.q import q
from .queue.workers import process_file
from app.vectorstore.qdbclient import retriever_qdrant_store
from pydantic import BaseModel
from bson import ObjectId


class FeedbackRequest(BaseModel):
    input: str


app = FastAPI()
# app.mount("/uploads", StaticFiles(directory="/mnt/uploads"), name="uploads")


@app.get("/")
def hello():
    try:
        return {"status": "cool server is running"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/upload")
async def upload_file(file: UploadFile):
    try:
        file_doc = FileSchema(
            filename=file.filename,
            status="queued",
        )

        result = files_collection.insert_one(file_doc.model_dump())

        filepath = f"/mnt/uploads/{result.inserted_id}/{file.filename}"

        # Save file to disk
        await save_to_disk(file=await file.read(), path=filepath)

        # Queue the file
        q.enqueue(process_file, str(result.inserted_id))
        return {"file_id": str(result.inserted_id)}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/status/{file_id}")
async def get_status(file_id: str):
    try:
        file_doc = files_collection.find_one({"_id": ObjectId(file_id)})
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")

        # Convert ObjectId to string for JSON response
        file_doc["_id"] = str(file_doc["_id"])
        return {
            "file_id": file_doc["_id"],
            "status": file_doc.get("status", "unknown"),
            "response": file_doc.get("response", None),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def get_feedback(request: FeedbackRequest):
    try:
        retriever = retriever_qdrant_store()
        results = retriever.similarity_search(request.input, k=3)
        context = "\n\n".join([doc.page_content for doc in results])
        prompt = f"""
        You are a professional career coach.
        The user uploaded their resume, and here are the most
        relevant sections:

        {context}

        The user asked: "{request.input}"

        Give clear, constructive, and practical feedback to improve this
        section of their resume.
        """
        llm = chatwithopenaimodel()
        response = llm.invoke(prompt)
        return {
            "user_query": request.input,
            "feedback": response.content,
        }
    except Exception as e:
        return {"error": str(e)}
