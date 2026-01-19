import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def save_uploaded_files(user_id, channel_id, uploaded_files):
    """
    Save uploaded files in MEDIA_ROOT/<user_id>/<channel_id>/.
    Automatically renames duplicates with (1), (2), etc.
    Returns a list of dicts with file_name and saved_path.
    """
    saved_files = []

    user_media_dir = os.path.join(settings.MEDIA_ROOT, str(user_id), str(channel_id))
    os.makedirs(user_media_dir, exist_ok=True)

    for file in uploaded_files:
        ext = os.path.splitext(file.name)[1].lower()
        base_name = os.path.splitext(file.name)[0]
        save_name = file.name
        save_path = os.path.join(user_media_dir, save_name)

        # Avoid overwriting existing files
        counter = 1
        while os.path.exists(save_path):
            save_name = f"{base_name}({counter}){ext}"
            save_path = os.path.join(user_media_dir, save_name)
            counter += 1

        # Save the file using Django's storage system
        default_storage.save(save_path, ContentFile(file.read()))

        saved_files.append(
            {
                "original_name": file.name,
                "saved_name": save_name,
                "path": save_path,
            }
        )
        print(f"file process: {saved_files}")

    files = [file.get("saved_name") for file in saved_files if file]

    return files
