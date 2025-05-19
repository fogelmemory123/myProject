from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Participant, Event, User

participants_bp = Blueprint('participants', __name__)
api = Api(participants_bp)

# רישום משתמש לאירוע
class RegisterParticipant(Resource):
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return {"message": "משתמש לא נמצא"}, 404

        data = request.get_json()
        event_id = data.get('event_id')

        if not event_id:
            return {"message": "חסר מזהה אירוע"}, 400

        # האם כבר רשום?
        already_registered = Participant.query.filter_by(user_id=user.id, event_id=event_id).first()
        if already_registered:
            return {"message": "כבר נרשמת לאירוע הזה"}, 400

        participant = Participant(
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
            event_id=event_id,
            branch_id=user.branch_id,
            user_id=user.id
        )

        db.session.add(participant)
        db.session.commit()

        return {"message": "נרשמת בהצלחה!"}, 201


# צפייה במשתתפי אירוע
class EventParticipants(Resource):
    @jwt_required()
    def get(self, event_id):
        participants = Participant.query.filter_by(event_id=event_id).all()
        return jsonify([{
            "id": p.id,
            "name": p.name,
            "email": p.email,
            "branch_id": p.branch_id,
            "user_id": p.user_id
        } for p in participants])

class PublicParticipants(Resource):
    def get(self, event_id):
        participants = Participant.query.filter_by(event_id=event_id).all()
        return jsonify([{
            "id": p.id,
            "name": p.name
        } for p in participants])
# רישום הנתיבים
api.add_resource(RegisterParticipant, '/register') 
api.add_resource(PublicParticipants, '/public/event/<int:event_id>/participants')
api.add_resource(EventParticipants, '/<int:event_id>/participants')   
