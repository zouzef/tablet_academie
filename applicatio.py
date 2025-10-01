from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_wtf.csrf import CSRFProtect
import os
import requests
import json
import threading
import subprocess
import re
import socket
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# Global variable to store app type based on port
app_contexts = {}
# Global session cache to store session data for each room
session_cache = {}

headers = 4

def create_app(port=5000):
    """Create Flask app with port-specific configuration"""
    # Determine app type based on port
    app_type = 'admin' if port == 5000 else 'tablet'
    template_folder = 'dashboard_admin' if port == 5000 else 'dashboard_tablet'
    app = Flask(__name__, template_folder=template_folder)
    app.secret_key = 'your_secret_key_here'
    # Store app context info
    app_contexts[port] = {
        'type': app_type,
        'template_folder': template_folder
    }
    API_URL = "https://www.unistudious.com/api_slc/login_check"
    csrf = CSRFProtect(app)
    # Initialize errors list
    if not app.config.get("ERRORS"):
        app.config["ERRORS"] = []
    # App configuration
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['APP_TYPE'] = app_type
    app.config['PORT'] = port
    # Initialize scheduler for periodic session updates
    scheduler = BackgroundScheduler()
    scheduler.start()
    # Helper functions
    def get_ip_from_arp(mac_address):
        """Get IP address from ARP table using MAC address"""
        try:
            commands = [
                ['arp', '-a'],  # Windows/Linux
                ['ip', 'neigh'],  # Linux
                ['arp', '-an']  # macOS/BSD
            ]
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.lower()
                        for line in lines.split('\n'):
                            if mac_address in line:
                                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                                if ip_match:
                                    return ip_match.group(1)
                    break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
        except Exception as e:
            print(f"Error checking ARP table: {e}")
        return None
    def scan_network_for_mac(mac_address):
        """Scan local network to find device with specific MAC address"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            network_base = '.'.join(local_ip.split('.')[:-1]) + '.'
            print(f"🔍 Scanning network: {network_base}0/24")
            for i in range(1, 255):
                ip = f"{network_base}{i}"
                try:
                    subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                   capture_output=True, timeout=2)
                except:
                    pass
            return get_ip_from_arp(mac_address)
        except Exception as e:
            print(f"Error scanning network: {e}")
            return None
    def get_all_camera(token: str):
        url = "https://www.unistudious.com/slc/get-all-camera"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print("❌ Error fetching cameras:", e)
            return []
        cameras = []
        if isinstance(data, list):
            for cam in data:
                camera = {
                    "id": cam.get("id"),
                    "name": cam.get("name"),
                    "mac": cam.get("mac"),
                    "username": cam.get("username"),
                    "password": cam.get("password"),
                    "status": cam.get("status"),
                    "type": cam.get("type", "ipcam"),
                    "roomId": cam.get("roomId"),
                    "roomName": cam.get("roomName"),
                    "created_at": cam.get("created_at")
                }
                cameras.append(camera)
        else:
            print("❌ Unexpected format from camera API:", data)
        return cameras


    def get_all_rooms(token: str):
        url = "https://www.unistudious.com/slc/get-all-room"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as e:
            print("❌ Error fetching rooms:", e)
            return []
        rooms = []
        if result.get("success") and isinstance(result.get("data"), list):
            for room in result["data"]:
                rooms.append({
                    "id": room.get("id"),
                    "name": room.get("name"),
                    "capacity": room.get("capacity")
                })
        else:
            print("❌ Unexpected format from room API:", result)
        return rooms


    def get_all_sessions(token: str):
        """Fetch all sessions from the remote server"""
        url = "https://www.unistudious.com/slc/get-all-calendar"  # Adjust URL as needed
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print("❌ Error fetching sessions:", e)
            return []
        sessions = []
        if isinstance(data, list):
            sessions = data
        elif isinstance(data, dict) and data.get("success") and isinstance(data.get("data"), list):
            sessions = data["data"]
        else:
            print("❌ Unexpected format from session API:", data)
        return sessions


    def update_session_cache():
        """Update session cache with latest session data"""
        global session_cache
        # Get token from any active session (you might need to adjust this logic)
        token = None
        for app_context in app_contexts.values():
            if hasattr(app_context, 'token'):
                token = app_context.token
                break
        if not token:
            print("❌ No token available for session update")
            return
        try:
            sessions = get_all_sessions(token)
            # Group sessions by room_id
            new_cache = {}
            for session_data in sessions:
                room_id = session_data.get("id_room")
                if room_id:
                    if room_id not in new_cache:
                        new_cache[room_id] = []
                    new_cache[room_id].append(session_data)
            session_cache = new_cache
            print(f"✅ Session cache updated with {len(sessions)} sessions across {len(new_cache)} rooms")
        except Exception as e:
            print(f"❌ Error updating session cache: {e}")
    def get_tablet_room_id():
        """Get room ID for current tablet based on camera MAC address"""
        try:
            # Get network interface MAC address of current device
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            # Get cameras and find matching room
            token = session.get('token')
            if token:
                cameras = get_all_camera(token)
                for camera in cameras:
                    # You might need to implement logic to match current device with camera
                    # This is a simplified example
                    if camera.get("mac"):  # Implement proper matching logic
                        return camera.get("roomId")
        except Exception as e:
            print(f"❌ Error getting tablet room ID: {e}")
        return None
    # Routes
    @app.route('/')
    def root():
        current_port = int(request.host.split(':')[1]) if ':' in request.host else 80
        print(f"🔍 Accessing from port {current_port}")
        if current_port == 5000:
            # Admin: show login page
            return render_template('login.html', app_type=app_type, port=current_port)
        else:
            # Tablet or other ports: show index directly
            room_id = get_tablet_room_id()
            room_sessions = session_cache.get(room_id, []) if room_id else []
            return render_template('index.html',
                                   user=session.get('user', ''),
                                   token=session.get('token', ''),
                                   app_type=app_type,
                                   port=current_port,
                                   room_id=room_id,
                                   sessions=room_sessions)


    @app.route('/login', methods=['POST'])
    def handle_login():
        username = request.form['username']
        password = request.form['password']
        payload = {"username": username, "password": password}
        try:
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                if token:
                    session['user'] = username
                    session['token'] = token
                    # Store token for session updates
                    app_contexts[port]['token'] = token
                    # Start periodic session updates if this is the first login
                    if not scheduler.get_jobs():
                        scheduler.add_job(
                            func=update_session_cache,
                            trigger="interval",
                            seconds=30,  # Update every 30 seconds
                            id='session_update_job'
                        )
                    print(f"✅ Login successful on {app_type} app")
                    return redirect(url_for('index'))
                else:
                    return "❌ Login failed: No token returned", 401
            else:
                return f"❌ Login failed: Status code {response.status_code}", 401
        except Exception as e:
            return f"⚠️ Error connecting to login API: {str(e)}", 500


    @app.route('/check-login', methods=['POST'])
    @csrf.exempt
    def handle_login_json():
        username = request.json.get('username')
        password = request.json.get('password')
        payload = {"username": username, "password": password}
        try:
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                if token:
                    session['user'] = username
                    session['token'] = token
                    # Store token for session updates
                    app_contexts[port]['token'] = token
                    return jsonify({"success": True, "password": password})
                else:
                    return jsonify({"success": False, "message": "No token received"}), 401
            else:
                return jsonify({"success": False, "message": f"Status code {response.status_code}"}), 401
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500


    @app.route('/dashboard', methods=['GET', 'POST'])
    def dashboard():
        if 'user' in session:
            return f"Welcome to the {app_type} dashboard, {session['user']}!"
        else:
            return redirect(url_for('login'))


    @app.route('/index', methods=['GET'])
    def index():
        if 'user' in session:
            print(f"🏠 Index page accessed on {app_type} app (port {port})")
            room_id = None
            room_sessions = []
            if app_type == 'tablet':
                room_id = get_tablet_room_id()
                room_sessions = session_cache.get(room_id, []) if room_id else []
                print(f"📱 Tablet room ID: {room_id}, Sessions: {len(room_sessions)}")
            return render_template('index.html',
                                   user=session['user'],
                                   token=session['token'],
                                   app_type=app_type,
                                   port=port,
                                   room_id=room_id,
                                   sessions=room_sessions)
        else:
            return redirect(url_for('login'))


    # API Routes
    @app.route('/api/cameras', methods=['GET'])
    @csrf.exempt
    def api_get_cameras():
        print(f"🔍 API cameras endpoint called on {app_type} app (port {port})")
        if 'token' not in session:
            print("❌ No token in session")
            return jsonify({'error': 'Unauthorized', 'message': 'No token found'}), 401
        token = session['token']
        print(f"🔑 Using token: {token[:20]}...")
        try:
            cameras = get_all_camera(token)
            print(f"✅ Found {len(cameras)} cameras")
            return jsonify(cameras)
        except Exception as e:
            print(f"❌ Error in api_get_cameras: {str(e)}")
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


    @app.route('/api/rooms', methods=['GET'])
    @csrf.exempt
    def api_get_rooms():
        print(f"📥 /api/rooms called on {app_type} app (port {port})")
        if 'token' not in session:
            print("❌ No token in session")
            return jsonify({'success': False, 'error': 'No token in session'}), 401
        token = session['token']
        print(f"🔐 Token: {token[:20]}...")
        try:
            rooms = get_all_rooms(token)
            return jsonify({"success": True, "rooms": rooms})
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500


    @app.route('/api/sessions', methods=['GET'])
    @csrf.exempt
    def api_get_sessions():
        """Get all sessions or sessions for a specific room"""
        print(f"📥 /api/sessions called on {app_type} app (port {port})")
        if 'token' not in session:
            print("❌ No token in session")
            return jsonify({'success': False, 'error': 'No token in session'}), 401
        room_id = request.args.get('room_id')
        try:
            if room_id:
                # Return sessions for specific room
                room_sessions = session_cache.get(room_id, [])
                return jsonify({
                    "success": True,
                    "sessions": room_sessions,
                    "room_id": room_id,
                    "count": len(room_sessions)
                })
            else:
                # Return all sessions
                return jsonify({
                    "success": True,
                    "sessions": session_cache,
                    "total_rooms": len(session_cache)
                })
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500


    @app.route('/api/tablet-sessions', methods=['GET'])
    @csrf.exempt
    def api_get_tablet_sessions():
        """Get sessions for current tablet's room"""
        print(f"📱 /api/tablet-sessions called on {app_type} app (port {port})")
        if 'token' not in session:
            print("❌ No token in session")
            return jsonify({'success': False, 'error': 'No token in session'}), 401
        try:
            room_id = get_tablet_room_id()
            if room_id:
                room_sessions = session_cache.get(room_id, [])
                return jsonify({
                    "success": True,
                    "room_id": room_id,
                    "sessions": room_sessions,
                    "count": len(room_sessions),
                    "last_updated": datetime.now().isoformat()
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Could not determine tablet room ID"
                })
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500


    @app.route('/api/refresh-sessions', methods=['POST'])
    @csrf.exempt
    def api_refresh_sessions():
        """Manually refresh session cache"""
        print(f"🔄 Manual session refresh requested on {app_type} app (port {port})")
        if 'token' not in session:
            print("❌ No token in session")
            return jsonify({'success': False, 'error': 'No token in session'}), 401
        try:
            update_session_cache()
            return jsonify({
                "success": True,
                "message": "Sessions refreshed successfully",
                "total_rooms": len(session_cache),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"❌ Error refreshing sessions: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500


    @app.route('/api/discover-camera-ip', methods=['POST'])
    @csrf.exempt
    def discover_camera_ip():
        """Discover IP address of a camera using its MAC address"""
        try:
            data = request.get_json()
            mac_address = data.get('mac')
            if not mac_address:
                return jsonify({'success': False, 'error': 'MAC address is required'}), 400
            mac_address = mac_address.lower().replace('-', ':').replace('.', ':')
            print(f"🔍 Searching for IP of MAC: {mac_address}")
            ip_address = get_ip_from_arp(mac_address)
            if not ip_address:
                ip_address = scan_network_for_mac(mac_address)
            if ip_address:
                print(f"✅ Found IP: {ip_address} for MAC: {mac_address}")
                return jsonify({
                    'success': True,
                    'ip_address': ip_address,
                    'mac_address': mac_address
                })
            else:
                print(f"❌ IP not found for MAC: {mac_address}")
                return jsonify({
                    'success': False,
                    'error': 'Camera IP address not found on network'
                }), 404
        except Exception as e:
            print(f"❌ Error discovering IP: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/get-camera-stream', methods=['POST'])
    @csrf.exempt
    def get_camera_stream():
        """Get camera stream URL using discovered IP"""
        try:
            data = request.get_json()
            ip_address = data.get('ip_address')
            username = data.get('username', 'admin')
            password = data.get('password', 'admin')
            if not ip_address:
                return jsonify({'success': False, 'error': 'IP address is required'}), 400
            stream_urls = [
                f"http://{username}:{password}@{ip_address}/video/mjpg.cgi",
                f"http://{username}:{password}@{ip_address}/videostream.cgi",
                f"http://{username}:{password}@{ip_address}/video.cgi",
                f"http://{username}:{password}@{ip_address}/cam/realmonitor?channel=1&subtype=0",
                f"rtsp://{username}:{password}@{ip_address}/cam/realmonitor?channel=1&subtype=0",
                f"http://{ip_address}/video/mjpg.cgi"
            ]
            working_url = None
            for url in stream_urls:
                try:
                    response = requests.get(url.replace('rtsp://', 'http://'), timeout=5)
                    if response.status_code == 200:
                        working_url = url
                        break
                except:
                    continue
            if working_url:
                return jsonify({
                    'success': True,
                    'stream_url': working_url,
                    'ip_address': ip_address
                })
            else:
                return jsonify({
                    'success': True,
                    'stream_url': stream_urls[0],
                    'ip_address': ip_address,
                    'note': 'Using default stream URL pattern'
                })
        except Exception as e:
            print(f"❌ Error getting stream URL: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/slc/get-details', methods=['GET'])
    @csrf.exempt
    def get_scl_details():
        token = session.get('token')
        if not token:
            print("❌ No token in session")
            return jsonify({"error": "Not logged in"}), 401
        url = "https://www.unistudious.com/slc/get-details"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return jsonify(data)
        except requests.RequestException as e:
            print("❌ Error fetching cameras:", e)
            return jsonify({"error": "Failed to fetch cameras"}), 500


    @app.route('/logs')
    def get_logs():
        with open("logs.json", "r") as f:
            logs = json.load(f)
        return jsonify(logs)


    @app.route('/api/server-load-status', methods=['GET'])
    @csrf.exempt
    def get_server_load_status():
        status = app.config.get("SERVER_STATUS", "unknown")
        erreur = app.config.get("ERREUR", "")
        return jsonify({"status": status, "erreur": erreur})


    @app.route('/add-camera', methods=['POST'])
    @csrf.exempt
    def handle_add_camera():
        name = request.form.get('name')
        camera_type = request.form.get('cameraType')
        token = session.get('token')
        room_id = request.form.get('roomName')
        if not token:
            return "Unauthorized: no token found", 401
        ip = ""
        mac = ""
        username = ""
        password = ""
        if camera_type == 'webcam':
            mac = request.form.get('webCamPath')
        elif camera_type == 'ipcam':
            ip = request.form.get('ip')
            mac = request.form.get('mac')
            username = request.form.get('username')
            password = request.form.get('password')
        else:
            return "Invalid camera type", 400
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "name": name,
            "mac": mac,
            "status": "",
            "roomId": room_id,
            "username": username,
            "password": password,
            "type": camera_type,
        }
        add_camera_url = "https://www.unistudious.com/slc/create-camera"
        try:
            response = requests.post(add_camera_url, data=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            print("Response from server:", data)
            if data.get("success"):
                return redirect(url_for('index') + "#camera-section")
            else:
                return f"Failed to add camera: {data.get('message', 'Unknown error')}", 400
        except requests.RequestException as e:
            print(f"Response content: {response.text}")
            return f"Error calling add-camera API: {str(e)}", 500


    @app.route('/api/server-load-report', methods=['POST'])
    @csrf.exempt
    def receive_server_load_status():
        data = request.get_json()
        status = data.get("status")
        erreur = data.get("erreur")
        if status not in ["up", "down"]:
            return jsonify({"success": False, "error": "Invalid status"}), 400
        app.config["SERVER_STATUS"] = status
        if status == "down" and erreur:
            errors = app.config.get("ERRORS", [])
            errors.append(erreur)
            app.config["ERRORS"] = errors
        return jsonify({"success": True, "message": "Status received"})


    @app.route('/api/errors', methods=['GET'])
    @csrf.exempt
    def get_errors():
        errors = app.config.get("ERRORS", [])
        return jsonify({"errors": errors})
    @app.route('/api/server-status', methods=['GET'])
    @csrf.exempt
    def get_server_status():
        status = app.config.get("SERVER_STATUS", "unknown")
        return jsonify({"status": status})


    @app.route('/api/server-report', methods=['POST'])
    @csrf.exempt
    def receive_server_status():
        data = request.get_json()
        status = data.get("status")
        Erreur = data.get("erreur")
        if status not in ["up", "down"]:
            return jsonify({"success": False, "error": "Invalid status"}), 400
        app.config["SERVER_STATUS"] = status
        app.config["Erreur"] = Erreur
        errors = app.config.get("ERRORS", [])
        errors.append(Erreur)
        app.config["ERRORS"] = errors
        print(f"📡 Server reported status: {status}")
        return jsonify({"success": True, "message": "Status received"})


    @app.route('/api/test')
    @csrf.exempt
    def api_test():
        return jsonify({
            'status': 'success',
            'message': f'API is working on {app_type} app!',
            'app_type': app_type,
            'port': port
        })


    @app.route('/api/session-status')
    @csrf.exempt
    def api_session_status():
        return jsonify({
            'logged_in': 'user' in session,
            'has_token': 'token' in session,
            'user': session.get('user', 'Not logged in'),
            'app_type': app_type,
            'port': port
        })


    @app.route('/cameras')
    def cameras():
        if 'token' not in session:
            return redirect(url_for('login'))
        token = session['token']
        cameras = get_all_camera(token)
        return render_template('index.html',
                               cameras=cameras,
                               user=session['user'],
                               token=session['token'],
                               app_type=app_type,
                               port=port)


    @app.route('/logout')
    def logout():
        session.pop('user', None)
        session.pop('token', None)
        return redirect(url_for('login'))


    @app.before_request
    def make_session_permanent():
        session.permanent = True
    return app


def run_app(port):
    """Run Flask app on specific port"""
    app = create_app(port)
    cert_path = os.path.join(os.path.dirname(__file__), 'cert.pem')
    key_path = os.path.join(os.path.dirname(__file__), 'key.pem')
    app_type = 'admin' if port == 5000 else 'tablet'
    print(f"🚀 Starting {app_type} application on port {port}")
    print(f"📁 Using templates from: {'dashboard_admin' if port == 5000 else 'dashboard_tablet'}")
    # Check if SSL certificates exist
    if os.path.exists(cert_path) and os.path.exists(key_path):
        app.run(host='0.0.0.0', port=port, debug=True, ssl_context=(cert_path, key_path), use_reloader=False)
    else:
        print("⚠️  SSL certificates not found, running without HTTPS")
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)


if __name__ == '__main__':
    print("🚀 Starting Multi-Dashboard Application")
    print("=" * 50)
    print("🖥️  Admin Dashboard: https://localhost:5000")
    print("📱 Tablet Dashboard: https://localhost:5001")
    print("=" * 50)
    # Create threads for both applications
    admin_thread = threading.Thread(target=run_app, args=(5000,))
    tablet_thread = threading.Thread(target=run_app, args=(5001,))
    # Start both applications
    admin_thread.daemon = True
    tablet_thread.daemon = True
    admin_thread.start()
    tablet_thread.start()
    print("✅ Both applications started!")
    print("Press Ctrl+C to stop both applications")
    try:
        # Keep main thread alive
        admin_thread.join()
        tablet_thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Stopping applications...")
        print("👋 Goodbye!")