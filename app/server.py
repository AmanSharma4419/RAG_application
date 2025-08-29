from fastapi import FastAPI, HTTPException, UploadFile
from .utils.file import save_to_disk
from app.schemas.file import FileSchema
from app.db.mongo import files_collection
from pymongo.errors import PyMongoError
from .queue.q import q
from .queue.workers import process_file
from app.vectorstore.qdbclient import get_qdrant_store

# from fastapi.staticfiles import StaticFiles
from bson import ObjectId

app = FastAPI()
# app.mount("/uploads", StaticFiles(directory="/mnt/uploads"), name="uploads")


@app.get("/")
def hello():
    try:
        vector_store = get_qdrant_store()
        vector_store.add_texts(["Hello my name is aman kumar and im software developer"])
        return {"status": "cool"}
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
        raise HTTPException(status_code=500,
                            detail=f"Database error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Unexpected error: {str(e)}")


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
            "response": file_doc.get("response", None)  # roasted reply if available
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))