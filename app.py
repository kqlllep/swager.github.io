#!/usr/bin/env python3
import os, json, uuid, datetime
from flask import Flask, render_template, request, redirect, url_for, abort, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me")
DATA_FILE = os.environ.get("DATA_FILE", "data.json")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"configs": [], "subs": [], "forum": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    d.setdefault("configs", [])
    d.setdefault("subs", [])
    d.setdefault("forum", [])
    return d

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_iso():
    return datetime.datetime.utcnow().isoformat()

# ---------- ГЛАВНАЯ ----------
@app.route("/")
def index():
    data = load_data()
    top_configs = sorted(data["configs"], key=lambda x: x.get("views", 0), reverse=True)[:10]
    top_subs    = sorted(data["subs"],    key=lambda x: x.get("views", 0), reverse=True)[:10]
    threads     = sorted(data["forum"],   key=lambda x: x.get("created", ""), reverse=True)[:5]
    return render_template("index.html",
        top_configs=top_configs, top_subs=top_subs,
        configs=data["configs"], subs=data["subs"], threads=threads)

# ---------- ПРОСМОТР ----------
@app.route("/c/<cid>")
def view_config(cid):
    data = load_data()
    for c in data["configs"]:
        if c["id"] == cid:
            c["views"] = c.get("views", 0) + 1
            save_data(data)
            return render_template("config_view.html", c=c)
    abort(404)

@app.route("/s/<sid>")
def view_sub(sid):
    data = load_data()
    for s in data["subs"]:
        if s["id"] == sid:
            s["views"] = s.get("views", 0) + 1
            save_data(data)
            return render_template("sub_view.html", s=s)
    abort(404)

# ---------- ПУБЛИКАЦИЯ ----------
@app.route("/publish/config", methods=["POST"])
def publish_config():
    data = load_data()
    title = request.form.get("title", "").strip()
    protocol = request.form.get("protocol", "VLESS").strip()
    payload = request.form.get("payload", "").strip()
    if title and payload:
        data["configs"].append({
            "id": str(uuid.uuid4())[:8],
            "title": title, "protocol": protocol,
            "payload": payload, "views": 0,
        })
        save_data(data)
        flash("Конфиг опубликован", "ok")
    else:
        flash("Заполни название и содержимое", "err")
    return redirect(url_for("index") + "#publish")

@app.route("/publish/sub", methods=["POST"])
def publish_sub():
    data = load_data()
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()
    if title and url:
        data["subs"].append({
            "id": str(uuid.uuid4())[:8],
            "title": title, "url": url, "views": 0,
        })
        save_data(data)
        flash("Подписка опубликована", "ok")
    else:
        flash("Заполни название и URL", "err")
    return redirect(url_for("index") + "#publish")

# ---------- ФОРУМ ----------
@app.route("/forum")
def forum():
    data = load_data()
    threads = sorted(data["forum"], key=lambda x: x.get("created", ""), reverse=True)
    return render_template("forum.html", threads=threads)

@app.route("/forum/new", methods=["POST"])
def forum_new():
    data = load_data()
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    author = request.form.get("author", "").strip() or "Аноним"
    if title and body:
        data["forum"].append({
            "id": str(uuid.uuid4())[:8],
            "title": title, "body": body, "author": author,
            "created": now_iso(), "replies": [],
        })
        save_data(data)
        flash("Тред создан", "ok")
    else:
        flash("Заполни заголовок и текст", "err")
    return redirect(url_for("forum"))

@app.route("/forum/<tid>/reply", methods=["POST"])
def forum_reply(tid):
    data = load_data()
    body = request.form.get("body", "").strip()
    author = request.form.get("author", "").strip() or "Аноним"
    if body:
        for t in data["forum"]:
            if t["id"] == tid:
                t["replies"].append({"author": author, "body": body, "created": now_iso()})
                save_data(data)
                flash("Ответ добавлен", "ok")
                break
    return redirect(url_for("forum"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)