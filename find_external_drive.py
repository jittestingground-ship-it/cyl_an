import os

def find_external_drive():
    media_dir = "/media/kw"
    if os.path.exists(media_dir):
        for entry in os.listdir(media_dir):
            drive_path = os.path.join(media_dir, entry)
            if os.path.ismount(drive_path):
                return drive_path
    # Fallback to BASE_DIR if not found
    return os.path.dirname(os.path.abspath(__file__))

# Usage example:
external_drive_path = find_external_drive()
