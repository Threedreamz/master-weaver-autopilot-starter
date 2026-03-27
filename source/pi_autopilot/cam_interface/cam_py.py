#!/usr/bin/env python3
import threading
import sys
import cv2
from flask import Flask, Response
from picamera2 import Picamera2

class cam_py:
    def __init__(self, host="0.0.0.0", http_port=8443, https_port=8080,
                 cert="/etc/apache2/ssl/server.crt",
                 key="/etc/apache2/ssl/server.key"):
 
        self.host = host
        self.http_port = http_port
        self.https_port = https_port
        self.cert = cert
        self.key = key
        self.is_https = False

        self.app = Flask(__name__)

        # NICHTS initialisieren! Kamera erst bei start()
        self.cam = None
        self.server_thread = None
        self.routes_initialized = False

    # ------------------------------------------------------------
    # ROUTES EINRICHTEN (einmalig)
    # ------------------------------------------------------------
    def _init_routes(self):
        if self.routes_initialized:
            return
        
        @self.app.route("/")
        def capture_image():
            if self.cam is None:
                return "Camera not started", 500

            frame = self.cam.capture_array()
            if frame is None:
                return "Frame error", 500

            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            frame = cv2.bitwise_not(frame)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                return "JPEG encoding error", 500

            return Response(buffer.tobytes(), mimetype="image/jpeg")

        @self.app.after_request
        def add_cors_headers(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        
        self.routes_initialized = True

    # ------------------------------------------------------------
    # START SERVER
    # ------------------------------------------------------------
    def start(self, https=False):
        if self.server_thread is not None:
            print("⚠️ Server already running.")
            return

        self.is_https = https

        # Kamera initialisieren
        self.cam = Picamera2()
        config = self.cam.create_preview_configuration(
            main={"size": (640, 480)}
        )
        self.cam.configure(config)
        self.cam.start()

        # Routes initialisieren
        self._init_routes()

        def run_flask():
            if https:
                ctx = (self.cert, self.key)
                print(f"🔒 HTTPS enabled on {self.host}:{self.https_port}")
                self.app.run(host=self.host, port=self.https_port,
                             ssl_context=ctx, threaded=True)
            else:
                print(f"🌐 HTTP enabled on {self.host}:{self.http_port}")
                self.app.run(host=self.host, port=self.http_port,
                             threaded=True)

        self.server_thread = threading.Thread(target=run_flask, daemon=True)
        self.server_thread.start()

    # ------------------------------------------------------------
    # STOP SERVER
    # ------------------------------------------------------------
    def stop(self):
        """
        Flask hat keinen richtigen Stop — wir stoppen jedoch sauber die Kamera.
        """
        print("🛑 Stopping camera server...")

        if self.cam:
            try:
                self.cam.stop()
                print("📷 Camera stopped.")
            except Exception as ex:
                print(ex)

        self.cam = None
        self.server_thread = None
