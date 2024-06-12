from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from dormitory import db


class Dorm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    levels = db.Column(db.Integer, nullable=False)
    rooms = db.Column(db.Integer, nullable=False, default=0)
    left_residents = db.Column(db.Integer, nullable=False, default=0)
    gender = db.Column(db.String(10), nullable=False)


class Room(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    dorm_id = db.Column(db.Integer, db.ForeignKey("dorm.id"), nullable=False)
    dorm = db.relationship("Dorm", backref=db.backref("apartments"))
    level = db.Column(db.Integer, nullable=False)
    spaces = db.Column(db.Integer, nullable=False)
    residents = db.Column(db.Integer, nullable=False, default=0)


class Manager(db.Model, UserMixin):
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(20), default="12312312312")
    dorm_id = db.Column(db.Integer, db.ForeignKey("dorm.id"), nullable=False)
    dorm = db.relationship("Dorm", backref=db.backref("managers"))

    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model, UserMixin):
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(20), default="12312312312")
    major = db.Column(db.String(20), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.String(20), db.ForeignKey("room.id"), nullable=False)
    room = db.relationship("Room", backref=db.backref("students"))

    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class Fix(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), db.ForeignKey("student.id"), nullable=False)
    student = db.relationship("Student", backref=db.backref("fixes"))
    room_id = db.Column(db.String(20), db.ForeignKey("room.id"), nullable=False)
    room = db.relationship("Room", backref=db.backref("fixes"))
    category = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(100))
    picture = db.Column(db.String(100))
    submit_time = db.Column(db.DateTime, default=db.func.now())
    status = db.Column(db.String(20), default="未处理")


class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), db.ForeignKey("student.id"), nullable=False)
    student = db.relationship("Student", backref=db.backref("visitors"))
    room_id = db.Column(db.String(20), db.ForeignKey("room.id"), nullable=False)
    room = db.relationship("Room", backref=db.backref("visitors"))
    name = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    visit_time = db.Column(db.DateTime, default=db.func.now())
    leave_time = db.Column(db.DateTime, default=None)


class Move(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), db.ForeignKey("student.id"), nullable=False)
    student = db.relationship("Student", backref=db.backref("moves"))
    original_room_id = db.Column(db.String(20), nullable=False)
    target_room_id = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(100))
    submit_time = db.Column(db.DateTime, default=db.func.now())
    status = db.Column(db.String(20), default="未处理")
