from flask import Flask, render_template, session, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
import json
from datetime import datetime,timedelta
import threading
import time
from errueur_handling import *


app = Flask(__name__, template_folder='templates')
app.secret_key = "your_secret_key"

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NTU2ODY0MzAsImV4cCI6MTc1NjI5MTIzMCwicm9sZXMiOlsiUk9MRV9TTEMiXSwidXNlcm5hbWUiOiJmNDo0ZDozMDplZTpjOToxZCJ9.hlUIduUsgleWFdyAL7waHSl0qkITUSn5qW4VJlLMSG2R5kvKvypgZon8jMSBluOuZKp6k0bofBVtoxbxDoQkkPjM8O_uqjuGPra4A_0EZVjKUolZMcFYqoMkfFic0WA14_z5z_j28m3zhhT5MkOuhaA-SS2LacvVGMNFrqRVF7Cs-CyniyBfEBtLK63KTNo80k-J7kZysZng8Ff97FDdFYdOPxY4Kz2mrTmWOhwl6E3xQUaNdBCJmpM750Njl-EzWY4Pmz6vurcv9Gy9_jhpaZhJeP6Xl2r0RHwcsx8wpwjaDdxTsvQx0OHDN_tc8Y5l7x5E2hwgIKBcpmFlP_fUhA"

tablet_id_global = None

# Store active connections and their associated rooms
active_connections = {}


def testing_id_tablet(tablet_id, tablette):
    for i in tablette:
        if i["mac"] == tablet_id:
            return True
    return False


def fetch_all_tablets():
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = "https://www.unistudious.com/slc/get-all-tablets"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching tablets: {e}")
        return None


def fetch_attendance():
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = "https://www.unistudious.com/slc/get-all-calendar"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching attendance: {e}")
        return None


def get_room_tablet(id_tablet, tablette):
    for i in tablette:
        if i["mac"] == id_tablet:
            return i["roomId"]
    return None


@app.route('/tablet/<tablet_id>/check_session')
def check_session(tablet_id):
    print(f"DEBUG: Checking session for tablet_id: '{tablet_id}'")  # Debug line
    print(f"DEBUG: tablet_id type: {type(tablet_id)}")  # Debug line

    try:
        tablette = fetch_all_tablets()
        print(f"DEBUG: Fetched tablets: {len(tablette) if tablette else 0}")  # Debug line

        if not testing_id_tablet(tablet_id, tablette):
            print(f"DEBUG: Tablet {tablet_id} not found in registered tablets")  # Debug line
            return jsonify({'status': 'no_session'})

        room = get_room_tablet(tablet_id, tablette)
        print(f"DEBUG: Found room: {room}")  # Debug line

        attendance_calendar = fetch_attendance()
        if not attendance_calendar or "data" not in attendance_calendar:
            print("DEBUG: No attendance calendar data")  # Debug line
            return jsonify({'status': 'no_session'})

        session_room = get_session_room(room, attendance_calendar["data"])
        if not session_room:
            print(f"DEBUG: No session found for room {room}")  # Debug line
            return jsonify({'status': 'no_session'})

        session_start = datetime.strptime(session_room.get("start"), "%Y-%m-%d %H:%M:%S")
        session_end = datetime.strptime(session_room.get("end"), "%Y-%m-%d %H:%M:%S")
        now = datetime.now()

        print(f"DEBUG: Session time check - Start: {session_start}, End: {session_end}, Now: {now}")  # Debug line

        if session_start - timedelta(minutes=5) <= now <= session_end:
            print("DEBUG: Session is active")  # Debug line
            return jsonify({'status': 'active'})

        print("DEBUG: Session is not active")  # Debug line
        return jsonify({'status': 'no_session'})

    except Exception as e:
        error_details = traceback.format_exc()  # Full error traceback
        print(error_details)
        send_error_email(error_details)  # Send email
        return jsonify({'status': 'error', 'message': str(e)}), 500


