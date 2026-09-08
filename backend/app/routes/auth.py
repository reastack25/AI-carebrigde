from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from sqlalchemy import select

from ..extensions import db
from ..models import Patient, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "patient")

    if not name or not email or not password:
        return jsonify({"message": "name, email and password are required"}), 400
    if role not in {"patient", "doctor", "admin"}:
        return jsonify({"message": "invalid role"}), 400
    if len(password) < 8:
        return jsonify({"message": "password must be at least 8 characters"}), 400
    if db.session.scalar(select(User).where(User.email == email)):
        return jsonify({"message": "email is already registered"}), 409

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    if role == "patient":
        db.session.add(Patient(user_id=user.id))

    db.session.commit()
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"user": user.to_dict(), "access_token": token}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    user = db.session.scalar(select(User).where(User.email == email))

    if not user or not user.check_password(password):
        return jsonify({"message": "invalid email or password"}), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"user": user.to_dict(), "access_token": token})
