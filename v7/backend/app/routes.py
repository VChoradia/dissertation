# app/routes.py
from flask import Flask, request, jsonify, render_template, request, redirect, url_for, flash
import requests
from . import app, db
from .models import Device, UserDetail

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

    device = Device.query.filter_by(ip_address=ip_address).first()
    if device:
        patient_detail = UserDetail(user_name=user_name, phone_number=phone_number, device_id=device.id)
        db.session.add(patient_detail)
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


def send_user_data_to_device(ip_address, user_name, phone_number):
    print(user_name, phone_number)
    device_url = f"http://{ip_address}/receive-user-data"
    data = {
        'userName': user_name,
        'phoneNumber': phone_number
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

    if request.method == 'POST':
        # Process the submitted user details form
        user_name = request.form.get('user_name')
        phone_number = request.form.get('phone_number')
        
        # Attempt to send user data to the device
        success = send_user_data_to_device(device.ip_address, user_name, phone_number)
        if success:
            # Save user details to the database only if successful
            new_user_detail = UserDetail(device_id=device.id, user_name=user_name, phone_number=phone_number)
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