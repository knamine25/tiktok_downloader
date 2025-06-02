from flask import Flask, render_template, request, send_from_directory
import os
import yt_dlp
import threading
import time
import requests

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"

# رابط Google Apps Script
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdf5P-F1nTmDx63V3zyOddTUjR60dpBivsNwT--hFxZy1LyXeXY2f8jOP1_hDiNAZyog/exec"

# إنشاء مجلد التنزيلات إذا لم يكن موجودًا
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def increase_download_count():
    try:
        requests.post(GOOGLE_SCRIPT_URL)
    except Exception as e:
        print(f"فشل في تحديث Google Sheet: {e}")

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

# تشغيل تنظيف الملفات في الخلفية
cleanup_thread = threading.Thread(target=cleanup_download_folder, daemon=True)
cleanup_thread.start()

@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    filename = ""

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

                # زيادة العداد في Google Sheet
                increase_download_count()

            except Exception as e:
                error = f"Download failed: {str(e)}"

    return render_template("index.html", error=error, filepath=filename)

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
