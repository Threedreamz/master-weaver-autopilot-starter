#!/usr/bin/env python3
from flask import Flask, request, jsonify
from trello.trello_class import trello_class
import time
import ssl

app = Flask(__name__)


class middleman:
    def __init__(self):
        self.tc = trello_class()

    @app.route('/sstart', methods=['GET'])
    def start_process1():
        print("🔹 /sstart called")
        time.sleep(1)
        return jsonify({
            "status": "ok",
            "message": "Process started",
            "timestamp": int(time.time())
        })

    @app.route("/add_get", methods=['GET'])
    def tc_adderQ():
        tc = trello_class()
        tc.addQueue()
        return jsonify({"status": "ok", "message": "Auftrag hinzugefügt"})

    @app.route("/getAuftrag", methods=['GET'])
    def tc_adder():
        tc = trello_class()
        auftrag = tc.getAuftrag()
        return jsonify({"auftrag": auftrag}), 200
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({"status": "success"}), 200
    @app.route('/add_Auftrag', methods=['POST'])
    def start_process():
        data = request.get_json() or {}
        task_id = data.get('id')
        size = data.get('size')
        auftragsId = data.get('auftragsId')
        status = data.get('status')
        tc = trello_class()
        response = tc.addAuftrag(task_id, auftragsId, size)
        if response is None:
            return jsonify({
                "status": "error",
                "message": "there exists already a queue item",
                "timestamp": int(time.time())
            })
        else:
            print(f"🟨 Start process: id={task_id}, size={size}, auftragsId={auftragsId}")
            return jsonify({
                "status": "ok",
                "message": response,
                "timestamp": int(time.time())
            })

    @app.route('/add', methods=['POST'])
    def add_task():
        data = request.get_json() or {}
        task_id = data.get('id')
        size = data.get('size')

        if not task_id or not size:
            return jsonify({"error": "Missing id or size"}), 400

        print(f"🟩 Received task: id={task_id}, size={size}")
        return jsonify({
            "status": "ok",
            "message": f"Task {task_id} with size {size} added.",
            "timestamp": int(time.time())
        })

    @app.route('/moveToDefect', methods=["POST"])
    def moveToDefect():
        data = request.get_json() or {}
        task_id = data.get('id')
        tc = trello_class()
        auftrag = tc.getAuftrag()
        if auftrag:
            tc.moveToDefect(auftrag['id'])
        queue = tc.getQueue()
        if queue:
            tc.moveToDefect(queue['id'])
        print(f"🟥 Moved task {task_id} to defect")
        return jsonify({
            "status": "ok",
            "message": f"Task {task_id} removed.",
            "timestamp": int(time.time())
        })

    @app.route('/check_online', methods=['GET'])
    def check_online():
        return jsonify({"status": "ok", "message": "online"})


    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    def start(self):
        # HTTPS aktivieren mit Apache-Zertifikaten
        context = (
            '/etc/apache2/ssl/server.crt',
            '/etc/apache2/ssl/server.key'
        )
        print("🔒 HTTPS server running on https://0.0.0.0:5007")
        app.run(host='0.0.0.0', port=5007, ssl_context=context, threaded=True)


