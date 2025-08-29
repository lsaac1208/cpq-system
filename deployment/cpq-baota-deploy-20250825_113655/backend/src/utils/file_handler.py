#!/usr/bin/env python3
"""
File handling utilities for CPQ system
Handles image uploads, validation, compression, and storage
"""

import os
import uuid
import hashlib
import mimetypes
from datetime import datetime
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
from flask import current_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileHandler:
    """Handle file uploads and processing for CPQ system"""
    
    # Allowed file extensions and MIME types
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 
        'image/webp', 'image/gif'
    }
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
    
    # Image processing settings
    MAX_IMAGE_WIDTH = 1200
    MAX_IMAGE_HEIGHT = 1200
    THUMBNAIL_SIZE = (300, 300)
    JPEG_QUALITY = 85
    
    def __init__(self, upload_folder=None):
        """Initialize FileHandler with upload folder"""
        if upload_folder:
            self.upload_folder = upload_folder
        else:
            # Use consistent path regardless of context
            try:
                # First try to get app instance path
                app_instance_path = current_app.instance_path
                self.upload_folder = os.path.join(app_instance_path, 'uploads', 'products')
            except RuntimeError:
                # Fallback: use project root uploads folder
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                self.upload_folder = os.path.join(project_root, 'uploads', 'products')
        
        # Ensure upload folder exists
        self._ensure_upload_folder()
    
    def _ensure_upload_folder(self):
        """Ensure upload folder and subdirectories exist"""
        try:
            os.makedirs(self.upload_folder, exist_ok=True)
            
            # Create subdirectories for organization
            subdirs = ['originals', 'thumbnails', 'compressed']
            for subdir in subdirs:
                os.makedirs(
                    os.path.join(self.upload_folder, subdir), 
                    exist_ok=True
                )
            
            logger.info(f"Upload folder initialized: {self.upload_folder}")
            
        except OSError as e:
            logger.error(f"Failed to create upload folder: {e}")
            raise
    
    def is_allowed_file(self, filename, mimetype=None):
        """Check if file is allowed based on extension and MIME type"""
        if not filename:
            return False
        
        # Check file extension
        file_ext = filename.rsplit('.', 1)[-1].lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return False
        
        # Check MIME type if provided
        if mimetype and mimetype not in self.ALLOWED_MIME_TYPES:
            return False
        
        return True
    
    def validate_file(self, file_data, filename, mimetype=None):
        """Validate uploaded file"""
        errors = []
        
        # Check if file exists
        if not file_data:
            errors.append("No file provided")
            return False, errors
        
        # Check file size
        if len(file_data) > self.MAX_FILE_SIZE:
            errors.append(f"File size exceeds {self.MAX_FILE_SIZE / (1024*1024):.1f}MB limit")
        
        # Check file type
        if not self.is_allowed_file(filename, mimetype):
            errors.append("File type not allowed. Supported: " + ", ".join(self.ALLOWED_EXTENSIONS))
        
        # Validate image format by trying to open it
        try:
            from io import BytesIO
            if isinstance(file_data, bytes):
                image_buffer = BytesIO(file_data)
            else:
                image_buffer = file_data
            
            with Image.open(image_buffer) as img:
                # Verify the image is valid
                img.verify()
            
            # Reset buffer position for next use
            if hasattr(image_buffer, 'seek'):
                image_buffer.seek(0)
                
        except Exception as e:
            logger.error(f"Image validation failed for {filename}: {str(e)}")
            errors.append(f"Invalid or corrupted image file: {str(e)}")
        
        if errors:
            logger.warning(f"File validation failed for {filename}: {', '.join(errors)}")
            return False, errors
        
        logger.info(f"File validation successful for {filename}")
        return True, []
    
    def generate_secure_filename(self, original_filename):
        """Generate a secure, unique filename"""
        # Get file extension
        ext = original_filename.rsplit('.', 1)[-1].lower()
        
        # Generate unique identifier
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create secure filename
        secure_name = f"{timestamp}_{unique_id}.{ext}"
        return secure_name
    
    def optimize_image(self, image_data, filename):
        """Optimize image for web use"""
        try:
            # Open image
            with Image.open(image_data) as img:
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Auto-rotate based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Resize if too large
                if img.width > self.MAX_IMAGE_WIDTH or img.height > self.MAX_IMAGE_HEIGHT:
                    img.thumbnail((self.MAX_IMAGE_WIDTH, self.MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                
                # Save optimized image
                from io import BytesIO
                output = BytesIO()
                
                # Determine format
                file_ext = filename.rsplit('.', 1)[-1].lower()
                if file_ext in ['jpg', 'jpeg']:
                    img.save(output, 'JPEG', quality=self.JPEG_QUALITY, optimize=True)
                elif file_ext == 'png':
                    img.save(output, 'PNG', optimize=True)
                elif file_ext == 'webp':
                    img.save(output, 'WEBP', quality=self.JPEG_QUALITY, optimize=True)
                else:
                    # Default to JPEG for other formats
                    filename = filename.rsplit('.', 1)[0] + '.jpg'
                    img.save(output, 'JPEG', quality=self.JPEG_QUALITY, optimize=True)
                
                output.seek(0)
                return output.getvalue(), filename
                
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            raise ValueError(f"Failed to process image: {e}")
    
    def create_thumbnail(self, image_data, filename):
        """Create thumbnail version of image"""
        try:
            with Image.open(image_data) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Auto-rotate based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Create thumbnail
                img.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                from io import BytesIO
                output = BytesIO()
                
                # Always save thumbnails as JPEG for consistency
                thumb_filename = filename.rsplit('.', 1)[0] + '_thumb.jpg'
                img.save(output, 'JPEG', quality=80, optimize=True)
                output.seek(0)
                
                return output.getvalue(), thumb_filename
                
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            raise ValueError(f"Failed to create thumbnail: {e}")
    
    def save_file(self, file_data, filename, subdir='originals'):
        """Save file to upload directory"""
        try:
            file_path = os.path.join(self.upload_folder, subdir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise
    
    def delete_file(self, filename, subdir='originals'):
        """Delete file from upload directory"""
        try:
            file_path = os.path.join(self.upload_folder, subdir, filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def process_upload(self, file_data, original_filename, mimetype=None):
        """Complete file upload processing pipeline"""
        # Step 1: Validate file
        is_valid, errors = self.validate_file(file_data, original_filename, mimetype)
        if not is_valid:
            return {
                'success': False,
                'errors': errors
            }
        
        try:
            # Step 2: Generate secure filename
            secure_filename = self.generate_secure_filename(original_filename)
            
            # Step 3: Optimize image
            from io import BytesIO
            optimized_data, optimized_filename = self.optimize_image(
                BytesIO(file_data), secure_filename
            )
            
            # Step 4: Create thumbnail
            thumbnail_data, thumbnail_filename = self.create_thumbnail(
                BytesIO(optimized_data), optimized_filename
            )
            
            # Step 5: Save files
            # Save original (for backup)
            self.save_file(file_data, secure_filename, 'originals')
            
            # Save optimized version
            optimized_path = self.save_file(optimized_data, optimized_filename, 'compressed')
            
            # Save thumbnail
            self.save_file(thumbnail_data, thumbnail_filename, 'thumbnails')
            
            # Step 6: Generate URLs (API-relative paths for proper routing)
            image_url = f"/api/v1/products/uploads/{optimized_filename}"
            thumbnail_url = f"/api/v1/products/uploads/{thumbnail_filename}"
            
            return {
                'success': True,
                'image_url': image_url,
                'thumbnail_url': thumbnail_url,
                'filename': optimized_filename,
                'thumbnail_filename': thumbnail_filename,
                'file_size': len(optimized_data),
                'original_filename': original_filename
            }
            
        except Exception as e:
            logger.error(f"File processing failed: {e}")
            return {
                'success': False,
                'errors': [f"File processing failed: {str(e)}"]
            }
    
    def cleanup_old_files(self, old_filename):
        """Clean up old files when updating images"""
        if not old_filename:
            return
        
        # Extract base filename (without path and extension)
        base_filename = os.path.splitext(os.path.basename(old_filename))[0]
        
        # Try to delete from all subdirectories
        subdirs = ['originals', 'compressed', 'thumbnails']
        
        for subdir in subdirs:
            subdir_path = os.path.join(self.upload_folder, subdir)
            
            if os.path.exists(subdir_path):
                # Find files that match the pattern
                for filename in os.listdir(subdir_path):
                    file_base = os.path.splitext(filename)[0]
                    
                    # Match original filename or thumbnail pattern
                    if (file_base == base_filename or 
                        file_base == f"{base_filename}_thumb"):
                        
                        file_path = os.path.join(subdir_path, filename)
                        try:
                            os.remove(file_path)
                            logger.info(f"Cleaned up old file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to clean up file {file_path}: {e}")

# Convenience function for easy import
def create_file_handler(upload_folder=None):
    """Factory function to create FileHandler instance"""
    return FileHandler(upload_folder)