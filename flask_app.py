from flask import Flask, render_template, request, send_from_directory
import json
import os
import yt_dlp
import threading
import time
import requests

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
TEXT_COUNTER_FILE = "download_count.txt"
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbxdf5P-F1nTmDx63V3zyOddTUjR60dpBivsNwT--hFxZy1LyXeXY2f8jOP1_hDiNAZyog/exec"

# إنشاء المجلد وملف العد إذا لم يكن موجودًا
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
if not os.path.exists(TEXT_COUNTER_FILE):
    with open(TEXT_COUNTER_FILE, "w") as f:
        f.write("0")

def increase_local_counter():
    with open(TEXT_COUNTER_FILE, "r") as f:
        count = int(f.read().strip())
    count += 1
    with open(TEXT_COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

def send_to_google_sheet():
    try:
        requests.get(GOOGLE_SHEET_URL)
    except Exception as e:
        print(f"Failed to send to Google Sheet: {e}")

def cleanup_download_folder(age_seconds=300):
    """يحذف الملفات الأقدم من 5 دقائق"""
    while True:
        now = time.time()
        for filename in os.listdir(DOWNLOAD_FOLDER):
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > age_seconds:
                    try:
                        os.remove(filepath)
                        print(f"Deleted old file: {filepath}")
                    except Exception as e:
                        print(f"Error deleting file {filepath}: {e}")
        time.sleep(60)

cleanup_thread = threading.Thread(target=cleanup_download_folder, daemon=True)
cleanup_thread.start()

@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    filename = ""
    total_downloads = 0

    with open(TEXT_COUNTER_FILE, "r") as f:
        total_downloads = int(f.read().strip())

    if request.method == "POST":
        url = request.form.get("tiktok_url").strip()
        if not url:
            error = "Please enter a TikTok video URL."
        else:
            try:
                ydl_opts = {
                    'format': 'mp4',
                    'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(id)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_id = info.get('id')
                    ext = info.get('ext', 'mp4')
                    filename = f"{video_id}.{ext}"

                increase_local_counter()
                send_to_google_sheet()

                with open(TEXT_COUNTER_FILE, "r") as f:
                    total_downloads = int(f.read().strip())

            except Exception as e:
                error = f"Download failed: {str(e)}"

    return render_template("index.html", error=error, filepath=filename, total=total_downloads)

@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

if __name__ == "__main__":
    app.run(debug=True)
