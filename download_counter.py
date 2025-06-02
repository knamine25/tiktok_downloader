import json
import threading

COUNT_FILE = "download_count.json"
_lock = threading.Lock()

def init_counter():
    try:
        with open(COUNT_FILE, "r") as f:
            json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(COUNT_FILE, "w") as f:
            json.dump({"total_downloads": 0}, f)

def get_download_count():
    with _lock:
        with open(COUNT_FILE, "r") as f:
            data = json.load(f)
            return data.get("total_downloads", 0)

def increase_download_count():
    with _lock:
        try:
            with open(COUNT_FILE, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"total_downloads": 0}
        data["total_downloads"] = data.get("total_downloads", 0) + 1
        with open(COUNT_FILE, "w") as f:
            json.dump(data, f)
        return data["total_downloads"]

init_counter()
