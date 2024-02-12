from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///referral_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    referral_code = db.Column(db.String(6), unique=True)
    referral_valid_until = db.Column(db.DateTime)
    referred_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.referral_code}')"

# Регистрация нового пользователя
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    referred_by_code = data.get('referral_code')

    if not username or not email or not password:
        return jsonify({'error': 'Please provide username, email, and password'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'User with this email already exists'}), 400

    # Генерация реферального кода
    referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # Установка срока годности реферального кода
    referral_valid_until = datetime.utcnow() + timedelta(days=30)

    # Создание нового пользователя
    user = User(username=username, email=email, password=password, referral_code=referral_code, referral_valid_until=referral_valid_until)

    # Если указан реферрер, ищем его по реферральному коду и устанавливаем связь
    if referred_by_code:
        referred_by = User.query.filter_by(referral_code=referred_by_code).first()
        if referred_by:
            user.referred_by = referred_by.id

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# Вход пользователя
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Please provide email and password'}), 400

    user = User.query.filter_by(email=email, password=password).first()

    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200

# Получение информации о рефералах по id реферера
@app.route('/referrals/<int:user_id>', methods=['GET'])
def get_referrals(user_id):
    referrals = User.query.filter_by(referred_by=user_id).all()
    referral_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in referrals]
    return jsonify({'referrals': referral_data}), 200

# UI документация (Swagger/ReDoc)
@app.route('/docs')
def docs():
    return redoc.render()

if __name__ == '__main__':
    app.run(debug=True)
