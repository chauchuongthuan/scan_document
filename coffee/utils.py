import boto3
from django.conf import settings
from datetime import datetime
from io import BytesIO
from PIL import Image
import re
import os
from slugify import slugify

class R2Uploader:
    MAX_SIZE = 3 * 1024 * 1024  # 3MB
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
    
    def _validate_file(self, file):
        """Validate file size and type"""
        if file.size > self.MAX_SIZE:
            raise ValueError(f"File size exceeds {self.MAX_SIZE/1024/1024}MB limit")
            
        if file.content_type not in self.ALLOWED_TYPES:
            raise ValueError("Only image files are allowed")
            
        # Basic shell scan
        if b'<?php' in file.read()[:1024]:
            raise ValueError("Potential malicious file detected")
        file.seek(0)
    
    def _convert_to_webp(self, file):
        """Convert image to webp format"""
        try:
            img = Image.open(file)
            if img.format.lower() == 'webp':
                return file
            
            output = BytesIO()
            img.save(output, format='WEBP', quality=85)
            output.seek(0)
            return output
        except Exception as e:
            raise ValueError(f"Image conversion failed: {str(e)}")
    
    def _generate_filename(self, file, folder, function_name):
        """Generate filename in format: {function_name}/{slug}-{datetime}.webp"""
        name = os.path.splitext(file.name)[0]
        slug = slugify(name)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{folder}/{function_name}/{slug}-{timestamp}.webp"
    
    def upload(self, file, folder='uploads', function_name='default', is_media=False):
        """Upload file to R2 with validation and conversion"""
        if not file:
            return None
            
        try:
            self._validate_file(file)
            
            # Convert to webp
            webp_file = self._convert_to_webp(file)
            
            # Generate filename
            if is_media:
                folder = 'media'  # Ghi đè folder thành 'media' nếu là upload media
            filename = self._generate_filename(file, folder, function_name)
            
            # Upload to R2
            self.client.upload_fileobj(
                webp_file,
                settings.R2_BUCKET_NAME,
                filename,
                ExtraArgs={
                    'ContentType': 'image/webp',
                    'ACL': 'public-read',
                }
            )
            
            return f"{settings.R2_PUBLIC_URL}/{filename}"
            
        except Exception as e:
            print(f"R2 upload error: {str(e)}")
            print(f"Bucket: {settings.R2_BUCKET_NAME}")
            print(f"Endpoint: {settings.R2_ENDPOINT_URL}")
            raise e
    
    def delete(self, url):
        """Delete file from R2 using its URL"""
        try:
            key = url.replace(f"{settings.R2_PUBLIC_URL}/", "")
            self.client.delete_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=key
            )
            return True
        except Exception as e:
            print(f"R2 delete error: {str(e)}")
            return False