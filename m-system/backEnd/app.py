from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db, jwt
from shifts.routes import shifts_bp
from calendar_app.routes import calendar_bp
from admin.routes import admin_bp
from roles.routes import roles_bp
from rooms.routes import rooms_bp
from participants.routes import participants_bp

app = Flask(__name__)

app.config.from_object(Config)



CORS(app, resources={r"/*": {"origins": [
    "https://shiftsmasters.com",
    "https://www.shiftsmasters.com"
]}}, supports_credentials=True)
db.init_app(app)
jwt.init_app(app)

# רישום ה-Blueprintים
app.register_blueprint(shifts_bp, url_prefix='/shifts')
app.register_blueprint(calendar_bp, url_prefix='/calendar')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(roles_bp, url_prefix='/roles')
app.register_blueprint(rooms_bp, url_prefix='/rooms')
app.register_blueprint(participants_bp, url_prefix="/api/participants")

#app.register_blueprint(branches_bp, url_prefix='/branches')

with app.app_context():
 

    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
