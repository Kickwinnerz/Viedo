from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

DB = "videos.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    uploader TEXT,
                    upload_time TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER,
                    username TEXT,
                    comment TEXT,
                    time TEXT
                )""")
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM videos ORDER BY id DESC")
    videos = c.fetchall()
    conn.close()
    return render_template("index.html", videos=videos)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        uploader = request.form.get("uploader", "Anonymous")
        file = request.files["video"]

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("INSERT INTO videos (filename, uploader, upload_time) VALUES (?, ?, ?)",
                      (filename, uploader, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()

            return redirect(url_for("index"))
    return render_template("upload.html")

@app.route("/comment/<int:video_id>", methods=["POST"])
def comment(video_id):
    username = request.form.get("username", "Guest")
    comment_text = request.form.get("comment")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO comments (video_id, username, comment, time) VALUES (?, ?, ?, ?)",
              (video_id, username, comment_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))

def get_comments(video_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT username, comment, time FROM comments WHERE video_id=? ORDER BY id DESC", (video_id,))
    comments = c.fetchall()
    conn.close()
    return comments

app.jinja_env.globals.update(get_comments=get_comments)

# Vercel ke liye: sirf app return karna hai
def handler(request, response):

    return app(request, response)
