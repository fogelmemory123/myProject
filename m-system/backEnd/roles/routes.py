from flask import Blueprint, jsonify
from flask_restful import Api, Resource
from extensions import db
from models import Role

roles_bp = Blueprint('roles', __name__)
api = Api(roles_bp)

class RoleList(Resource):
    def get(self):
        roles = Role.query.all()
        return jsonify([{'id': r.id, 'name': r.name} for r in roles])

api.add_resource(RoleList, '/')
