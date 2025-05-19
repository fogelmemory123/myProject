from flask import Blueprint, request, jsonify
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Event, User, Branch
from datetime import datetime

calendar_bp = Blueprint('calendar', __name__)
api = Api(calendar_bp)

# הוספת אירוע חדש
class AdminAddEventResource(Resource):
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return {"message": "משתמש לא נמצא"}, 404

        if user.role_obj.name not in ["אדמין", "מנהל סניף"]:
            return {"message": "אין לך הרשאות להוסיף אירועים"}, 403

        data = request.get_json()
        datetime_str = data.get('date')
        description = data.get('event_description')
        lecturer = data.get('lecturer_name')
        branch_id = data.get('branch_id')

        if not datetime_str or not description or not branch_id:
            return {"message": "יש למלא את כל השדות הנדרשים (תאריך, תיאור, סניף)"}, 400

        if user.role_obj.name == "מנהל סניף":
            if not user.branch_id:
                return {"message": "למנהל הסניף לא משויך סניף"}, 400
            if int(branch_id) != user.branch_id:
                return {"message": "אין לך גישה להוסיף אירוע לסניף אחר"}, 403

        try:
            dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
            event_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
                event_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                return {"message": "פורמט תאריך/שעה שגוי"}, 400

        new_event = Event(
            date=event_date,
            event_description=description,
            lecturer_name=lecturer,
            branch_id=branch_id,
            created_by=user.id
        )

        db.session.add(new_event)
        db.session.commit()

        return {"message": "האירוע נוסף בהצלחה"}, 201

class AdminGetEventsResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return {"message": "משתמש לא נמצא"}, 404

        branch_id_param = request.args.get('branch_id')

        if branch_id_param:
            events = Event.query.filter_by(branch_id=branch_id_param).all()
        else:
            events = Event.query.all()

        result = []
        for e in events:
            result.append({
                "id": e.id,
                "date": e.date,
                "event_description": e.event_description,
                "lecturer_name": e.lecturer_name,
                "branch_id": e.branch_id,
                "branch_city": e.branch.city,
                "created_by": e.created_by
            })

        return jsonify(result)

class CalendarProfileResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return {"message": "משתמש לא נמצא"}, 404

        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "branch_city": user.branch.city,
            "role": user.role_obj.name
        }

class CalendarBranchListResource(Resource):
    @jwt_required()
    def get(self):
        branches = Branch.query.all()
        return jsonify([
            {"id": b.id, "city": b.city}
            for b in branches
        ])

api.add_resource(AdminAddEventResource, '/event')
api.add_resource(AdminGetEventsResource, '/events')
api.add_resource(CalendarProfileResource, '/profile')
api.add_resource(CalendarBranchListResource, '/branches')
