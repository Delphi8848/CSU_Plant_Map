from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime
import uuid
import json

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

if not DATA_FILE.exists():
    DATA_FILE.write_text("[]", encoding="utf-8")


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/plants", methods=["GET"])
def get_plants():
    campus_id = request.args.get("campus_id")
    data = load_data()
    if campus_id:
        data = [x for x in data if x.get("campus_id") == campus_id]
    return jsonify(data)


@app.route("/api/plants", methods=["POST"])
def add_plant():
    name = request.form.get("name", "").strip()
    desc = request.form.get("desc", "").strip()
    lng = request.form.get("lng", "").strip()
    lat = request.form.get("lat", "").strip()
    campus_id = request.form.get("campus_id", "").strip()
    campus_name = request.form.get("campus_name", "").strip()
    category = request.form.get("category", "").strip()
    recorder = request.form.get("recorder", "").strip()

    if not all([name, lng, lat, campus_id, campus_name, category, recorder]):
        return jsonify({"ok": False, "msg": "缺少必要字段"}), 400

    image_url = ""
    image_filename = ""

    image = request.files.get("image")
    if image and image.filename:
        if not allowed_file(image.filename):
            return jsonify({"ok": False, "msg": "图片格式不支持"}), 400

        ext = image.filename.rsplit(".", 1)[1].lower()
        safe_name = secure_filename(image.filename.rsplit(".", 1)[0])
        image_filename = f"{uuid.uuid4().hex}_{safe_name}.{ext}"
        save_path = UPLOAD_DIR / image_filename
        image.save(save_path)
        image_url = f"/static/uploads/{image_filename}"

    item = {
        "id": uuid.uuid4().hex,
        "name": name,
        "desc": desc,
        "lng": float(lng),
        "lat": float(lat),
        "campus_id": campus_id,
        "campus_name": campus_name,
        "category": category,
        "recorder": recorder,
        "image_url": image_url,
        "image_filename": image_filename,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    data = load_data()
    data.append(item)
    save_data(data)

    return jsonify({"ok": True, "item": item})


@app.route("/api/plants/<plant_id>", methods=["DELETE"])
def delete_plant(plant_id):
    data = load_data()
    target = None
    remain = []

    for item in data:
        if item.get("id") == plant_id:
            target = item
        else:
            remain.append(item)

    if target is None:
        return jsonify({"ok": False, "msg": "未找到该植物"}), 404

    image_filename = target.get("image_filename", "")
    if image_filename:
        img_path = UPLOAD_DIR / image_filename
        if img_path.exists():
            try:
                img_path.unlink()
            except Exception:
                pass

    save_data(remain)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)