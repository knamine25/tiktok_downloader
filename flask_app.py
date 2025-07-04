from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import yt_dlp
import threading
import time

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Global in-memory counter
download_counter = 0

def cleanup_download_folder(age_seconds=300):
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
    global download_counter
    error = ""
    filename = ""

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

                # Increase the in-memory counter
                download_counter += 1

            except Exception as e:
                error = f"Download failed: {str(e)}"

    return render_template("index.html", error=error, filepath=filename, total=download_counter)

@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route("/increase_download", methods=["POST"])
def increase_download():
    global download_counter
    download_counter += 1
    return jsonify({"total": download_counter})

@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

if __name__ == "__main__":
    app.run(debug=True)
