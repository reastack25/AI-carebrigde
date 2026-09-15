from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import select

from ..extensions import db
from ..models import CareConsent, ClinicalReview, HealthTimelineEvent, MedicalReport, Medication, Patient, SymptomCheck, User

clinical_bp = Blueprint("clinical", __name__, url_prefix="/api/clinical")
MAX_NOTE_LENGTH = 5000


def current_user():
    return db.session.get(User, int(get_jwt_identity()))


def require_role(*roles):
    claims = get_jwt()
    return claims.get("role") in roles


def _doctor_dict(doctor):
    return {
        "id": doctor.id,
        "name": doctor.name,
        "email": doctor.email,
        "specialty": doctor.specialty or "",
        "facility": doctor.facility or "",
    }


def _patient_dict(patient):
    profile = patient.patient_profile
    return {
        "id": patient.id,
        "name": patient.name,
        "email": patient.email,
        "profile": {
            "date_of_birth": profile.date_of_birth.isoformat() if profile and profile.date_of_birth else None,
            "gender": profile.gender if profile else "",
            "blood_group": profile.blood_group if profile else "",
            "emergency_contact": profile.emergency_contact if profile else "",
        },
    }


@clinical_bp.get("/doctors")
@jwt_required()
def list_doctors():
    doctors = db.session.scalars(select(User).where(User.role == "doctor").order_by(User.name.asc())).all()
    return jsonify({"doctors": [_doctor_dict(doctor) for doctor in doctors]}), 200


@clinical_bp.get("/consents")
@jwt_required()
def list_consents():
    user = current_user()
    if not user:
        return jsonify({"message": "user not found"}), 404
    if user.role == "patient":
        consents = db.session.scalars(select(CareConsent).where(CareConsent.patient_id == user.id).order_by(CareConsent.granted_at.desc())).all()
    elif user.role == "doctor":
        consents = db.session.scalars(select(CareConsent).where(CareConsent.doctor_id == user.id, CareConsent.revoked_at.is_(None)).order_by(CareConsent.granted_at.desc())).all()
    else:
        return jsonify({"message": "forbidden"}), 403
    return jsonify({"consents": [item.to_dict() for item in consents]}), 200


@clinical_bp.post("/consents")
@jwt_required()
def grant_consent():
    user = current_user()
    if not user or user.role != "patient":
        return jsonify({"message": "only patients can grant consent"}), 403
    data = request.get_json(silent=True) or {}
    doctor_id = data.get("doctor_id")
    if isinstance(doctor_id, bool) or not str(doctor_id).isdigit() or int(doctor_id) <= 0:
        return jsonify({"message": "doctor_id must be a positive integer"}), 400
    doctor = db.session.get(User, int(doctor_id))
    if not doctor or doctor.role != "doctor":
        return jsonify({"message": "doctor not found"}), 404
    existing = db.session.scalar(select(CareConsent).where(CareConsent.patient_id == user.id, CareConsent.doctor_id == doctor.id, CareConsent.revoked_at.is_(None)))
    if existing:
        return jsonify({"consent": existing.to_dict()}), 200
    consent = CareConsent(patient_id=user.id, doctor_id=doctor.id)
    db.session.add(consent)
    db.session.flush()
    db.session.add(HealthTimelineEvent(user_id=user.id, event_type="consent_granted", title="Clinical access granted", summary=f"You granted {doctor.name} access to your CareBridge health records.", event_metadata={"doctor_id": doctor.id, "consent_id": consent.id}))
    db.session.commit()
    return jsonify({"consent": consent.to_dict()}), 201


@clinical_bp.delete("/consents/<int:doctor_id>")
@jwt_required()
def revoke_consent(doctor_id):
    user = current_user()
    if not user or user.role != "patient":
        return jsonify({"message": "only patients can revoke consent"}), 403
    consent = db.session.scalar(select(CareConsent).where(CareConsent.patient_id == user.id, CareConsent.doctor_id == doctor_id, CareConsent.revoked_at.is_(None)))
    if not consent:
        return jsonify({"message": "active consent not found"}), 404
    consent.revoked_at = datetime.now(timezone.utc)
    doctor = db.session.get(User, doctor_id)
    db.session.add(HealthTimelineEvent(user_id=user.id, event_type="consent_revoked", title="Clinical access revoked", summary=f"You revoked {doctor.name if doctor else 'the doctor'}'s access to your CareBridge health records.", event_metadata={"doctor_id": doctor_id, "consent_id": consent.id}))
    db.session.commit()
    return jsonify({"consent": consent.to_dict()}), 200


