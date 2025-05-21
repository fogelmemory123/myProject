import os
from datetime import timedelta
class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://username:password@host:port/database_name"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '')
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=90)
    
