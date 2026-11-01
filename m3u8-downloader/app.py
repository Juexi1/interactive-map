import os
import subprocess
import threading
from urllib.parse import urlparse
from flask import Flask, Response, render_template, request, jsonify

app = Flask(__name__)
DEFAULT_URL = "https://vip.dytt-kan.com/20250608/505_e8c0653f/index.m3u8"
ALLOWED_HOST = "vip.dytt-kan.com"
ACTIVE = threading.BoundedSemaphore(2)

@app.get("/")
def home():
    return render_template("index.html", default_url=DEFAULT_URL)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/download")
def download():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST
        or parsed.username or parsed.password or parsed.port not in (None, 443)
        or not parsed.path.lower().endswith(".m3u8")):
        return jsonify(error="仅允许指定来源的 HTTPS M3U8 地址"), 400
    if not ACTIVE.acquire(blocking=False):
        return jsonify(error="下载任务已满，请稍后重试"), 429
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
           "-rw_timeout", "15000000", "-i", url,
           "-map", "0:v:0?", "-map", "0:a:0?", "-c", "copy",
           "-movflags", "frag_keyframe+empty_moov", "-f", "mp4", "pipe:1"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    except Exception as e:
        ACTIVE.release()
        return jsonify(error="无法启动 FFmpeg: " + str(e)), 500
    def stream():
        try:
            while True:
                chunk = proc.stdout.read(131072)
                if not chunk:
                    break
                yield chunk
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            ACTIVE.release()
    return Response(stream(), mimetype="video/mp4", headers={
        "Content-Disposition": 'attachment; filename="video.mp4"',
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"
    })