@clinical_bp.get("/patients")
@jwt_required()
def doctor_patients():
    user = current_user()
    if not user or not require_role("doctor"):
        return jsonify({"message": "doctor access required"}), 403
    patients = db.session.scalars(select(User).join(CareConsent, CareConsent.patient_id == User.id).where(CareConsent.doctor_id == user.id, CareConsent.revoked_at.is_(None), User.role == "patient").distinct().order_by(User.name.asc())).all()
    return jsonify({"patients": [{"id": patient.id, "name": patient.name, "email": patient.email} for patient in patients]}), 200


def _patient_records(patient_id):
    medications = db.session.scalars(select(Medication).where(Medication.user_id == patient_id).order_by(Medication.created_at.desc()).limit(50)).all()
    reports = db.session.scalars(select(MedicalReport).where(MedicalReport.user_id == patient_id).order_by(MedicalReport.created_at.desc()).limit(50)).all()
    symptoms = db.session.scalars(select(SymptomCheck).where(SymptomCheck.user_id == patient_id).order_by(SymptomCheck.created_at.desc()).limit(50)).all()
    timeline = db.session.scalars(select(HealthTimelineEvent).where(HealthTimelineEvent.user_id == patient_id).order_by(HealthTimelineEvent.created_at.desc()).limit(50)).all()
    return {"medications": [item.to_dict() for item in medications], "medical_reports": [item.to_dict() for item in reports], "symptom_checks": [item.to_dict() for item in symptoms], "timeline": [item.to_dict() for item in timeline]}


@clinical_bp.get("/patients/<int:patient_id>/records")
@jwt_required()
def patient_records(patient_id):
    user = current_user()
    if not user or not require_role("doctor"):
        return jsonify({"message": "doctor access required"}), 403
    patient = db.session.get(User, patient_id)
    if not patient or patient.role != "patient":
        return jsonify({"message": "patient not found"}), 404
    consent = db.session.scalar(select(CareConsent).where(CareConsent.patient_id == patient_id, CareConsent.doctor_id == user.id, CareConsent.revoked_at.is_(None)))
    if not consent:
        return jsonify({"message": "active patient consent is required"}), 403
    return jsonify({"patient": _patient_dict(patient), "records": _patient_records(patient_id)}), 200


@clinical_bp.post("/patients/<int:patient_id>/reviews")
@jwt_required()
def create_review(patient_id):
    user = current_user()
    if not user or not require_role("doctor"):
        return jsonify({"message": "doctor access required"}), 403
    patient = db.session.get(User, patient_id)
    if not patient or patient.role != "patient":
        return jsonify({"message": "patient not found"}), 404
    consent = db.session.scalar(select(CareConsent).where(CareConsent.patient_id == patient_id, CareConsent.doctor_id == user.id, CareConsent.revoked_at.is_(None)))
    if not consent:
        return jsonify({"message": "active patient consent is required"}), 403
    data = request.get_json(silent=True) or {}
    note = str(data.get("note", "")).strip()
    status = str(data.get("status", "reviewed")).strip().lower()
    if not note:
        return jsonify({"message": "note is required"}), 400
    if len(note) > MAX_NOTE_LENGTH:
        return jsonify({"message": "note must not exceed 5000 characters"}), 400
    if status not in {"reviewed", "follow_up", "urgent_review"}:
        return jsonify({"message": "invalid review status"}), 400
    review = ClinicalReview(patient_id=patient_id, doctor_id=user.id, status=status, note=note)
    db.session.add(review)
    db.session.flush()
    db.session.add(HealthTimelineEvent(user_id=patient_id, event_type="clinical_review", title="Clinical review completed", summary="A doctor added a clinical review to your CareBridge record.", event_metadata={"review_id": review.id, "doctor_id": user.id, "status": status}))
    db.session.commit()
    return jsonify({"review": review.to_dict()}), 201


@clinical_bp.get("/reviews")
@jwt_required()
def reviews():
    user = current_user()
    if not user:
        return jsonify({"message": "user not found"}), 404
    if user.role == "patient":
        items = db.session.scalars(select(ClinicalReview).where(ClinicalReview.patient_id == user.id).order_by(ClinicalReview.created_at.desc()).limit(50)).all()
    elif user.role == "doctor":
        items = db.session.scalars(select(ClinicalReview).where(ClinicalReview.doctor_id == user.id).order_by(ClinicalReview.created_at.desc()).limit(50)).all()
    else:
        return jsonify({"message": "forbidden"}), 403
    return jsonify({"reviews": [item.to_dict() for item in items]}), 200
