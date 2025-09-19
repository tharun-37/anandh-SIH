import os
import json
from flask import Flask, render_template
from flask_websockets import WebSockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

# --- CONFIGURATION ---
# The host '0.0.0.0' makes the server accessible on your local network
HOST = '0.0.0.0' 
# The port is read from the environment variable, defaulting to 8765 for local use
PORT = int(os.environ.get('PORT', 8765))

# --- FLASK APP SETUP ---
app = Flask(__name__)
sockets = WebSockets(app)

# A set to store all connected browser clients (websockets)
browser_clients = set()

# --- ROUTES ---
@app.route('/')
def admin_dashboard():
    """Serves the main admin.html page."""
    return render_template('admin.html')

@sockets.route('/')
def websocket_handler(ws):
    """Handles all incoming WebSocket connections (from ESP32s and browsers)."""
    # A simple way to distinguish browsers from ESP32s by their user agent
    user_agent = ws.environ.get('HTTP_USER_AGENT', '').lower()
    is_browser = 'mozilla' in user_agent or 'chrome' in user_agent or 'safari' in user_agent

    if is_browser:
        print("Browser client connected.")
        browser_clients.add(ws)
        try:
            # Keep the connection alive to push data to it
            while not ws.closed:
                ws.receive()
        finally:
            print("Browser client disconnected.")
            browser_clients.remove(ws)
    else:
        # Assume it's an ESP32 device
        print("ESP32 client connected.")
        try:
            while not ws.closed:
                message = ws.receive()
                if message:
                    print(f"Received alert from ESP32: {message}")
                    # Forward the alert message to ALL connected browsers
                    for client in list(browser_clients):
                        try:
                            client.send(message)
                        except Exception:
                            # Clean up broken connections
                            browser_clients.remove(client)
        finally:
            print("ESP32 client disconnected.")

if __name__ == "__main__":
    print(f"🚀 Server starting at http://{HOST}:{PORT}")
    print("Dashboard is available on this computer at http://localhost:8765")
    server = pywsgi.WSGIServer((HOST, PORT), app, handler_class=WebSocketHandler)
    server.serve_forever()