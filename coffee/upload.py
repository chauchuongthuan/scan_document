import os
import re
import subprocess

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
from django.conf import settings
import os

load_dotenv()


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg','webp', 'gif', 'pdf', 'mp4', 'zip', 'doc', 'docx', 'xlsx'}

def uploadFile(files, paths_cdn):
    print(files)
    if 'file' not in files:
        return 'File bị lỗi'

    elif 'file' in files and files['file']:
        file = files['file']
        if paths_cdn and paths_cdn != '':
            path = paths_cdn.lstrip('/')
        else:
            now = datetime.now()
            year = now.year
            month = now.month
            day = now.day
            path = f"{year}/{month}/{day}"
    else:
        return False

    if file:
        if allowed_file(file.name):
            try:
                cleaned_filename = remove_special_characters(file.name)
                file_path = save_file(file, path)
                if file_path:
                    # Return relative path for URL construction
                    return f"{path}/{cleaned_filename}"
                return False
            except Exception as e:
                print("Error: ", e)
                return False
        else:
            return True
    return False

def pathByDate():
    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day
    return f"{year}/{month}/{day}"

def remove_special_characters(filename):
    pattern = r'[^a-zA-Z0-9_.]'
    cleaned_filename = re.sub(pattern, '', filename)
    return cleaned_filename

def save_file(file, path):
    filename = remove_special_characters(file.name)
    relative_path = os.path.join('uploads', path, filename)
    
    # Create full path
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    try:
        # Save the file
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Return the relative path that can be used in URLs
        return os.path.join(settings.MEDIA_ROOT, relative_path)
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_file(file_path, content_type='image/jpeg'):
    with open(file_path, 'rb') as f:
        image = Image.open(f)
        image_io = BytesIO()
        image.save(image_io, format=image.format)
        image_io.seek(0)

        file_name = os.path.basename(file_path)
        return InMemoryUploadedFile(image_io, None, file_name, content_type, image_io.tell(), None)

def upload_editor_image(file, paths_cdn, absolute_path):
    if file:    
        cleaned_filename = remove_special_characters(os.path.basename(absolute_path))
        relative_path = os.path.join('uploads', paths_cdn, cleaned_filename)
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Save the file
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
                
        return f'/media/{relative_path}'
    return False