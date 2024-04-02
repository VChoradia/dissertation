# app/routes.py
from flask import Flask, request, jsonify, render_template, request, redirect, url_for, flash,  stream_with_context, Response, g
import time
import json
import requests
from . import app, db
from .models import Device, UserDetail

from threading import Lock

most_recent_bpm = 0
most_recent_temp = 0
data_lock = Lock()


@app.route('/')
def index():
    devices = Device.query.all()
    return render_template('index.html', devices=devices)

@app.route('/add-device-page')
def add_device_page():
    return render_template('add_device.html')

@app.route('/add-device', methods=['POST'])
def add_device():
    ip_address = request.form.get('ip')
    passkey = request.form.get('passkey')
    nickname = request.form.get('nickname')
    
    if verify_device(ip_address, passkey):
        new_device = Device(ip_address=ip_address, passkey=passkey, nickname=nickname)
        db.session.add(new_device)
        try:
            db.session.commit()
            flash('Device added successfully!')
        except Exception as e:
            db.session.rollback()
            flash('Failed to add device. It might already exist.')
            print(e)  # For debugging
        return redirect(url_for('index'))
    else:
        flash('Failed to connect to device')
        return redirect(url_for('add_device_page'))


@app.route('/submit-user-details', methods=['POST'])
def submit_user_details():
    ip_address = request.json.get('deviceIp')
    user_name = request.json.get('userName')
    phone_number = request.json.get('phoneNumber')
    bpm_upper_threshold = request.form.get('bpm_upper_threshold')
    bpm_lower_threshold = request.form.get('bpm_lower_threshold')
    temperature_upper_threshold = request.form.get('temperature_upper_threshold')
    temperature_lower_threshold = request.form.get('temperature_lower_threshold')

    device = Device.query.filter_by(ip_address=ip_address).first()
    if device:
        user_detail = UserDetail(user_name=user_name, 
                                 phone_number=phone_number, 
                                 device_id=device.id, 
                                 bpm_upper_threshold=bpm_upper_threshold, 
                                 bpm_lower_threshold=bpm_lower_threshold,
                                 temperature_upper_threshold=temperature_upper_threshold,
                                 temperature_lower_threshold=temperature_lower_threshold
                                 )
        
        db.session.add(user_detail)
        try:
            db.session.commit()
            return jsonify({"message": "Device will start publishing data"}), 200
        except Exception as e:
            db.session.rollback()
            print(e)  # For debugging
            return jsonify({"error": "Failed to add patient details"}), 500
    else:
        return jsonify({"error": "Device not registered"}), 400


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


@app.route('/device/<device_id>/live-data')
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
