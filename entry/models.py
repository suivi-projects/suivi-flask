from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import random
import uuid
from entry import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    return user

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    reset_password_token = db.Column(db.String(100), nullable=True)

    __mapper_args__ = {
        'polymorphic_on': role,
    }

    def __str__(self):
        return f"User('{self.username}', '{self.role}')"

class Rider(User):
    __tablename__ = 'rider'
    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contact = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    vehicle_registration = db.Column(db.String(50), unique=True, nullable=False)
    area_of_operation = db.Column(db.String(100), nullable=False)
    current_location = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='available')
    assigned_parcels = db.relationship('Parcel', back_populates='assigned_rider')

    __mapper_args__ = {
        'polymorphic_identity': 'rider',
    }

    def __repr__(self):
        return f"Rider('{self.username}', '{self.contact}', '{self.vehicle_type}')"

class Sender(User):
    __tablename__ = 'sender'
    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contact = db.Column(db.String(20), unique=True, nullable=False)
    parcels = db.relationship('Parcel', backref='sender', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'sender',
    }

    def __repr__(self):
        return f"Sender('{self.username}', '{self.email}')"

class Admin(User):
    __tablename__ = 'admin'
    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contact = db.Column(db.String(20), unique=True, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

    def __repr__(self):
        return f"Admin('{self.username}', '{self.email}')"

class Parcel(db.Model):
    __tablename__ = 'parcel'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('sender.id'), nullable=False)
    receiver_name = db.Column(db.String(100))
    receiver_contact = db.Column(db.String(20))
    pickup_location = db.Column(db.String(255), nullable=False)
    delivery_location = db.Column(db.String(255), nullable=False)
    pickup_lat = db.Column(db.Float, nullable=True)
    pickup_lng = db.Column(db.Float, nullable=True)
    delivery_lat = db.Column(db.Float, nullable=True)
    delivery_lng = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(50), default='pending', nullable=False)
    stripe_charge_id = db.Column(db.String(100), nullable=True, unique=True)
    description = db.Column(db.String(400), nullable=True)
    rider_id = db.Column(db.String(36), db.ForeignKey('rider.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')
    expected_arrival = db.Column(db.String(50))
    tracking_number = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_rider = db.relationship('Rider', back_populates='assigned_parcels')
    mpesa_receipt = db.Column(db.String(50), nullable=True)
    checkout_request_id = db.Column(db.String(100), nullable=True, index=True)


    @staticmethod
    def generate_tracking_number():
        return ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=10))

    def set_expected_arrival(self):
        self.expected_arrival = (datetime.now() + timedelta(days=1)).strftime('%B %d, %Y, %I:%M %p')

    def __init__(self, **kwargs):
        super(Parcel, self).__init__(**kwargs)
        self.tracking_number = self.generate_tracking_number()
        self.set_expected_arrival()

    def __repr__(self):
        return f"Parcel('{self.id}', '{self.sender_id}', '{self.receiver_name}', '{self.status}')"

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)

class UnansweredQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), default='new', nullable=False) #  enum later with 'new', 'reviewed', 'answered', 'irrelevant'
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        user_info = f" (User ID: {self.user_id})" if self.user_id else ""
        return f'<UnansweredQuestion {self.id}: "{self.query_text[:50]}..."{user_info}>'