def get_session_room(room, attendance):

    # Filter sessions for this room
    list_session = [i for i in attendance if i["roomId"] == room]


    if not list_session:

        return None

    # Get current time
    now = datetime.now()


    # Filter out expired sessions (sessions that have already ended)
    active_or_upcoming_sessions = []
    for session in list_session:
        session_start = datetime.strptime(session["start"], "%Y-%m-%d %H:%M:%S")
        session_end = datetime.strptime(session["end"], "%Y-%m-%d %H:%M:%S")

        # Only include sessions that haven't ended yet
        if now <= session_end + timedelta(minutes=5):  # Give 5 minutes grace period
            active_or_upcoming_sessions.append(session)



    if not active_or_upcoming_sessions:

        return None

    # Sort by start time and get the earliest one that hasn't ended
    active_or_upcoming_sessions.sort(key=lambda x: datetime.strptime(x["start"], "%Y-%m-%d %H:%M:%S"))

    # Return the next/current session
    selected_session = active_or_upcoming_sessions[0]
    session_start = datetime.strptime(selected_session["start"], "%Y-%m-%d %H:%M:%S")
    session_end = datetime.strptime(selected_session["end"], "%Y-%m-%d %H:%M:%S")


    return selected_session


def get_calender(id_attendance):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = f"https://www.unistudious.com/slc/get-attendance/{id_attendance}"
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching attendance: {e}")
        return None


def get_attendance(session_id, listt):
    for i in listt:
        if i["id"] == session_id:
            return i
    return None


def change_stutatus(id_attendance):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "status": True
    }
    response = requests.post(f"https://www.unistudious.com/slc/update-attendance-student/{id_attendance}",
                             headers=headers, data=payload)
    response.raise_for_status()
    return response.json()


# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    # Remove from active connections
    if request.sid in active_connections:
        del active_connections[request.sid]


@socketio.on('join_session')
def handle_join_session(data):
    session_id = data.get('session_id')
    tablet_id = data.get('tablet_id')

    if session_id:
        # Join a room based on session ID
        join_room(f'session_{session_id}')
        active_connections[request.sid] = {
            'session_id': session_id,
            'tablet_id': tablet_id,
            'room': f'session_{session_id}'
        }
        print(f'Client {request.sid} joined session {session_id}')
        emit('status', {'message': f'Joined session {session_id}'})


@socketio.on('leave_session')
def handle_leave_session(data):
    session_id = data.get('session_id')
    if session_id:
        leave_room(f'session_{session_id}')
        print(f'Client {request.sid} left session {session_id}')


# Background task to check for updates
def background_attendance_checker():
    send_error_email("server connected successfully")
    """Background task that checks for attendance updates and broadcasts them"""
    previous_data = {}

    while True:
        try:
            # Get all active sessions from connections
            active_sessions = set()
            for conn_data in active_connections.values():
                if 'session_id' in conn_data:
                    active_sessions.add(conn_data['session_id'])

            # Check each active session for updates
            for session_id in active_sessions:
                try:
                    # Fetch current attendance data
                    current_data = get_calender(session_id)

                    if current_data and "attendance" in current_data:
                        attendance_data = current_data["attendance"]

                        # Compare with previous data
                        session_key = f"session_{session_id}"
                        if session_key in previous_data:
                            # Check if data has changed
                            if previous_data[session_key] != attendance_data:
                                print(f"Attendance updated for session {session_id}")
                                # Broadcast update to all clients in this session
                                socketio.emit('attendance_update',
                                              {
                                                  'session_id': session_id,
                                                  'attendance': attendance_data,
                                                  'timestamp': datetime.now().isoformat()
                                              },
                                              room=session_key)

                        # Update previous data
                        previous_data[session_key] = attendance_data

                except Exception as e:
                    print(f"Error checking session {session_id}: {e}")

        except Exception as e:
            print(f"Error in background checker: {e}")

        # Wait before next check (adjust interval as needed)
        time.sleep(5)  # Check every 5 seconds


# Start background task
def start_background_tasks():
    background_thread = threading.Thread(target=background_attendance_checker, daemon=True)
    background_thread.start()


