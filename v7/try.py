from flask import Flask, request, jsonify, render_template, request, redirect, url_for, flash
from flask_cors import CORS
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

app.secret_key = 'dissertation'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('index.html', devices=devices)

@app.route('/add-device-page')
def add_device_page():
    return render_template('add_device.html', devices=devices)

@app.route('/add-device', methods=['POST'])
def add_device():
    ip_address = request.form.get('ip')
    passkey = request.form.get('passkey')
    nickname = request.form.get('nickname')
    
    if verify_device(ip_address, passkey):
        devices[ip_address] = {'nickname': nickname, 'passkey': passkey}
        return redirect(url_for('index'))
    else:
        return jsonify({"error": "Failed to connect to device"}), 400


@app.route('/submit-patient-details', methods=['POST'])
def submit_patient_details():
    ip_address = request.json.get('deviceIp')
    patient_name = request.json.get('patientName')
    phone_number = request.json.get('phoneNumber')
    
    print(ip_address, patient_name, phone_number)
    success = send_patient_data_to_device(ip_address, patient_name, phone_number)
    if ip_address in devices:
        # Here you could notify the device to start. Skipping for brevity.
        return jsonify({"message": "Device will start publishing data"}), 200
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


def send_patient_data_to_device(ip_address, patient_name, phone_number):
    print(patient_name, phone_number)
    device_url = f"http://{ip_address}/receive-patient-data"
    data = {
        'patientName': patient_name,
        'phoneNumber': phone_number
    }
    try:
        response = requests.post(device_url, json=data, timeout=5)
        if response.status_code == 200:
            print("Successfully sent patient data to the device.")
        else:
            print("Failed to send patient data. Device responded with an error.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send patient data to the device: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
