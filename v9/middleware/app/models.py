from . import db
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone

bcrypt = Bcrypt()

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Devices and users within an organization
    devices = db.relationship('Device', backref='organization', lazy=True, cascade="all, delete-orphan")
    users = db.relationship('User', backref='organization', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(17), unique=True, nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    passkey = db.Column(db.String(80), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    # Direct link to user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    data = db.relationship('DeviceData', backref='device', lazy=True, cascade="all, delete-orphan")

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    bpm_upper_threshold = db.Column(db.Integer, nullable=True)
    bpm_lower_threshold = db.Column(db.Integer, nullable=True)
    temperature_upper_threshold = db.Column(db.Integer, nullable=True)
    temperature_lower_threshold = db.Column(db.Integer, nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    # Link back to the device
    device = db.relationship('Device', back_populates='user', uselist=False)

class DeviceData(db.Model):
    __tablename__ = 'device_data'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    bpm = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# Ensure bidirectional relationship and easy access from both sides
User.device = db.relationship('Device', back_populates='user', uselist=False, foreign_keys=[Device.user_id])
Device.user = db.relationship('User', back_populates='device', foreign_keys=[Device.user_id])
