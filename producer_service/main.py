import os
import art # type: ignore
import uuid
import json
import pika
import time
import datetime
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, Form, File
from utils.validate import validate_file_extension, validate_file_size
from rabbitmq_client import RabbitMQClient
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Face Verification API
app = FastAPI(title="Face Verification API",description="API for face verification",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"],expose_headers=["*"])

baseURL = os.getenv("BASEURL_STATIC", "./uploads")
os.makedirs(baseURL, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

art.tprint("Face Verification API")
print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Face verification master.\n")

@app.post("/api/v1/face/verification", tags=["face"])
async def face_verification(
    file: UploadFile = File(...),
):
    try:
        dd, mm, yyyy = datetime.datetime.now().strftime("%d-%m-%Y").split("-")
        uuid_name = str(uuid.uuid4())
        folder_path = Path(f"{baseURL}/{yyyy}/{mm}/{dd}/{uuid_name}")
        os.makedirs(folder_path, exist_ok=True)

        validation_result = await validate_file_extension(file.filename)
        if validation_result:
            return validation_result
        
        # check size per file
        validate_file = await validate_file_size(file.file.read())
        if validate_file:
            return validate_file
        file.file.seek(0)

        # Save file to disk
        os.makedirs(folder_path, exist_ok=True)
        file_path = folder_path / f"{uuid_name}.{file.filename.split('.')[-1]}"
        with open(file_path, "wb") as original_image:
            original_image.write(file.file.read())

        # Initialize RabbitMQ client with proper parameters
        mq_client = RabbitMQClient(
            qname=os.getenv("RABBITMQ_QUEUE", "face_verification_queue"),
            hostname=os.getenv("RABBITMQ_HOST", "localhost"),
            username=os.getenv("RABBITMQ_USER", "ipu_user"),
            password=os.getenv("RABBITMQ_PASS", "ipu_password"),
            local=False
        )
        
        # Connect to RabbitMQ
        if not mq_client.connect():
            raise ConnectionError("Failed to connect to RabbitMQ")
        
        # Prepare the data for RabbitMQ
        request_data = {"file": str(file_path.absolute())}
        request_id = str(uuid.uuid4())
        metadata = {"request_id": request_id, "timestamp": datetime.datetime.now().isoformat()}
        response = mq_client.call(request_data, metadata)
        with open(f"{file_path.parent}/{request_id}.json", "w") as f:
            f.write(response.decode('utf-8'))
        return JSONResponse(status_code=200,content=json.loads(response.decode('utf-8')))

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if 'mq_client' in locals():
            mq_client.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("API_PORT", 8085)), reload=True)