from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class Branch(db.Model):
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(80), unique=True, nullable=False)

    users = db.relationship('User', back_populates='branch', lazy=True)
    events = db.relationship('Event', back_populates='branch', lazy=True)
    room_reservations = db.relationship('RoomReservation', back_populates='branch', lazy=True)
    participants = db.relationship('Participant', back_populates='branch', lazy=True)
    shifts = db.relationship('Shift', back_populates='branch', lazy=True)

    def __repr__(self):
        return f'<Branch {self.city}>'


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    users = db.relationship('User', back_populates='role_obj', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)  # Changed from String to Date
    password_hash = db.Column(db.String(228), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    branch = db.relationship('Branch', back_populates='users')
    role_obj = db.relationship('Role', back_populates='users')
    shifts = db.relationship('Shift', back_populates='user', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('Event', back_populates='creator', lazy=True, cascade='all, delete-orphan')
    room_reservations = db.relationship('RoomReservation', back_populates='user', lazy=True, cascade='all, delete-orphan')
    participations = db.relationship('Participant', back_populates='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name}>'


class Shift(db.Model):
    __tablename__ = 'shifts'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    shiftType = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)

    user = db.relationship('User', back_populates='shifts')
    branch = db.relationship('Branch', back_populates='shifts')  # Added back_populates

    def __repr__(self):
        return f'<Shift {self.date} {self.shiftType} {self.location}>'


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)  # Changed from String to Date
    event_description = db.Column(db.String(200), nullable=False)
    lecturer_name = db.Column(db.String(100), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    branch = db.relationship('Branch', back_populates='events')
    creator = db.relationship('User', back_populates='events')
    participants = db.relationship(
        'Participant',
        back_populates='event',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f'<Event {self.date} {self.event_description}>'


class RoomReservation(db.Model):
    __tablename__ = 'room_reservations'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.String(10), nullable=False)
    room_name = db.Column(db.String(50), nullable=False)
    slot = db.Column(db.Integer, default=1)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)

    user = db.relationship('User', back_populates='room_reservations')
    branch = db.relationship('Branch', back_populates='room_reservations')

    __table_args__ = (
        db.UniqueConstraint('date', 'hour', 'room_name', 'slot', 'branch_id'),
    )

    def __repr__(self):
        return f'<RoomReservation {self.date} {self.hour} Room: {self.room_name}>'


class Participant(db.Model):
    __tablename__ = 'participants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reminder_sent = db.Column(db.Boolean, default=False)

    event = db.relationship('Event', back_populates='participants')
    branch = db.relationship('Branch', back_populates='participants')
    user = db.relationship('User', back_populates='participations')

    def __repr__(self):
        return f'<Participant {self.name} {self.email}>'
