# app/routes.py
from flask import request, jsonify, Response, stream_with_context
from . import app, db
from .models import Organization, User, Device, DeviceData
import requests
from datetime import datetime
import json
import time

@app.route('/register', methods=['POST'])
def register_organization():
    data = request.json
    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        return jsonify({"error": "Name and password are required"}), 400

    if Organization.query.filter_by(name=name).first():
        return jsonify({"error": "Organization already exists"}), 400

    new_organization = Organization(name=name)
    new_organization.set_password(password)
    db.session.add(new_organization)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"success": "Organization registered successfully", "organization_id": new_organization.id}), 201

@app.route('/login', methods=['POST'])
def login_organization():
    data = request.json
    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        return jsonify({"error": "Name and password are required"}), 400

    organization = Organization.query.filter_by(name=name).first()

    if organization and organization.check_password(password):
        # For simplicity, returning a success message. 
        # In a real app, you might return a token for authenticated routes.
        return jsonify({"success": "Login successful", "organization_id": organization.id}), 200
    else:
        return jsonify({"error": "Invalid name or password"}), 401


@app.route('/add-new-user', methods=['POST'])
def add_new_user():
    data = request.json
    organization_id = data.get('organization_id')
    username = data.get('username')
    phone_number = data.get('phone_number')
    bpm_upper_threshold = data.get('bpm_upper_threshold', None)
    bpm_lower_threshold = data.get('bpm_lower_threshold', None)
    temperature_upper_threshold = data.get('temperature_upper_threshold', None)
    temperature_lower_threshold = data.get('temperature_lower_threshold', None)

    if not all([organization_id, username, phone_number]):
        return jsonify({"error": "Organization ID, username, and phone number are required"}), 400

    # Check if the organization exists
    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"error": "Organization not found"}), 404

    # Check if a user with the same username already exists within the organization
    existing_user = User.query.filter_by(username=username, organization_id=organization_id).first()
    if existing_user:
        return jsonify({"error": "A user with this username already exists within the organization"}), 409

    new_user = User(username=username, phone_number=phone_number,
                    bpm_upper_threshold=bpm_upper_threshold, bpm_lower_threshold=bpm_lower_threshold,
                    temperature_upper_threshold=temperature_upper_threshold, temperature_lower_threshold=temperature_lower_threshold,
                    organization_id=organization_id)  # Assign the user to the organization

    db.session.add(new_user)
    try:
        db.session.commit()
        return jsonify({"success": "User added successfully", "user_id": new_user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500 

@app.route('/add-new-device', methods=['POST'])
def add_or_update_device():
    data = request.json
    mac_address = data.get('mac_address')
    ip_address = data.get('ip_address')
    passkey = data.get('passkey')
    nickname = data.get('nickname')

    # Find an existing device by MAC address
    device = Device.query.filter_by(mac_address=mac_address).first()

    if device:
        # Update the existing device's IP address 
        device.ip_address = ip_address
    else:
        # Create a new device since it doesn't exist
        device = Device(mac_address=mac_address, ip_address=ip_address, nickname=nickname, passkey=passkey)
        db.session.add(device)

    try:
        db.session.commit()
        return jsonify({"success": "Device added or updated successfully", "device_id": device.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@app.route('/associate-device', methods=['POST'])
def associate_device_to_organization():
    data = request.json
    nickname = data.get('nickname', '').strip()
    passkey = data.get('passkey', '').strip()
    organization_id = data.get('organization_id')

    # Validate required fields
    if not organization_id or not nickname or not passkey:
        return jsonify({"error": "Organization ID, nickname, and passkey are required"}), 400

    # Check if the organization exists
    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"error": "Organization not found"}), 404

    # Find the device by nickname and passkey
    device = Device.query.filter_by(nickname=nickname, passkey=passkey).first()

    if not device:
        return jsonify({"error": "Device not found with the provided nickname and passkey"}), 404

    # Check if the device is already associated with an organization
    if device.organization_id:
        return jsonify({"error": "Device is already associated with an organization"}), 409

    # Associate the device with the organization
    device.organization_id = organization_id

    try:
        db.session.commit()
        return jsonify({"success": "Device associated with the organization successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/assign-device-to-user', methods=['POST'])
def assign_device_to_user():
    data = request.json
    user_id = data.get('user_id')
    device_id = data.get('device_id')

    # Validate user and device IDs
    if not user_id or not device_id:
        return jsonify({"error": "User ID and Device ID are required"}), 400

    # Find the user and device
    user = User.query.get(user_id)
    device = Device.query.get(device_id)

    if not user or not device:
        return jsonify({"error": "User or Device not found"}), 404

    # Optionally, update the device with the user_id if you're tracking device assignment in your database
    device.user_id = user_id
    db.session.commit()

    # Prepare the user details to send to the device
    user_details = {
        "username": user.username,
        "phone_number": user.phone_number,
        "bpm_upper_threshold": user.bpm_upper_threshold,
        "bpm_lower_threshold": user.bpm_lower_threshold,
        "temperature_upper_threshold": user.temperature_upper_threshold,
        "temperature_lower_threshold": user.temperature_lower_threshold,
    }

    # Send a request to the device's IP address with the user details
    try:
        response = requests.post(f"http://{device.ip_address}:80/receive-user-details", json=user_details, timeout=5)
        if response.status_code == 200:
            return jsonify({"success": "User details sent to the device successfully"}), 200
        else:
            return jsonify({"error": "Failed to send user details to the device"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request to device failed: {e}"}), 500

@app.route('/unassign-device/<int:device_id>/<int:user_id>', methods=['POST'])
def unassign_device(device_id, user_id):

    device = Device.query.get(device_id)
    user = User.query.get(user_id)

    if not device or not user:
        return jsonify({"error": "Device or user not found"}), 404

    if device.user_id != user_id:
        return jsonify({"error": "Device is not assigned to the specified user"}), 400
    try:
        # Clear user details from the device by sending a request
        if device.ip_address:
            response = requests.post(f"http://{device.ip_address}:80/clear-user-details", json={}, timeout=5)
            if response.status_code != 200:
                return jsonify({"error": "Failed to clear user details on the device"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to communicate with the device: {e}"}), 500

    # Remove the link between the device and the user
    device.user_id = None
    user.device = None
    # Optionally, clear device data associated with the device
    DeviceData.query.filter_by(device_id=device_id).delete()

    db.session.commit()

    db.session.refresh(device)
    db.session.refresh(user)


    return jsonify({"success": "Device unassigned successfully, user details cleared, and device data removed"}), 200


@app.route('/update-user-details', methods=['POST'])
def update_user_details():
    data = request.json
    user_id = data.get('user_id')

    # Validate user ID
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # Find the user
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Update user details
    user.username = data.get('username', user.username)
    user.phone_number = data.get('phone_number', user.phone_number)
    user.bpm_upper_threshold = data.get('bpm_upper_threshold', user.bpm_upper_threshold)
    user.bpm_lower_threshold = data.get('bpm_lower_threshold', user.bpm_lower_threshold)
    user.temperature_upper_threshold = data.get('temperature_upper_threshold', user.temperature_upper_threshold)
    user.temperature_lower_threshold = data.get('temperature_lower_threshold', user.temperature_lower_threshold)

    # If a device is assigned to the user, send the updated details to the device
    if user.device:
        device = user.device
        user_details = {
            "username": user.username,
            "phone_number": user.phone_number,
            "bpm_upper_threshold": user.bpm_upper_threshold,
            "bpm_lower_threshold": user.bpm_lower_threshold,
            "temperature_upper_threshold": user.temperature_upper_threshold,
            "temperature_lower_threshold": user.temperature_lower_threshold,
        }

        try:
            response = requests.post(f"http://{device.ip_address}:80/receive-user-details", json=user_details, timeout=5)
            if response.status_code == 200:
                db.session.commit()
                return jsonify({"success": "User details updated successfully and sent to the device"}), 200
            else:
                db.session.rollback()
                return jsonify({"error": "Failed to send updated user details to the device"}), 500
        except requests.exceptions.RequestException as e:
            db.session.rollback()
            return jsonify({"error": f"Request to device failed: {e}"}), 500
    else:
        return jsonify({"success": "User details updated successfully, but no device is assigned to this user"}), 200
    
@app.route('/get-device-data/<int:device_id>', methods=['GET'])
def get_device_data(device_id):
    # Retrieve the latest data for the specified device
    def generate():
        with app.app_context():
            # Infinite loop to continuously poll for new data
            while True:
                # Query for the latest device data here
                latest_data = DeviceData.query.filter_by(device_id=device_id).order_by(DeviceData.timestamp.desc()).first()
                yield f"data: {json.dumps({'bpm': latest_data.bpm, 'temperature': latest_data.temperature})}\n\n"
                time.sleep(5)  # Sleep for a bit before sending the next update
        
    return Response(generate(), content_type='text/event-stream', headers={'Cache-Control': 'no-cache'})

@app.route('/save-device-data', methods=['POST'])
def save_device_data():
    data = request.get_json()
    device_id = data.get('device_id')
    bpm = data.get('bpm')
    temperature = data.get('temp')

    if not device_id or bpm is None or temperature is None:
        return jsonify({"error": "Missing data"}), 400

    new_device_data = DeviceData(
        device_id=device_id,
        bpm=bpm,
        temperature=temperature,
        timestamp=datetime.now()
    )

    db.session.add(new_device_data)
    try:
        db.session.commit()
        return jsonify({"message": "Device data saved successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/delete-device/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    device = Device.query.get(device_id)
    if device:
        # If the device is assigned to a user, clear the association
        if device.user:
            try:
                if device.ip_address:  # If the device has an IP address
                    # Send a request to clear user details on the device
                    requests.post(f"http://{device.ip_address}:80/clear-user-details", json={}, timeout=5)
            except requests.exceptions.RequestException as e:
                # Log the error or handle it as needed
                print(f"Failed to clear user details on the device: {e}")

            # Clear the user_id from the device to unassign the user
            device.user_id = None

        # Delete all associated device data
        DeviceData.query.filter_by(device_id=device_id).delete()

        # Finally, delete the device
        db.session.delete(device)
        db.session.commit()
        return jsonify({"success": "Device and its data deleted successfully, user details cleared"}), 200
    else:
        return jsonify({"error": "Device not found"}), 404


@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        if user.device:
            try:
                device = user.device
                # Send a request to clear user details on the device
                requests.post(f"http://{device.ip_address}:80/clear-user-details", json={}, timeout=5)
            except requests.exceptions.RequestException as e:
                # Log the error or handle it as needed
                print(f"Failed to clear user details on the device: {e}")
                
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": "User deleted successfully, device user details cleared"}), 200
    else:
        return jsonify({"error": "User not found"}), 404


@app.route('/delete-organization/<int:organization_id>', methods=['DELETE'])
def delete_organization(organization_id):
    organization = Organization.query.get(organization_id)
    if organization:
        devices = organization.devices
        for device in devices:
            try:
                if device.ip_address:
                    # Send a request to clear user details on the device
                    requests.post(f"http://{device.ip_address}:80/clear-user-details", json={}, timeout=5)
            except requests.exceptions.RequestException as e:
                # Log the error or handle it as needed
                print(f"Failed to clear user details on device {device.id}: {e}")
                
        db.session.delete(organization)
        db.session.commit()
        return jsonify({"success": "Organization, its devices, users, and device data deleted successfully, device user details cleared"}), 200
    else:
        return jsonify({"error": "Organization not found"}), 404

@app.route('/devices', methods=['GET'])
def get_devices():
    # Retrieve organization_id from query parameters
    organization_id = request.args.get('organization_id', default=None, type=int)

    if organization_id is None:
        return jsonify({"error": "organization_id is required"}), 400

    # Filter devices by the provided organization_id
    devices = Device.query.filter_by(organization_id=organization_id).all()

    devices_list = [{
        'id': device.id,
        'mac_address': device.mac_address,
        'ip_address': device.ip_address,
        'nickname': device.nickname,
        'is_assigned_to_user': device.user_id is not None
    } for device in devices]

    return jsonify(devices_list), 200

@app.route('/users', methods=['GET'])
def get_users():

    organization_id = request.args.get('organization_id', default=None, type=int)

    users = User.query.filter_by(organization_id=organization_id).all()
    users_list = [{
        'id': user.id,
        'username': user.username,
        'device_assigned': user.device is not None 
    } for user in users]
    return jsonify(users_list), 200

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = {
        'id': user.id,
        'username': user.username,
        'phone_number': user.phone_number,
        'bpm_upper_threshold': user.bpm_upper_threshold,
        'bpm_lower_threshold': user.bpm_lower_threshold,
        'temperature_upper_threshold': user.temperature_upper_threshold,
        'temperature_lower_threshold': user.temperature_lower_threshold,
        'device': {
            'id': user.device.id,
            'mac_address': user.device.mac_address,
            'ip_address': user.device.ip_address,
            'nickname': user.device.nickname
        } if user.device else None
    }
    return jsonify(user_data), 200
