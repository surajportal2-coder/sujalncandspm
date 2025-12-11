from flask import Flask, render_template, request, redirect
from instagrapi import Client
import threading
import time
import random
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sujal_hawk_final_2025"

# Global state
status = {"running": False, "sent": 0, "threads": 0, "logs": [], "text": "Ready"}
cfg = {"thread_id": "", "messages": "", "delay": 12, "cycle": 35, "break": 40, "threads": 3, "group_name": "", "sessionid": ""}

clients = []
workers = []

DEVICES = [
    {"phone_manufacturer": "Google", "phone_model": "Pixel 8 Pro", "android_version": 15, "android_release": "15.0.0", "app_version": "323.0.0.46.109"},
    {"phone_manufacturer": "Samsung", "phone_model": "SM-S928B", "android_version": 15, "android_release": "15.0.0", "app_version": "324.0.0.41.110"},
]

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    status["logs"].append(entry)
    if len(status["logs"]) > 600:
        status["logs"] = status["logs"][-600:]

def bomber(cl, tid, msgs):
    local_sent = 0
    while status["running"]:
        try:
            msg = random.choice(msgs)
            cl.direct_send(msg, thread_ids=[tid])
            local_sent += 1
            status["sent"] += 1
            log(f"Sent #{status['sent']} → {msg[:50]}")

            # Group name change after every cycle
            if status["sent"] % cfg["cycle"] == 0 and cfg["group_name"]:
                new_name = f"{cfg['group_name']} → {datetime.now().strftime('%I:%M:%S %p')}"
                cl.direct_thread_update_title(tid, new_name)
                log(f"Group name changed → {new_name}")

            if local_sent % cfg["cycle"] == 0:
                log(f"Break {cfg['break']}s")
                time.sleep(cfg["break"])

            time.sleep(cfg["delay"] + random.uniform(-2, 3))
        except:
            time.sleep(20)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        status["running"] = False
        time.sleep(2)
        status["logs"].clear()
        status["sent"] = 0
        clients.clear()
        workers.clear()

        cfg["sessionid"] = request.form.get('sessionid', '').strip()
        cfg["thread_id"] = request.form['thread_id']
        cfg["messages"] = request.form['messages']
        cfg["group_name"] = request.form.get('group_name', '')
        cfg["delay"] = float(request.form.get('delay', 12))
        cfg["cycle"] = int(request.form.get('cycle', 35))
        cfg["break"] = int(request.form.get('break', 40))
        cfg["threads"] = int(request.form.get('threads', 3))

        msgs = [m.strip() for m in cfg["messages"].split('\n') if m.strip()]
        tid = int(cfg["thread_id"])

        status["running"] = True
        status["text"] = "BOMBING ACTIVE"
        log("SPAMMER STARTED")

        for i in range(cfg["threads"]):
            cl = Client()
            device = random.choice(DEVICES)
            cl.set_device(device)
            cl.delay_range = [8, 25]
            try:
                cl.login_by_sessionid(cfg["sessionid"])
                clients.append(cl)
                t = threading.Thread(target=bomber, args=(cl, tid, msgs), daemon=True)
                t.start()
                workers.append(t)
                log(f"Thread {i+1} → Login SUCCESS")
            except Exception as e:
                log(f"Thread {i+1} Failed → {str(e)[:80]}")

        status["threads"] = len(clients)
        if not clients:
            status["text"] = "LOGIN FAILED"
            status["running"] = False

    return render_template('index.html', **status, cfg=cfg)

@app.route('/stop')
def stop():
    status["running"] = False
    log("STOPPED BY USER")
    status["text"] = "STOPPED"
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
