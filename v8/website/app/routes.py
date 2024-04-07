# app/routes.py
from flask import Flask, request, jsonify, render_template, request, redirect, url_for, flash,  stream_with_context, Response, g, session
import time
import json
import requests
from . import app, db
from .models import Device, UserDetail
from functools import wraps

from threading import Lock

most_recent_bpm = 0
most_recent_temp = 0
data_lock = Lock()

API_BASE_URL = 'http://localhost:5500'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'organization_id' not in session:
            return redirect(url_for('register_login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['POST'])
def register():
    data = {
        'name': request.form.get('name'),
        'password': request.form.get('password')
    }
    response = requests.post( API_BASE_URL + '/register', json=data)
    if response.status_code == 201:
        # Assuming registration logs the user in as well
        session['organization_id'] = response.json().get('organization_id')
        return redirect(url_for('index'))
    else:
        return f"Error: {response.json().get('error')}"

@app.route('/login', methods=['POST'])
def login():
    data = {
        'name': request.form.get('name'),
        'password': request.form.get('password')
    }
    response = requests.post(API_BASE_URL +'/login', json=data)
    if response.status_code == 200:
        session['organization_id'] = response.json().get('organization_id')
        return redirect(url_for('index'))
    else:
        return f"Error: {response.json().get('error')}"


@app.route('/')
def index():
    if 'organization_id' in session:
        organization_id = session.get('organization_id')
        try:
            response = requests.get(API_BASE_URL +'/users?organization_id='+ str(organization_id))
            print(response)
            if response.status_code == 200:
                users = response.json()  
                return render_template('index.html', users=users)
            else:
                return render_template('index.html', users={})
        except requests.RequestException as e:
            # Handle request exceptions (e.g., network errors)
            return str(e), 500
    
    else:
        return redirect(url_for('register_login_page'))

@app.route('/register_login')
def register_login_page():
    return render_template('login_portal.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('organization_id', None)
    return redirect(url_for('register_login_page'))

@app.route('/add-device-page')
@login_required
def add_device_page():
    return render_template('add_device.html')

@app.route('/about-us')
def about_us_page():
    return render_template('about_us.html')

@app.route('/add-device', methods=['POST'])
@login_required
def add_device():
    nickname = request.form.get('nickname')
    passkey = request.form.get('passkey')
    organization_id = session.get('organization_id')  # Assuming this is stored in session upon login

    data = {
        'nickname': nickname,
        'passkey': passkey,
        'organization_id': organization_id
    }
    
    # Sending POST request to the associate-device endpoint on the other server
    response = requests.post(API_BASE_URL+'/associate-device', json=data)
    
    if response.status_code == 200:
        flash('Device added successfully!')
    else:
        # Extract error message from response if available
        error_message = response.json().get('error', 'Failed to add device.')
        flash(error_message)
    
    return redirect(url_for('index'))


@app.route('/submit-user-details', methods=['GET'])
@login_required
def submit_user_details():
    organization_id = session.get('organization_id')
    if not organization_id:
        # Assuming there's a page to handle this scenario
        flash('Organization ID not found. Please log in.')
        return redirect(url_for('login'))

    # Make the GET request to the /devices endpoint
    response = requests.get(f'http://localhost:5500/devices?organization_id={organization_id}')
    
    if response.status_code == 200:
        devices = response.json()
        # Filter unassigned devices
        unassigned_devices = [device for device in devices if not device['is_assigned_to_user']]
    else:
        flash('Failed to fetch devices. Please try again.')
        unassigned_devices = []
    
    # Render the submit_user_details.html template with the list of unassigned devices
    return render_template('submit_user_details.html', unassigned_devices=unassigned_devices)
    
@app.route('/add-user', methods=['POST'])
@login_required
def add_user_page():
    # Form data
    username = request.form.get('user_name')
    phone_number = request.form.get('phone_number')
    bpm_upper_threshold = request.form.get('bpm_upper_threshold')
    bpm_lower_threshold = request.form.get('bpm_lower_threshold')
    temperature_upper_threshold = request.form.get('temperature_upper_threshold')
    temperature_lower_threshold = request.form.get('temperature_lower_threshold')
    device_id = request.form.get('device_id')  # Assuming this comes from the form

    organization_id = session.get('organization_id')  # Assuming this is stored in the session

    print(username, organization_id)

    user_data = {
        'organization_id': organization_id,
        'username': username,
        'phone_number': phone_number,
        'bpm_upper_threshold': bpm_upper_threshold,
        'bpm_lower_threshold': bpm_lower_threshold,
        'temperature_upper_threshold': temperature_upper_threshold,
        'temperature_lower_threshold': temperature_lower_threshold,
    }

    # Step 1: Add new user
    response = requests.post(API_BASE_URL+'/add-new-user', json=user_data)
    
    if response.status_code == 201:
        flash('User added successfully!')
        user_id = response.json().get('user_id')
        
        # Step 2: Optionally assign the device to the user
        if device_id:
            assignment_data = {
                'user_id': user_id,
                'device_id': device_id,
            }
            response = requests.post(API_BASE_URL+'/assign-device-to-user', json=assignment_data)
            
            if response.status_code != 200:
                flash('Failed to assign device to user.')
    else:
        error_message = response.json().get('error', 'Failed to add user.')
        flash(error_message)
    
    return redirect(url_for('index'))



def verify_device(ip_address, passkey):
    # This is the endpoint on the ESP32S3 for verification. Adjust as needed.
    device_verification_url = f"http://{ip_address}/verify?passkey={passkey}"
    
    try:
        # Send passkey for verification. Adjust the data sent as per your device's API.
        response = requests.get(device_verification_url, timeout=5)
        if response.status_code == 200 and response.json().get('verified'):
            return True
    except requests.exceptions.RequestException as e:
        # This catches any request errors, including connection failures and timeouts.
        print(f"Request failed: {e}")
    return False


def send_user_data_to_device(ip_address, user_name, phone_number, bpm_upper_threshold, bpm_lower_threshold, temperature_upper_threshold, temperature_lower_threshold):
    print(user_name, phone_number, bpm_upper_threshold, bpm_lower_threshold, temperature_upper_threshold, temperature_lower_threshold)
    device_url = f"http://{ip_address}/receive-user-data"
    data = {
        'userName': user_name,
        'phoneNumber': phone_number,
        'bpmUpperThreshold': bpm_upper_threshold,
        'bpmLowerThreshold': bpm_lower_threshold,
        'tempUpperThreshold': temperature_upper_threshold,
        'tempLowerThreshold': temperature_lower_threshold
    }
    try:
        response = requests.post(device_url, json=data, timeout=5)
        if response.status_code == 200:
            print("Successfully sent user data to the device.")
            return True
        else:
            print("Failed to send user data. Device responded with an error.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to send user data to the device: {e}")
        return False


@app.route('/device/<device_id>', methods=['GET', 'POST'])
@login_required
def device_page(device_id):
    # Fetch the specific device using the device_id
    device = Device.query.get(device_id)
    if device is None:
        flash('Device not found.', 'error')
        return redirect(url_for('index'))
    
     # Check if user details have already been submitted for this device
    user_detail = UserDetail.query.filter_by(device_id=device_id).first()
    if user_detail:
        # If details exist, redirect to the live data page
        return redirect(url_for('live_data_page', device_id=device_id))

    if request.method == 'POST':
        # Process the submitted user details form
        user_name = request.form.get('user_name')
        phone_number = request.form.get('phone_number')
        bpm_upper_threshold = request.form.get('bpm_upper_threshold')
        bpm_lower_threshold = request.form.get('bpm_lower_threshold')
        temperature_upper_threshold = request.form.get('temperature_upper_threshold')
        temperature_lower_threshold = request.form.get('temperature_lower_threshold')

        
        # Attempt to send user data to the device
        success = send_user_data_to_device(device.ip_address, user_name, phone_number, bpm_upper_threshold, bpm_lower_threshold, temperature_upper_threshold, temperature_lower_threshold)
        if success:
            # Save user details to the database only if successful
            new_user_detail = UserDetail(device_id=device.id, 
                                         user_name=user_name, 
                                         phone_number=phone_number,
                                         bpm_upper_threshold=bpm_upper_threshold, 
                                         bpm_lower_threshold=bpm_lower_threshold,
                                         temperature_upper_threshold=temperature_upper_threshold,
                                         temperature_lower_threshold=temperature_lower_threshold)
            
            db.session.add(new_user_detail)
            try:
                db.session.commit()
                flash('User details submitted successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('There was an error saving the user details.', 'error')
                app.logger.error(f'Error: {e}')
        else:
            flash('Failed to send user data to the device.', 'error')

        return redirect(url_for('device_page', device_id=device_id))

    # Render the device page with the device details form
    return render_template('submit_user_details.html', device=device)

@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
def user_page(user_id):
    if request.method == 'POST':
        if 'update_details' in request.form:

            response = requests.post(f'{API_BASE_URL}/update-user-details', json={
                'user_id': user_id,
                'username': request.form['username'],
                'phone_number': request.form['phone_number'],
                'bpm_upper_threshold': request.form['bpm_upper_threshold'],
                'bpm_lower_threshold': request.form['bpm_lower_threshold'],
                'temperature_upper_threshold': request.form['temperature_upper_threshold'],
                'temperature_lower_threshold': request.form['temperature_lower_threshold'],
            })
            flash('Updated successfully' if response.status_code == 200 else 'Update failed', 'info')
        
        elif 'assign_device' in request.form:
            new_device_id = request.form.get('device_id')
            current_device_id = request.form.get('current_device_id')
            
            # Step 1: Unassign the current device if a different device is selected
            if current_device_id and (current_device_id != new_device_id):
                unassign_response = requests.post(f'{API_BASE_URL}/unassign-device/{current_device_id}')
                if unassign_response.status_code == 200:
                    flash('Current device unassigned successfully', 'info')
                else:
                    flash('Failed to unassign current device', 'error')

            # Step 2: Assign the new device if a device was selected
            if new_device_id:
                assign_response = requests.post(f'{API_BASE_URL}/assign-device-to-user', json={'user_id': user_id, 'device_id': new_device_id})
                if assign_response.status_code == 200:
                    flash('Device assigned successfully', 'success')
                else:
                    flash('Failed to assign new device', 'error')
            else:
                flash('No device selected', 'info')

        elif 'unassign_device' in request.form:

            device_id = request.form.get('device_id')
            if device_id:
                response = requests.post(f'{API_BASE_URL}/unassign-device/{device_id}')
                flash('Device unassigned successfully' if response.status_code == 200 else 'Device unassignment failed', 'info')

        elif 'delete_user' in request.form:

            response = requests.delete(f'{API_BASE_URL}/delete-user/{user_id}')
            if response.status_code == 200:
                flash('User deleted successfully', 'info')
                return redirect(url_for('index'))
            else:
                flash('Failed to delete user', 'error')

    user_response = requests.get(f'{API_BASE_URL}/user/{user_id}')
    user = user_response.json() if user_response.ok else None
    devices_response = requests.get(f'{API_BASE_URL}/devices?organization_id={session["organization_id"]}')
    devices = devices_response.json() if devices_response.ok else []

    return render_template('user_page.html', user=user, devices=devices)

@app.route('/device/<device_id>/live-data')
@login_required
def live_data_page(device_id):
    device = Device.query.get(device_id)
    print(device)
    user_detail = UserDetail.query.filter_by(device_id=device_id).first()

    if device is None:
        flash('Device not found.', 'error')
        return redirect(url_for('index'))

    # Logic to fetch live data from the device or database would go here
    bpm = None  # Placeholder for actual BPM data
    temperature = None  # Placeholder for actual temperature data

    return render_template('live_data.html', device=device, user_detail=user_detail, bpm=bpm, temperature=temperature)

@app.route('/device/<device_id>/update-details', methods=['POST'])
@login_required
def update_device_user_details(device_id):
    device = Device.query.get(device_id)
    if device is None:
        flash('Device not found.', 'error')
        return redirect(url_for('index'))

    user_name = request.form.get('user_name')
    phone_number = request.form.get('phone_number')
    bpm_upper_threshold = request.form.get('bpm_upper_threshold')
    bpm_lower_threshold = request.form.get('bpm_lower_threshold')
    temperature_upper_threshold = request.form.get('temperature_upper_threshold')
    temperature_lower_threshold = request.form.get('temperature_lower_threshold')

    # Attempt to send updated user data to the device
    success = send_user_data_to_device(device.ip_address, user_name, phone_number, bpm_upper_threshold, bpm_lower_threshold, temperature_upper_threshold, temperature_lower_threshold)
    if success:
        # Update user details in the database only if successful
        user_detail = UserDetail.query.filter_by(device_id=device_id).first()
        if user_detail:
            user_detail.user_name = user_name
            user_detail.phone_number = phone_number
            user_detail.bpm_lower_threshold = bpm_lower_threshold
            user_detail.bpm_upper_threshold = bpm_upper_threshold
            user_detail.temperature_lower_threshold = temperature_lower_threshold
            user_detail.temperature_upper_threshold = temperature_upper_threshold

            try:
                db.session.commit()
                flash('User details updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('There was an error saving the user details.', 'error')
                app.logger.error(f'Error: {e}')
        else:
            flash('User details not found for this device.', 'error')
    else:
        flash('Failed to send user data to the device.', 'error')

    return redirect(url_for('live_data_page', device_id=device_id))


def stop_publishing_data_to_device(ip_address):
    device_url = f"http://{ip_address}/stop-publishing"
    try:
        response = requests.post(device_url, timeout=5)
        if response.status_code == 200:
            print("Successfully requested the device to stop publishing data.")
            return True
        else:
            print("Failed to request the device to stop publishing data.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to communicate with the device: {e}")
        return False


@app.route('/device/<device_id>/delete', methods=['POST'])
def delete_device(device_id):
    device = Device.query.get(device_id)
    if device is None:
        flash('Device not found.', 'error')
        return redirect(url_for('index'))
    
    # Send request to ESP device to stop publishing data
    stop_publishing_success = stop_publishing_data_to_device(device.ip_address)
    if not stop_publishing_success:
        flash('Failed to stop device from publishing data.', 'error')
        return redirect(url_for('live_data_page', device_id=device_id))

    # If successful, delete device and associated user details
    UserDetail.query.filter_by(device_id=device_id).delete()
    Device.query.filter_by(id=device_id).delete()
    db.session.commit()
    flash('Device and associated user details deleted successfully.', 'success')

    return redirect(url_for('index'))

@app.route('/sendDetails', methods=['POST'])
def receive_details():
    global most_recent_bpm, most_recent_temp
    data = request.get_json()
    bpm = data.get('bpm')
    temp = data.get('temp')

    with data_lock:
        most_recent_bpm = bpm
        most_recent_temp = temp

    # You may want to do something with the data here, like store it in the database
    # For demonstration, just print it
    print('BPM:', most_recent_bpm, 'Temp:', most_recent_temp)
    
    return jsonify({'status': 'success'}), 200


@app.route('/data-stream')
def data_stream():
    def generate():
        while True:
            with data_lock:
                json_data = json.dumps({'bpm': most_recent_bpm, 'temp': most_recent_temp})
            yield f"data:{json_data}\n\n"
            time.sleep(1)
    
    return Response(stream_with_context(generate()), content_type='text/event-stream')
