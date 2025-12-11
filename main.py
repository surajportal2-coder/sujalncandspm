from flask import Flask, render_template, request, jsonify
from instagrapi import Client
import threading
import time
import random
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sujal_hawk_ajax_2025"

state = {"running": False, "sent": 0, "logs": [], "start_time": None}
cfg = {"thread_id": "", "messages": [], "delay": 12, "cycle": 35, "break": 40, "threads": 3, "group_name": "", "sessionid": ""}

clients = []

def log(msg):
    entry = f"[{time.strftime('%H:%M:%S')}] {msg}"
    state["logs"].append(entry)
    if len(state["logs"]) > 500:
        state["logs"] = state["logs"][-500:]

def bomber(cl, tid, msgs):
    local = 0
    while state["running"]:
        try:
            msg = random.choice(msgs)
            cl.direct_send(msg, thread_ids=[tid])
            local += 1
            state["sent"] += 1
            log(f"Sent #{state['sent']} → {msg[:40]}")

            if state["sent"] % cfg["cycle"] == 0 and cfg["group_name"]:
                new_name = f"{cfg['group_name']} → {datetime.now().strftime('%I:%M:%S %p')}"
                cl.direct_thread_update_title(tid, new_name)
                log(f"Group name changed → {new_name}")

            if local % cfg["cycle"] == 0:
                time.sleep(cfg["break"])
            time.sleep(cfg["delay"] + random.uniform(-2, 3))
        except:
            time.sleep(20)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    global state
    state["running"] = False
    time.sleep(1)
    state = {"running": True, "sent": 0, "logs": ["BOMBING STARTED"], "start_time": time.time()}
    clients.clear()

    cfg["sessionid"] = request.form.get("sessionid", "").strip()
    cfg["thread_id"] = int(request.form["thread_id"])
    cfg["messages"] = [m.strip() for m in request.form["messages"].split("\n") if m.strip()]
    cfg["group_name"] = request.form.get("group_name", "")
    cfg["delay"] = float(request.form.get("delay", 12))
    cfg["cycle"] = int(request.form.get("cycle", 35))
    cfg["break"] = int(request.form.get("break", 40))
    cfg["threads"] = int(request.form.get("threads", 3))

    for i in range(cfg["threads"]):
        try:
            cl = Client()
            cl.delay_range = [8, 30]
            cl.login_by_sessionid(cfg["sessionid"])
            clients.append(cl)
            threading.Thread(target=bomber, args=(cl, cfg["thread_id"], cfg["messages"]), daemon=True).start()
            log(f"Thread {i+1} → Login SUCCESS")
        except Exception as e:
            log(f"Thread {i+1} Failed → {str(e)[:60]}")

    return jsonify({"status": "started"})

@app.route('/stop')
def stop():
    state["running"] = False
    log("STOPPED BY USER")
    return jsonify({"status": "stopped"})

@app.route('/status')
def status():
    uptime = "00:00:00"
    if state.get("start_time"):
        t = int(time.time() - state["start_time"])
        h, r = divmod(t, 3600)
        m, s = divmod(r, 60)
        uptime = f"{h:02d}:{m:02d}:{s:02d}"
    return jsonify({
        "running": state["running"],
        "sent": state["sent"],
        "uptime": uptime,
        "logs": state["logs"][-100:]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
