from flask import Blueprint, jsonify, request, make_response
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Shift

shifts_bp = Blueprint('shifts', __name__)
api = Api(shifts_bp)

user_parser = reqparse.RequestParser()
user_parser.add_argument('email', required=True, help='Email cannot be blank')
user_parser.add_argument('password', required=True, help='Password cannot be blank')

class Logout(Resource):
    @jwt_required()
    def post(self):
        return make_response(jsonify({'status': 'success', 'message': 'Logged out successfully'}), 200)

class UserRegistration(Resource):
    def post(self):
        data = request.get_json()

        required_fields = ['first_name', 'last_name', 'email', 'password', 'role', 'branch_id']
        for field in required_fields:
            if field not in data:
                return {'message': f'{field} is required'}, 400

        if User.query.filter_by(email=data['email']).first():
            return {'message': 'User already exists'}, 400

        user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            role=data['role'],
            branch_id=data['branch_id'],
            birth_date=data.get('birth_date')
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        return {'access_token': access_token, 'access_id': user.id}, 200

class UserLogin(Resource):
    def post(self):
        data = user_parser.parse_args()
        user = User.query.filter_by(email=data['email']).first()

        if not user or not user.check_password(data['password']):
            return {'message': 'Invalid email or password'}, 401

        access_token = create_access_token(identity=str(user.id))
        return {'access_token': access_token, 'access_id': user.id}, 200

class AddShifts(Resource):
    @jwt_required()
    def post(self):
        user = User.query.get(get_jwt_identity())
        if not user:
            return {'status': 'fail', 'message': 'User not found'}, 404

        data = request.get_json()
        date = data.get('date')
        shiftType = data.get('shiftType')
        location = data.get('location')

        if not all([date, shiftType]):
            return {'status': 'fail', 'message': 'Missing date or shiftType'}, 400

        # מחפש משמרת קיימת למשתמש בתאריך ובסוג המשמרת
        existing_shift = Shift.query.filter_by(
            date=date, 
            shiftType=shiftType, 
            user_id=user.id
        ).first()

        # אם location לא נשלח בכלל (None)
        if location is None:
            return {
                'status': 'fail',
                'message': 'Location is required'
            }, 400

        # אם location ריק (מבטל משמרת)
        if not location:
            if existing_shift:
                db.session.delete(existing_shift)
                db.session.commit()
                return {
                    'status': 'success',
                    'message': 'Shift deleted successfully',
                    'data': {
                        'date': date,
                        'shiftType': shiftType,
                        'action': 'deleted'
                    }
                }, 200
            else:
                return {
                    'status': 'success',
                    'message': 'No shift exists to delete',
                    'data': {
                        'date': date,
                        'shiftType': shiftType,
                        'action': 'none'
                    }
                }, 200

        # אם location לא ריק - עדכון/יצירת משמרת
        if existing_shift:
            existing_shift.location = location
            existing_shift.branch_id = user.branch_id
            db.session.commit()
            return {
                'status': 'success',
                'message': 'Shift updated successfully',
                'data': {
                    'id': existing_shift.id,
                    'user': f'{user.first_name} {user.last_name}',
                    'date': date,
                    'shiftType': shiftType,
                    'location': location,
                    'branch_id': user.branch_id,
                    'action': 'updated'
                }
            }, 200
        else:
            new_shift = Shift(
                date=date,
                shiftType=shiftType,
                location=location,
                user_id=user.id,
                branch_id=user.branch_id
            )
            db.session.add(new_shift)
            db.session.commit()
            return {
                'status': 'success',
                'message': 'Shift created successfully',
                'data': {
                    'id': new_shift.id,
                    'user': f'{user.first_name} {user.last_name}',
                    'date': date,
                    'shiftType': shiftType,
                    'location': location,
                    'branch_id': user.branch_id,
                    'action': 'created'
                }
            }, 201

class GetShifts(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get(get_jwt_identity())
        if not user:
            return {'status': 'fail', 'message': 'User not found'}, 404

        shifts = Shift.query.filter_by(user_id=user.id).all()
        shift_data = [
            {
                'date': s.date.strftime('%Y-%m-%d'),  # ← תיקון לפורמט ISO
                'shiftType': s.shiftType,
                'location': s.location
            }
            for s in shifts
        ]
        return {'status': 'success', 'data': shift_data}



class GetAllShifts(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get(get_jwt_identity())
        if not user:
            return {'status': 'fail', 'message': 'User not found'}, 404

        shifts = Shift.query.filter_by(branch_id=user.branch_id).all()
        shift_data = [
            {
                'date': s.date.strftime('%Y-%m-%d'),  # ← המרה למחרוזת
                'shiftType': s.shiftType,
                'location': s.location,
                'user': f'{s.user.first_name} {s.user.last_name}',
                'branch_id': s.branch_id
            }
            for s in shifts
        ]
        return {'status': 'success', 'data': shift_data}


class GetUserName(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get(get_jwt_identity())
        if not user:
            return {'message': 'User not found'}, 404

        branch_name = user.branch.city if user.branch else 'לא משויך'
        role_name = user.role_obj.name if user.role_obj else 'לא מוגדר'

        return {
            'name': f'{user.first_name} {user.last_name}',
            'branch': branch_name,
            'role': role_name,
            'branch_id': user.branch_id
        }



# Register resources
#api.add_resource(UserRegistration, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(AddShifts, '/addshift')
api.add_resource(GetShifts, '/getshifts')
api.add_resource(GetAllShifts, '/getallshifts')
api.add_resource(Logout, '/logout')
api.add_resource(GetUserName, '/getusername')
