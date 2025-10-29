"""Image validation and cleaning utilities."""
from PIL import Image
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def is_valid_image(image_bytes: bytes, min_size: int = 100) -> bool:
    """Validate image bytes.
    
    Args:
        image_bytes: Image data
        min_size: Minimum size in pixels for width or height
        
    Returns:
        True if image is valid
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size
        
        if width < min_size or height < min_size:
            logger.debug(f"Image too small: {width}x{height}")
            return False
        
        # Check if image is valid
        img.verify()
        return True
    except Exception as e:
        logger.debug(f"Invalid image: {e}")
        return False


def normalize_image(image_bytes: bytes, max_size: int = 2048) -> bytes:
    """Normalize image to standard format.
    
    Args:
        image_bytes: Original image data
        max_size: Maximum dimension to resize to
        
    Returns:
        Normalized image bytes
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large
        width, height = img.size
        if width > max_size or height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Save to bytes
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Error normalizing image: {e}")
        return image_bytes

