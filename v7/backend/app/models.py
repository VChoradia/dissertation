from . import db


class Device(db.Model):
    __tablename__ = 'device'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(15), unique=True, nullable=False)
    passkey = db.Column(db.String(80), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)

class UserDetail(db.Model):
    __tablename__ = 'user_detail'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    bpm_upper_threshold = db.Column(db.Integer)
    bpm_lower_threshold = db.Column(db.Integer)
    temperature_upper_threshold = db.Column(db.Integer)
    temperature_lower_threshold = db.Column(db.Integer)
    device = db.relationship('Device', backref=db.backref('user_details', lazy=True))