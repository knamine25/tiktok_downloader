from flask import Flask, render_template, request, send_from_directory
import json
import os
import yt_dlp
import threading
import time

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
COUNT_FILE = "download_count.json"

# إنشاء المجلد وملف العد إذا لم يكن موجودًا
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
if not os.path.exists(COUNT_FILE):
    with open(COUNT_FILE, "w") as f:
        json.dump({"total_downloads": 0}, f)

# قفل لمنع تعارض القراءة والكتابة على ملف العد
count_lock = threading.Lock()

def increase_download_count():
    with count_lock:
        try:
            with open(COUNT_FILE, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"total_downloads": 0}

        data["total_downloads"] = data.get("total_downloads", 0) + 1

        with open(COUNT_FILE, "w") as f:
            json.dump(data, f)

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

# بدء تشغيل التنظيف في خلفية البرنامج
cleanup_thread = threading.Thread(target=cleanup_download_folder, daemon=True)
cleanup_thread.start()

@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    filename = ""
    total_downloads = 0

    # قراءة عدد التحميلات مع قفل لمنع تعارض في حالة وجود طلبات كثيرة
    with count_lock:
        try:
            with open(COUNT_FILE, "r") as f:
                total_downloads = json.load(f).get("total_downloads", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            total_downloads = 0

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

                increase_download_count()

                # إعادة قراءة عدد التحميلات بعد التحديث
                with count_lock:
                    with open(COUNT_FILE, "r") as f:
                        total_downloads = json.load(f).get("total_downloads", 0)

            except Exception as e:
                error = f"Download failed: {str(e)}"

    return render_template("index.html", error=error, filepath=filename, total=total_downloads)

@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

# إضافة خدمة ملفات السيو
@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

if __name__ == "__main__":
    app.run(debug=True)
