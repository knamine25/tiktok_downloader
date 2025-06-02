from flask import Flask, render_template, request, send_from_directory
import os
import yt_dlp
import threading
import time
import sqlite3

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
DB_FILE = "downloads.db"

# إنشاء مجلد التنزيلات إذا لم يكن موجودًا
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# تهيئة قاعدة البيانات وإنشاء جدول العداد إذا لم يكن موجودًا
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS counter (
            id INTEGER PRIMARY KEY,
            total_downloads INTEGER NOT NULL
        )
    ''')
    # إدخال صف عداد واحد إذا غير موجود
    c.execute('INSERT OR IGNORE INTO counter (id, total_downloads) VALUES (1, 0)')
    conn.commit()
    conn.close()

# زيادة عدد التنزيلات في قاعدة البيانات
def increase_download_count():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE counter SET total_downloads = total_downloads + 1 WHERE id = 1')
    conn.commit()
    conn.close()

# قراءة عدد التنزيلات من قاعدة البيانات
def get_download_count():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT total_downloads FROM counter WHERE id = 1')
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

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

# تهيئة قاعدة البيانات قبل بدء السيرفر
init_db()

# بدء تشغيل التنظيف في خلفية البرنامج
cleanup_thread = threading.Thread(target=cleanup_download_folder, daemon=True)
cleanup_thread.start()

@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    filename = ""
    total_downloads = get_download_count()

    if request.method == "POST":
        url = request.form.get("tiktok_url", "").strip()
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
                total_downloads = get_download_count()

            except Exception as e:
                error = f"Download failed: {str(e)}"

    return render_template("index.html", error=error, filepath=filename, total=total_downloads)

@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

# ملفات السيو
@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

if __name__ == "__main__":
    app.run(debug=True)
