from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import User, Branch, Role, Shift, Event, Participant
from datetime import datetime

admin_bp = Blueprint('admin', __name__)
api = Api(admin_bp)

class GetAdminDetails(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get(get_jwt_identity())

        if user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        return {
            'name': f'{user.first_name} {user.last_name}',
            'branch_id': user.branch_id,
            'branch_name': user.branch.city if user.branch else None,
            'role': user.role_obj.name
        }

class GetAllBranches(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.get(get_jwt_identity())

        if not current_user:
            return {'message': 'Unauthorized'}, 403

        role = current_user.role_obj.name

        if role == 'אדמין':
            branches = Branch.query.all()
        elif role == 'מנהל סניף':
            branches = [current_user.branch] if current_user.branch else []
        else:
            return {'message': 'אין הרשאה לצפות בסניפים'}, 403

        return {
            'branches': [{'id': b.id, 'name': b.city} for b in branches]
        }

class UserRegistration(Resource):
    @jwt_required()
    def post(self):
        current_user = User.query.get(get_jwt_identity())

        if not current_user or current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        data = request.get_json()
        required_fields = ['first_name', 'last_name', 'email', 'password', 'role']

        for field in required_fields:
            if field not in data or not data.get(field):
                return {'message': f'{field} is required'}, 400

        if current_user.role_obj.name == 'אדמין' and not data.get('branch_id'):
            return {'message': 'branch_id is required'}, 400

        if current_user.role_obj.name == 'מנהל סניף' and data.get('role') == 'אדמין':
            return {'message': 'אין הרשאה ליצור משתמש מסוג אדמין'}, 403

        branch_id = (
            current_user.branch_id if current_user.role_obj.name == 'מנהל סניף'
            else data.get('branch_id')
        )

        if User.query.filter_by(email=data['email']).first():
            return {'message': 'User already exists'}, 400

        role = Role.query.filter_by(name=data['role']).first()
        if not role:
            return {'message': 'Role not found'}, 400

        new_user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            role_id=role.id,
            branch_id=branch_id,
            birth_date=data.get('birth_date')
        )
        new_user.set_password(data['password'])

        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=str(new_user.id))
        return {'access_token': access_token, 'access_id': new_user.id}, 200

