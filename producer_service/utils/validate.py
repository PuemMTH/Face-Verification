from fastapi.responses import JSONResponse
from typing import Union
import os

async def validate_file_extension(filename: str) -> Union[JSONResponse, None]:
    """Validate file extension."""
    if filename.split('.')[-1].lower() not in ['jpg', 'jpeg', 'png']:
        return JSONResponse(content={
            'status': 'error',
            'message': "Invalid file type. Use 'jpg', 'jpeg', or 'png'"
        }, status_code=400)
    return None

async def validate_file_size(contents: bytes) -> Union[JSONResponse, None]:
    """Validate file size (2MB limit)."""
    if len(contents) > 2 * 1024 * 1024:
        return JSONResponse(content={
            'status': 'error',
            'message': "File size too large. Maximum file size is 2MB"
        }, status_code=400)
    return None

async def save_image(UPLOAD_DIR: str, contents: bytes, user_id: str, file_name: str) -> None:
    """Save image to disk."""
    image_path = UPLOAD_DIR / user_id / file_name
    os.makedirs(UPLOAD_DIR / user_id, exist_ok=True)
    with open(image_path, 'wb') as f:
        f.write(contents)