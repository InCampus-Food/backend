import cloudinary
import cloudinary.uploader
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

def upload_image(file_bytes: bytes, folder: str = "incampus") -> str:
    """Upload image ke Cloudinary, return URL-nya."""
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        transformation=[
            {"width": 800, "crop": "limit"},  # max width 800px
            {"quality": "auto"},               # compress otomatis
            {"fetch_format": "auto"}           # format terbaik (webp, dll)
        ]
    )
    return result["secure_url"]

def delete_image(public_id: str) -> None:
    """Hapus gambar dari Cloudinary by public_id."""
    cloudinary.uploader.destroy(public_id)