class GetAllShiftsForAdmin(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.get(get_jwt_identity())

        if not current_user or current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        query = db.session.query(Shift, Branch, User).join(Branch, Shift.branch_id == Branch.id).join(User, Shift.user_id == User.id)

        if current_user.role_obj.name == 'מנהל סניף':
            query = query.filter(Shift.branch_id == current_user.branch_id)

        shifts = query.all()

        shift_data = [
            {
                'user_id': shift.user.id,
                'user': f"{user.first_name} {user.last_name}",
                'date': shift.date.strftime('%Y-%m-%d'),
                'shiftType': shift.shiftType,
                'location': shift.location,
                'branch': branch.city
            }
            for shift, branch, user in shifts
        ]
        return {'status': 'success', 'data': shift_data}

class EventsWithParticipants(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.get(get_jwt_identity())

        if current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        if current_user.role_obj.name == 'אדמין':
            events = Event.query.all()
        else:
            events = Event.query.filter_by(branch_id=current_user.branch_id).all()

        output = []
        for event in events:
            participants = [
                {
                    'name': f'{p.user.first_name} {p.user.last_name}'
                }
                for p in event.participants if p.user
            ]
            output.append({
                'id': event.id,
                'date': event.date.strftime('%Y-%m-%d') if not isinstance(event.date, str) else event.date,
                'event_description': event.event_description,
                'lecturer_name': event.lecturer_name,
                'branch_city': event.branch.city if event.branch else '',
                'participants': participants
            })

        return jsonify(output)

class DeleteEvent(Resource):
    @jwt_required()
    def delete(self, event_id):
        current_user = User.query.get(get_jwt_identity())

        if current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        event = Event.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404

        if current_user.role_obj.name == 'מנהל סניף' and event.branch_id != current_user.branch_id:
            return {'message': 'אין לך הרשאה למחוק את האירוע הזה'}, 403

        Participant.query.filter_by(event_id=event.id).delete()
        db.session.delete(event)
        db.session.commit()

        return {'message': 'Event deleted successfully'}, 200

class GetUser(Resource):
    @jwt_required()
    def get(self, user_id):
        current_user = User.query.get(get_jwt_identity())

        if not current_user or current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        user_data = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'branch_id': user.branch_id,
            'branch': user.branch.city if user.branch else None,
            'role': user.role_obj.name if user.role_obj else None,
            'birth_date': user.birth_date.strftime('%Y-%m-%d') if isinstance(user.birth_date, datetime) else str(user.birth_date) if user.birth_date else None
        }

        return jsonify({'user': user_data}), 200

class GetAllUsers(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.get(get_jwt_identity())

        if not current_user:
            return {'message': 'Unauthorized'}, 403

        if not current_user.role_obj:
            return {'message': 'למשתמש אין תפקיד'}, 400

        role = current_user.role_obj.name

        if role == 'אדמין':
            users = User.query.all()
        elif role == 'מנהל סניף':
            users = User.query.filter_by(branch_id=current_user.branch_id).all()
        else:
            return {'message': 'אין לך הרשאה לצפות במשתמשים'}, 403

        user_list = []
        for user in users:
            user_data = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'branch_id': user.branch_id,
            }

            # Safely access branch city
            if user.branch:
                user_data['branch'] = user.branch.city
            else:
                user_data['branch'] = None

            # Safely access role name
            if user.role_obj:
                user_data['role'] = user.role_obj.name
            else:
                user_data['role'] = None

            # Safely format birth_date
            if isinstance(user.birth_date, datetime):
                user_data['birth_date'] = user.birth_date.strftime('%Y-%m-%d')
            elif user.birth_date:
                user_data['birth_date'] = str(user.birth_date)
            else:
                user_data['birth_date'] = None

            user_list.append(user_data)

        return {'users': user_list}, 200

class UpdateUser(Resource):
    @jwt_required()
    def put(self, user_id):
        current_user = User.query.get(get_jwt_identity())

        if not current_user or current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        data = request.get_json()
        # Update user fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        if 'branch_id' in data:
            user.branch_id = data['branch_id']
        if 'birth_date' in data:
            user.birth_date = data['birth_date']

        # if 'role' in data:
        #     if current_user.role_obj.name == 'אדמין':
        #         # אדמין יכול לשנות לכל תפקיד
        #         role = Role.query.filter_by(name=data['role']).first()
        #         if not role:
        #             return {'message': 'Role not found'}, 400
        #         user.role_id = role.id
        #     elif current_user.role_obj.name == 'מנהל סניף':
        #         # מנהל סניף יכול לשנות רק ל'מנהל סניף' או 'מקבל שירות'
        #         if data['role'] not in ['מנהל סניף', 'מקבל שירות']:
        #             return {'message': 'Branch manager can only assign branch manager or service receiver roles'}, 403
        #         role = Role.query.filter_by(name=data['role']).first()
        #         if not role:
        #             return {'message': 'Role not found'}, 400
        #         user.role_id = role.id

        db.session.commit()
        return {'message': 'User updated successfully'}, 200

# Resource registration
api.add_resource(GetAdminDetails, '/getadmin')
api.add_resource(UserRegistration, '/register')
api.add_resource(GetAllBranches, '/branches')
api.add_resource(GetUser, '/users/<int:user_id>')  # Fixed the method name
api.add_resource(GetAllUsers, '/allusers')
api.add_resource(GetAllShiftsForAdmin, '/allshifts')
api.add_resource(EventsWithParticipants, '/events_with_participants')
api.add_resource(DeleteEvent, '/calendar/event/<int:event_id>')
api.add_resource(UpdateUser, '/users/<int:user_id>')
