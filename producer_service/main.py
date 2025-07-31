import os
import art # type: ignore
import uuid
import json
import pika
import time
import datetime
from fastapi.responses import JSONResponse, FileResponse
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

# Use local path for file storage
upload_path = "./uploads"
os.makedirs(upload_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

art.tprint("Face Verification API")
print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Face verification master.\n")

@app.post("/api/v1/face/verification", tags=["face"])
async def face_verification(
    file: UploadFile = File(...),
):
    try:
        now = datetime.datetime.now()
        uuid_name = str(uuid.uuid4())
        folder_path = Path(f"{upload_path}/{now:%Y/%m/%d}")
        os.makedirs(folder_path, exist_ok=True)

        if (vr := await validate_file_extension(file.filename)):
            return vr
        file_bytes = file.file.read()
        if (vs := await validate_file_size(file_bytes)):
            return vs
        file.file.seek(0)

        file_ext = file.filename.split('.')[-1]
        file_path = folder_path / f"{uuid_name}.{file_ext}"
        with open(file_path, "wb") as fimg:
            fimg.write(file_bytes)

        mq_client = RabbitMQClient(
            qname=os.getenv("RABBITMQ_QUEUE"),
            rabbitmq_url=os.getenv("RABBITMQ_URL"),
            local=False
        )
        if not mq_client.connect():
            raise ConnectionError("Failed to connect to RabbitMQ")

        request_data = {"file": str(file_path.absolute())}
        metadata = {"request_id": uuid_name, "timestamp": now.isoformat()}
        response = mq_client.call(request_data, metadata)
        data_json = json.loads(response.decode('utf-8'))

        if 'align_face' in data_json:
            af = data_json['align_face'].split('/')
            static_base_url = os.getenv("BASEURL_STATIC")
            data_json['align_face'] = f"{static_base_url}/{'/'.join(af[-4:])}"

        with open(file_path.parent / f"{uuid_name}.json", "w") as f:
            json.dump(data_json, f)
        return JSONResponse(status_code=200, content=data_json)

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if 'mq_client' in locals():
            mq_client.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("API_PORT")), reload=True)