@app.route('/tablet/<tablet_id>')
def tablet_page(tablet_id):

    tablette = fetch_all_tablets()
    if not testing_id_tablet(tablet_id, tablette):
        return render_template("not_found.html", message="Tablet not registered")

    session['tablet_id'] = tablet_id

    # Get room from tablet
    room = get_room_tablet(tablet_id, tablette)

    # Get all scheduled sessions
    attendance_calendar = fetch_attendance()

    if not attendance_calendar or "data" not in attendance_calendar:
        return render_template("no_session.html",
                               message="No sessions found",
                               tablet_id=tablet_id)

    # Find the session for this tablet's room
    session_room = get_session_room(room, attendance_calendar["data"])


    if not session_room:
        return render_template("no_session.html",
                               message="No session for this room",
                               tablet_id=tablet_id)

    # Parse session times
    session_start_str = session_room.get("start")
    session_end_str = session_room.get("end")

    if not session_start_str or not session_end_str:
        return render_template("no_session.html",
                               message="Session time data is missing",
                               tablet_id=tablet_id)
    print(session_room)
    session_start = datetime.strptime(session_start_str, "%Y-%m-%d %H:%M:%S")
    session_end = datetime.strptime(session_end_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()


    # Show session only if current time is within the session duration
    if session_start - timedelta(minutes=5) <= now <= session_end:
        print("DEBUG MAIN ROUTE: Session is active -> rendering index.html")
        # Get room name from tablets data
        room_name = None
        for tablet in tablette:
            if tablet["roomId"] == room:
                room_name = tablet.get("roomName", f"Room {room}")
                break

        return render_template(
            "index.html",
            tablet_id=tablet_id,
            session_info=session_room,
            room_name=room_name or f"Room {room}"
        )

    return render_template("no_session.html",
                           message="No ongoing session at the moment",
                           tablet_id=tablet_id)




@app.route('/attendance/<int:session_id>')
def api_get_attendance(session_id):
    attendance_calendar = fetch_attendance()
    list_attendance = attendance_calendar["data"]
    data = get_attendance(session_id, list_attendance)

    if data:

        return jsonify(data)
    return jsonify([])


@app.route('/calender/<int:session_id>')
def api_get_calender(session_id):
    data = get_calender(session_id)

    if data and "attendance" in data:
        return jsonify(data["attendance"])
    return jsonify([])


@app.route('/add-note/<int:student_id>', methods=['POST'])
def add_note(student_id):
    try:
        data = request.get_json()
        note = data.get('note', '')
        session_id = data.get('session_id')

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Your actual add note implementation here
        # url = f"https://www.unistudious.com/slc/add-note/{student_id}"
        # response = requests.post(url, headers=headers, json={"note": note})
        # response.raise_for_status()

        # Emit real-time update for note addition
        if session_id:
            socketio.emit('note_update', {
                'student_id': student_id,
                'note': note,
                'timestamp': datetime.now().isoformat()
            }, room=f'session_{session_id}')

        return jsonify({"status": "success", "message": "Note added successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/change-stutatus/<int:id_attendance>', methods=['POST'])
def change_status_student(id_attendance):
    try:
        # Get session_id from request to emit update to correct room
        data = request.get_json() or {}
        session_id = data.get('session_id')

        response = change_stutatus(id_attendance)

        # Emit real-time status update
        if session_id:
            socketio.emit('status_update', {
                'attendance_id': id_attendance,
                'new_status': True,
                'timestamp': datetime.now().isoformat()
            }, room=f'session_{session_id}')

        return jsonify(response)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# Manual trigger for testing real-time updates
@app.route('/trigger-update/<int:session_id>')
def trigger_update(session_id):
    """Manual endpoint to trigger updates for testing"""
    socketio.emit('test_update', {
        'message': 'Manual update triggered',
        'session_id': session_id,
        'timestamp': datetime.now().isoformat()
    }, room=f'session_{session_id}')

    return jsonify({"status": "success", "message": "Update triggered"})


if __name__ == "__main__":
    # Start background tasks
    start_background_tasks()

    # Run with SocketIO
    socketio.run(app, host="0.0.0.0", port=5001, debug=True,
                 ssl_context=('cert.pem', 'key.pem'), allow_unsafe_werkzeug=True)