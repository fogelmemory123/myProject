from flask import Blueprint, request
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, RoomReservation, User
from datetime import datetime

rooms_bp = Blueprint('rooms', __name__)
api = Api(rooms_bp)

class AddRoomReservation(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        date_str = data.get('date')
        hour = data.get('hour')
        room_name = data.get('room_name')
        # Get slot number if provided, otherwise default to 1
        slot = data.get('slot', 1)

        if not all([date_str, hour, room_name]):
            return {"status": "fail", "message": "Missing data"}, 400

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return {"status": "fail", "message": "Invalid date format"}, 400

        user = User.query.get(get_jwt_identity())

        # Updated check - now checking slot as well
        existing_reservation = RoomReservation.query.filter_by(
            date=date,
            hour=hour,
            room_name=room_name,
            slot=slot,  # Check by slot
            branch_id=user.branch_id
        ).first()

        if existing_reservation:
            return {"status": "fail", "message": "Room already reserved in your branch"}, 409

        # Limit of maximum 2 reservations in Brosh room at the same hour
        if room_name == 'ברוש':
            count = RoomReservation.query.filter_by(
                date=date,
                hour=hour,
                room_name=room_name,
                branch_id=user.branch_id
            ).count()
            
            if count >= 2:
                return {"status": "fail", "message": "Maximum reservations reached for this room"}, 409

        # Save slot in reservation
        reservation = RoomReservation(
            date=date,
            hour=hour,
            room_name=room_name,
            slot=slot,  # Save slot
            user_id=user.id,
            branch_id=user.branch_id
        )

        db.session.add(reservation)
        db.session.commit()

        return {"status": "success", "message": "Room reserved successfully"}

class GetAllRoomReservations(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get(get_jwt_identity())
        reservations = RoomReservation.query.filter_by(branch_id=user.branch_id).all()
        data = [
            {
                "date": r.date.strftime('%Y-%m-%d'),
                "hour": r.hour,
                "room_name": r.room_name,
                "slot": r.slot,  # Added slot field to response
                "user": f"{r.user.first_name} {r.user.last_name}",
                "user_id": r.user.id,
                "branch": r.branch.city
            }
            for r in reservations
        ]
        return {"status": "success", "data": data}

class CancelRoomReservation(Resource):
    @jwt_required()
    def delete(self):
        data = request.get_json()
        date_str = data.get('date')
        hour = data.get('hour')
        room_name = data.get('room_name')
        slot = data.get('slot', 1)  # Get slot number if provided, otherwise default to 1

        if not all([date_str, hour, room_name]):
            return {"status": "fail", "message": "Missing data"}, 400

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return {"status": "fail", "message": "Invalid date format"}, 400

        user_id = get_jwt_identity()

        # Updated check - now checking slot as well
        reservation = RoomReservation.query.filter_by(
            date=date,
            hour=hour,
            room_name=room_name,
            slot=slot,  # Check by slot
            user_id=user_id
        ).first()

        if not reservation:
            return {"status": "fail", "message": "Reservation not found or not yours"}, 404

        db.session.delete(reservation)
        db.session.commit()

        return {"status": "success", "message": "Reservation canceled"}

# Register API endpoints
api.add_resource(AddRoomReservation, '/reserve')
api.add_resource(GetAllRoomReservations, '/all')
api.add_resource(CancelRoomReservation, '/cancel')
