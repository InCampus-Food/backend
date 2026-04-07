from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.core.cloudinary import upload_image
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/image")
async def upload_image_endpoint(
    file: UploadFile = File(...),
    folder: str = "campusfood",
    current_user: User = Depends(get_current_user)
):
    # Validasi tipe file
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Format tidak didukung. Gunakan JPEG, PNG, atau WebP.")
    
    # Baca file & validasi ukuran
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(400, "Ukuran file maksimal 5MB.")
    
    # Upload ke Cloudinary
    url = upload_image(file_bytes, folder=folder)
    
    return {"url": url}
