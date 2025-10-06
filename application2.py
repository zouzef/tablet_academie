# Flask and Socket.IO imports
from flask import Flask, render_template, session, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
import json
from datetime import datetime, timedelta
import threading
import time



from login import *

# ============= Configuration and Initialization =============
def load_config():
    with open("tablet_configuration.json", "r") as f:
        config = json.load(f)
        return config

config = load_config()
app = Flask(__name__, template_folder='templates')
app.secret_key = config["config"]["SECRET_KEY"]
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
token = login_tablet()
base_url = config["url"]["API_BASE_URL"]
active_connections = {}

# ============= Utility Functions =============
def testing_id_tablet(tablet_id, tablette):
    for i in tablette:
        if i["mac"] == tablet_id:
            return True
    return False

def fetch_all_tablets():
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = config["url"]["get_all_tablets"]
    url = f"{base_url}{endpoint}"
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching tablets: {e}")
        return None

def fetch_attendance():
    headers = {"Authorization": f"Bearer {token}"}
    end_point = config["url"]["get_all_calendar"]
    url = f"{base_url}{end_point}"
    try:
        response = requests.get(url, headers=headers, verify=False)
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

def get_session_room(room, attendance):
    list_session = [i for i in attendance if i["roomId"] == room]
    if not list_session:
        return None
    now = datetime.now()
    active_or_upcoming_sessions = []
    for session in list_session:
        try:
            session_start = datetime.strptime(session["start"], "%a, %d %b %Y %H:%M:%S %Z")
            session_end = datetime.strptime(session["end"], "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            try:
                session_start = datetime.strptime(session["start"], "%Y-%m-%d %H:%M:%S")
                session_end = datetime.strptime(session["end"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"DEBUG: Could not parse date format for session: {session['start']}")
                continue

        if now <= session_end + timedelta(minutes=5):
            active_or_upcoming_sessions.append(session)

    if not active_or_upcoming_sessions:
        return None

    active_or_upcoming_sessions.sort(key=lambda x: datetime.strptime(x["start"], "%a, %d %b %Y %H:%M:%S %Z")
    if 'GMT' in x["start"]
    else datetime.strptime(x["start"], "%Y-%m-%d %H:%M:%S"))

    return active_or_upcoming_sessions[0]

def get_calender(id_attendance):
    headers = {"Authorization": f"Bearer {token}"}
    end_point = config["url"]["get_attendance"]
    url = f"{base_url}{end_point}/{id_attendance}"
    try:
        response = requests.get(url, headers=headers, verify=False)
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
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"status": True}
        endpoint2 = config["url"]["update_attendance_student"]
        url2 = f"{base_url}{endpoint2}/{id_attendance}"
        response = requests.post(url2, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"DEBUG: Exception in change_stutatus: {e}")
        emit('status', {'message': f'Failed to change status for attendance {id_attendance}'})

def background_attendance_checker():
    previous_data = {}
    while True:
        try:
            active_sessions = set()
            for conn_data in active_connections.values():
                if 'session_id' in conn_data:
                    active_sessions.add(conn_data['session_id'])
            for session_id in active_sessions:
                try:
                    current_data = get_calender(session_id)
                    if current_data and "attendance" in current_data:
                        attendance_data = current_data["attendance"]
                        session_key = f"session_{session_id}"
                        if session_key in previous_data:
                            if previous_data[session_key] != attendance_data:

                                socketio.emit('attendance_update',
                                            {
                                                'session_id': session_id,
                                                'attendance': attendance_data,
                                                'timestamp': datetime.now().isoformat()
                                            },
                                            room=session_key)
                        previous_data[session_key] = attendance_data
                except Exception as e:
                    print(f"Error checking session {session_id}: {e}")
        except Exception as e:
            print(f"Error in background checker: {e}")
        time.sleep(5)

def start_background_tasks():
    try:

        background_thread = threading.Thread(target=background_attendance_checker, daemon=True)
        background_thread.start()
    except Exception as e:
        print(f"DEBUG: Exception in start_background_tasks: {e}")
        emit('status', {'message': f'Failed to start background tasks'})

# ============= WebSocket Event Handlers =============
@socketio.on('connect')
def handle_connect():
    try:

        print(f'Client connected: {request.sid}')
    except Exception as e:
        print(f"DEBUG: Exception in handle_connect: {e}")
        emit('status', {'message': f'Failed to connect client {request.sid}'})

@socketio.on('disconnect')
def handle_disconnect():
    try:
        print(f'Client disconnected: {request.sid}')
        if request.sid in active_connections:
            del active_connections[request.sid]
    except Exception as e:
        print(f"DEBUG: Exception in handle_disconnect: {e}")
        emit('status', {'message': f'Failed to disconnect client {request.sid}'})

@socketio.on('join_session')
def handle_join_session(data):
    try:
        session_id = data.get('session_id')
        tablet_id = data.get('tablet_id')
        if session_id:
            join_room(f'session_{session_id}')
            active_connections[request.sid] = {
                'session_id': session_id,
                'tablet_id': tablet_id,
                'room': f'session_{session_id}'
            }
            print(f'Client {request.sid} joined session {session_id}')
            emit('status', {'message': f'Joined session {session_id}'})
    except Exception as e:
        print(f"DEBUG: Exception in handle_join_session: {e}")
        emit('status', {'message': f'Failed to join session {session_id}'})


@socketio.on('leave_session')
def handle_leave_session(data):
    try:
        session_id = data.get('session_id')
        if session_id:
            leave_room(f'session_{session_id}')
            print(f'Client {request.sid} left session {session_id}')
    except Exception as e:
        print(f"DEBUG: Exception in handle_leave_session: {e}")
        emit('status', {'message': f'Failed to leave session {session_id}'})

# ============= API Endpoints =============

# ----- Tablet Related Endpoints -----
@app.route('/tablet/<tablet_id>')
def tablet_page(tablet_id):
    try:
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

        try:
            # Try the new format first
            session_start = datetime.strptime(session_start_str, "%a, %d %b %Y %H:%M:%S %Z")
            session_end = datetime.strptime(session_end_str, "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            # Fallback to the original format
            session_start = datetime.strptime(session_start_str, "%Y-%m-%d %H:%M:%S")
            session_end = datetime.strptime(session_end_str, "%Y-%m-%d %H:%M:%S")

        now = datetime.now()
        # Show session only if current time is within the session duration
        if session_start - timedelta(minutes=5) <= now <= session_end:

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
    except Exception as e:
        print(f"DEBUG: Exception in tablet_page: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400



@app.route('/tablet/<tablet_id>/check_session')
def check_session(tablet_id):
    try:
        tablette = fetch_all_tablets()

        if not testing_id_tablet(tablet_id, tablette):

            return jsonify({'status': 'no_session'})

        room = get_room_tablet(tablet_id, tablette)


        attendance_calendar = fetch_attendance()


        if not attendance_calendar or "data" not in attendance_calendar:
            print("DEBUG: No attendance calendar data")
            return jsonify({'status': 'no_session'})

        session_room = get_session_room(room, attendance_calendar["data"])
        if not session_room:
            #print(f"DEBUG: No session found for room {room}")
            return jsonify({'status': 'no_session'})

        # Parse the date strings with the correct format
        try:
            session_start = datetime.strptime(session_room.get("start"), "%a, %d %b %Y %H:%M:%S %Z")
            session_end = datetime.strptime(session_room.get("end"), "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            # Fallback to the original format
            session_start = datetime.strptime(session_room.get("start"), "%Y-%m-%d %H:%M:%S")
            session_end = datetime.strptime(session_room.get("end"), "%Y-%m-%d %H:%M:%S")

        now = datetime.now()


        if session_start - timedelta(minutes=5) <= now <= session_end:

            return jsonify({'status': 'active'})

        print("DEBUG: Session is not active")
        return jsonify({'status': 'no_session'})

    except Exception as e:
        print(f"DEBUG: Exception in check_session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ----- Attendance Related Endpoints -----
@app.route('/attendance/<int:session_id>')
def api_get_attendance(session_id):
    try:

        attendance_calendar = fetch_attendance()
        list_attendance = attendance_calendar["data"]
        data = get_attendance(session_id, list_attendance)
        if data:
            return jsonify(data)
        return jsonify([])

    except Exception as e:
        print(f"DEBUG: Exception in api_get_attendance: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/calender/<int:session_id>')
def api_get_calender(session_id):
    try:
        data = get_calender(session_id)
        if data and "attendance" in data:
            return jsonify(data["attendance"])
        return jsonify([])
    except Exception as e:
        print(f"DEBUG: Exception in api_get_calender: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/add-note/<int:attendance_id>', methods=['POST'])
def add_note(attendance_id):
    try:
        data = request.get_json()
        note = data.get('note', '')
        session_id = data.get('session_id')
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        endpoint3 = config["url"]["update-attendance-note"]
        url3 = f"{base_url}{endpoint3}/{attendance_id}"

        payload = {"note": note}
        response = requests.post(url3, headers=headers, data=json.dumps(payload), verify=False)
        response.raise_for_status()
        if session_id:
            socketio.emit('note_update', {
                'attendance_id': attendance_id,
                'note': note,
                'timestamp': datetime.now().isoformat()
            }, room=f'session_{session_id}')

        return jsonify({"status": "success", "message": "Note added successfully"})
    except Exception as e:
        print(f"DEBUG: Exception in add_note: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/change-stutatus/<int:id_attendance>', methods=['POST'])
def change_status_student(id_attendance):
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        response = change_stutatus(id_attendance)

        if session_id:
            socketio.emit('status_update', {
                'attendance_id': id_attendance,
                'new_status': True,
                'timestamp': datetime.now().isoformat()
            }, room=f'session_{session_id}')
        return jsonify(response)
    except Exception as e:
        print(f"DEBUG: Exception in change_status_student: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


#get statics about attendance
@app.route('/get-statics-attendance/<int:calender_id>')
def get_statics_attendance(calender_id):
    try:
        url=f"{base_url}{config['url']['get_statics_attendance']}/{calender_id}"
        headers={
            "Authorization": f"Bearer {token}"
        }

        response=requests.get(url,headers=headers,verify=False)
        response.raise_for_status()
        print(response.status_code)
        return response.json()

    except Exception as e:
        print(f"DEBUG:Error {e} coming from get_statics_attendance")
        return jsonify({"status":"error","message":str(e)}),500






# ----- Student Management Endpoints -----
@app.route('/api/show-attendance-unknown/<int:calenderId>')
def get_unknown_student(calenderId):
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"https://www.unistudious.com/slc/show-attendance-unknown-student/{calenderId}",headers=headers)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        print(f"DEBUG: Exception in get_unknown_student: {e}")  # Debug line
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/api/get-unknown-student-attendance/<int:calendarId>')
def get_unknown_student_attendance(calendarId):
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"https://www.unistudious.com/slc/get-unknown-student-attendance/{calendarId}",headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"DEBUG: Exception in get_unknown_student_attendance: {e}")  # Debug line
        return jsonify({'status': 'error', 'message': str(e)}), 500


@socketio.on('some_event')
@app.route('/api/add-student-attendance', methods=['POST'])
def add_student_attendance():
    try:
        # Get data from request (JS will send JSON)
        data = request.get_json()
        user_id = data.get('userId')  # required
        calendar_id = data.get('calendarId')  # required
        group_id = data.get('groupId')
        relation_id = data.get('relationId')  # optional
        checkbox1_checked = data.get('checkbox1', False)
        checkbox2_checked = data.get('checkbox2', False)
        selected_group_id = data.get('selectedGroupId')

        # Validate required fields
        if not user_id or not calendar_id:
            return jsonify({"success": False, "error": "userId and calendarId are required"}), 400

        # Initialize variables based on checkbox states
        add_to_group = False
        join_to_group = False
        final_selected_group_id = None
        final_relation_id = None

        # Case 1: Only checkbox2 is checked
        if checkbox2_checked and not checkbox1_checked:
            add_to_group = True
            join_to_group = False  # should be False (empty)
            final_selected_group_id = None  # should be None (empty)
            final_relation_id = relation_id
        # Case 2: Neither checkbox is checked
        elif not checkbox1_checked and not checkbox2_checked:
            add_to_group = False
            join_to_group = False
            final_selected_group_id = None
            final_relation_id = None
        # Case 3: checkbox1 is checked (with or without checkbox2)
        elif checkbox1_checked:
            add_to_group = True
            join_to_group = True
            final_selected_group_id = selected_group_id
            final_relation_id = relation_id

        # Prepare headers and payload for the external API
        headers = {
            "Authorization": f"Bearer {token}",
        }
        payload = {
            "userId": user_id,
            "calendarId": calendar_id,
            "groupId": group_id,
            "relationId": final_relation_id,
            "addToGroup": add_to_group,
            "selectedGroupId": final_selected_group_id,
            "joinToGroup": join_to_group
        }

        # Remove None values from payload to avoid sending null values
        #payload = {k: v for k, v in payload.items() if v is not None}

        # Call the external API
        url = f"{base_url}{config['url']['save_user']}"
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False
        )
        response.raise_for_status()


        if response.json().get('success') == False:
            socketio.emit('status', {'message': 'There is no Place for this student'})

        return jsonify({
            "success": True,
            "message": "Student attendance added successfully",
            "data": response.json()
        })



    except requests.exceptions.HTTPError as e:

        socketio.emit('status', {'message': f'HTTP Error: {str(e)}'}, namespace='/')

    except requests.exceptions.HTTPError as e:
        # ✅ FIXED: Use getattr to safely access response.status_code
        status_code = getattr(e, 'response', None)
        if status_code:
            status_code = status_code.status_code
        else:
            status_code = 500

        return jsonify({
            "success": False,
            "error": str(e),
            "response": e.response.text if hasattr(e, 'response') else None
        }), status_code

    except Exception as e:
        # ✅ FIXED: Don't reference 'response' variable that might not exist
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/delete-unknown-student-attendance', methods=['POST'])
def delete_unknown_student_attendance():
    try:
        data = request.get_json()
        calendarId = data.get('calendarId')  # ✅ matches frontend
        folder = data.get('folder')
        headers = {
            "Authorization": f"Bearer {token}",
        }
        payload = {
            "calendarId": calendarId,  # ✅ consistent spelling
            "folder": folder,
        }
        response = requests.post(
            "https://www.unistudious.com/slc/delete-unknown-student-attendance",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("DEBUG: Exception in delete_unknown_student_attendance:", e)
        return {"error": str(e)}, 500


@app.route('/slc/list-add-student-attendance/<int:calendarId>')
def get_all_student(calendarId):
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        url = f"{base_url}{config['url']['get_list_add_student_attendance']}/{calendarId}"
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()

        # Get the data from the external API
        data = response.json()



        # Make sure the response has the expected structure
        if 'users' not in data:
            print("No 'users' key in response, returning empty array")
            return jsonify({"users": []})


        return jsonify(data)

    except Exception as e:
        print("Error:", e)
        # Return empty users array to avoid breaking the frontend
        return jsonify({"users": []})



@app.route('/slc/attendance-save-user')
def save_user(userId,calenderId,groupId,relationId,addToGroup,selecedGroupId,joinToGroup):
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }

        payload ={
            "userId":userId,
            "calendarId":calenderId,
            "groupId":groupId,
            "relationId":relationId,
            "addToGroup":addToGroup,
            "selectedGroupId":selecedGroupId,
            "joinToGroup":joinToGroup
        }
        response = requests.post("https://www.unistudious.com/slc/attendance-save-user",headers=headers,data=payload)
        response.raise_for_status()


        return response.status_code

    except Exception as e:
        return e



@app.route("/slc/attendance-get-group-student-select/<int:calendarId>/<int:userId>")
def get_current_group(calendarId,userId):
    try:
        headers={
            "Authorization": f"Bearer {token}"
        }
        url=f"{base_url}{config['url']['attendance_get_group_student_select']}/{calendarId}/{userId}"
        response = requests.get(url,headers=headers,verify=False)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print("DEBUG: Exception in get_current_group:",e)
        return 404


#reset all_all_attendance
@app.route("/reset_attendance_api/<int:calander_id>")
def reset_attendance_api(calander_id):
    try:
        url=f"{base_url}{config['url']['reset_attendance_api']}/{calander_id}"
        headers={
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(url,headers=headers,verify=False)
        response.raise_for_status()
        if(response.status_code == 200):
            socketio.emit('reset_attendance', {'message': 'Reset attendance triggered'})
            return jsonify({"status":"success","Message":"success from resert_attendance_api"}),200

    except Exception as e:
        print("DEBUG:Error {e} come from resert_attendance_api")
        return jsonify({"status":"Error","Message":"error from resert_attendance_api"}),300


#delete attendance

@app.route("/delete_attendance_api/<int:calander_id>/<int:user_id>")
def delete_attendance_api(calander_id,user_id):
    try:
        url=f"{base_url}{config['url']['delete_attendance_api']}/{calander_id}/{user_id}"
        print(calander_id,user_id)
        headers={
            "Authorization": f"Bearer {token}"
        }
        response=requests.get(url,headers=headers,verify=False)
        response.raise_for_status()

        if(response.status_code == 200):
            socketio.emit('delete_attendance', {'message': 'Delete attendance triggered'})
            return jsonify({"status":"success","Message":"success from delete_attendance_api"}),200


    except Exception as e:
        print("DEBUG:Error {e} come from delete_attendance_api")
        return jsonify({"status":"Error","Message":"error from delete_attendance_api"}),300







# ----- Testing/Debug Endpoints -----
@app.route('/trigger-update/<int:session_id>')
def trigger_update(session_id):
    socketio.emit('test_update', {
        'message': 'Manual update triggered',
        'session_id': session_id,
        'timestamp': datetime.now().isoformat()
    }, room=f'session_{session_id}')
    return jsonify({"status": "success", "message": "Update triggered"})





# ----- Getting account data Endpoints -----
@app.route('/get-data-account/<int:calander_id>')
def get_data_account(calander_id):
    try:
        url=f"{base_url}{config['url']['get_data_account']}/{calander_id}"
        headers={
            "Authorization": f"Bearer {token}"
        }
        response=requests.get(url,headers=headers,verify=False)
        response.raise_for_status()
        print(response.json())
        if(response.status_code==200):
            return jsonify(response.json())
        else:
            return jsonify({"status": "error"})
    except Exception as e :
        print(f"DEBUG:Error {e} come from get_data_account")
        return jsonify({"status":"Error","Message":"error from get_data_account"}),300







# ============= Main Application Entry =============
if __name__ == "__main__":
    print(token)
    start_background_tasks()
    socketio.run(app,
                host="0.0.0.0",
                port=5010,
                debug=True,
                ssl_context=('cert.pem', 'key.pem'),
                allow_unsafe_werkzeug=True)
