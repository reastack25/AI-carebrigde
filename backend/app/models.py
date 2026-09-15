from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="patient")
    specialty = db.Column(db.String(120), nullable=True)
    license_number = db.Column(db.String(120), nullable=True)
    facility = db.Column(db.String(160), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role, "specialty": self.specialty or "", "license_number": self.license_number or "", "facility": self.facility or "", "created_at": self.created_at.isoformat()}


class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(30), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    emergency_contact = db.Column(db.String(120), nullable=True)
    user = db.relationship("User", backref=db.backref("patient_profile", uselist=False))


class Conversation(db.Model):
    __tablename__ = "conversations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, default="Health conversation")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    messages = db.relationship("Message", backref="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def to_dict(self, include_messages=True):
        result = {"id": self.id, "title": self.title, "created_at": self.created_at.isoformat()}
        if include_messages: result["messages"] = [message.to_dict() for message in self.messages]
        return result


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), nullable=False, default="en")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {"id": self.id, "sender": self.sender, "content": self.content, "language": self.language, "created_at": self.created_at.isoformat()}


class SymptomCheck(db.Model):
    __tablename__ = "symptom_checks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=True, index=True)
    symptoms = db.Column(db.Text, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.String(200), nullable=True)
    urgency = db.Column(db.String(30), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    possible_explanations = db.Column(db.JSON, nullable=False, default=list)
    next_steps = db.Column(db.JSON, nullable=False, default=list)
    red_flags = db.Column(db.JSON, nullable=False, default=list)
    language = db.Column(db.String(10), nullable=False, default="en")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {"id": self.id, "conversation_id": self.conversation_id, "symptoms": self.symptoms, "age": self.age, "duration": self.duration, "urgency": self.urgency, "summary": self.summary, "possible_explanations": self.possible_explanations or [], "next_steps": self.next_steps or [], "red_flags": self.red_flags or [], "language": self.language, "created_at": self.created_at.isoformat()}


class MedicalReport(db.Model):
    __tablename__ = "medical_reports"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    instruction = db.Column(db.String(1000), nullable=True)
    summary = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), nullable=False, default="en")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {"id": self.id, "conversation_id": self.conversation_id, "filename": self.filename, "mime_type": self.mime_type, "instruction": self.instruction or "", "summary": self.summary, "language": self.language, "created_at": self.created_at.isoformat()}


class Medication(db.Model):
    __tablename__ = "medications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    dosage = db.Column(db.String(255), nullable=True)
    frequency = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.String(255), nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    warnings = db.Column(db.JSON, nullable=False, default=list)
    source_filename = db.Column(db.String(255), nullable=True)
    language = db.Column(db.String(10), nullable=False, default="en")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {"id": self.id, "conversation_id": self.conversation_id, "name": self.name, "dosage": self.dosage or "", "frequency": self.frequency or "", "duration": self.duration or "", "instructions": self.instructions or "", "warnings": self.warnings or [], "source_filename": self.source_filename or "", "language": self.language, "created_at": self.created_at.isoformat()}


class HealthTimelineEvent(db.Model):
    __tablename__ = "health_timeline_events"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=True, index=True)
    event_type = db.Column(db.String(40), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    event_metadata = db.Column("metadata", db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {"id": self.id, "event_type": self.event_type, "title": self.title, "summary": self.summary, "metadata": self.event_metadata or {}, "conversation_id": self.conversation_id, "created_at": self.created_at.isoformat()}


class CareConsent(db.Model):
    __tablename__ = "care_consents"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    granted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {"id": self.id, "patient_id": self.patient_id, "doctor_id": self.doctor_id, "granted_at": self.granted_at.isoformat(), "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None, "active": self.revoked_at is None}


class ClinicalReview(db.Model):
    __tablename__ = "clinical_reviews"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="reviewed")
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {"id": self.id, "patient_id": self.patient_id, "doctor_id": self.doctor_id, "status": self.status, "note": self.note, "created_at": self.created_at.isoformat()}
