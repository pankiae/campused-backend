import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def save_uploaded_files(user_id, channel_id, uploaded_files):
    """
    Save uploaded files in MEDIA_ROOT/<user_id>/<channel_id>/.
    Automatically renames duplicates with (1), (2), etc.
    Returns a list of saved file names (same as original function).
    """
    saved_files = []

    # Absolute directory on disk (kept so other parts of your app can read files from disk)
    user_media_dir_abs = os.path.join(
        settings.MEDIA_ROOT, str(user_id), str(channel_id)
    )
    os.makedirs(user_media_dir_abs, exist_ok=True)

    # Relative folder inside storage (used when calling default_storage.save)
    relative_folder = os.path.join(str(user_id), str(channel_id))

    for uploaded in uploaded_files:
        # Strip any client-side path components (prevents traversal attempts)
        original_name = os.path.basename(uploaded.name)

        # Split name and ext (preserve original naming behavior)
        base_name, ext = os.path.splitext(original_name)
        save_name = original_name

        # Use filesystem check against the absolute folder to keep your (1), (2) naming
        candidate_abs_path = os.path.join(user_media_dir_abs, save_name)
        counter = 1
        while os.path.exists(candidate_abs_path):
            save_name = f"{base_name}({counter}){ext}"
            candidate_abs_path = os.path.join(user_media_dir_abs, save_name)
            counter += 1

        # Build relative storage path (no leading slash)
        rel_path = os.path.join(relative_folder, save_name).lstrip("/\\")

        # Save using default_storage with RELATIVE name (this is the fix)
        default_storage.save(rel_path, ContentFile(uploaded.read()))

        # Keep returned "path" as absolute on-disk path (matches original function)
        saved_files.append(
            {
                "original_name": original_name,
                "saved_name": save_name,
                "path": candidate_abs_path,  # absolute filesystem path (for backward compatibility)
            }
        )

        # optional debug
        print(f"file process: {saved_files}")

    # Return list of saved file-names (same shape as your original function)
    files = [fobj.get("saved_name") for fobj in saved_files if fobj]
    return files
