from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Officer(db.Model):
    __tablename__ = 'officers'
    
    id = db.Column(db.Integer, primary_key=True)
    badge_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    current_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    current_rank = db.Column(db.String(50))
    hire_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, suspended, terminated, retired
    photo_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    current_department = db.relationship('Department', backref='current_officers')
    incidents = db.relationship('Incident', backref='officer', lazy='dynamic')
    evidence = db.relationship('Evidence', backref='officer', lazy='dynamic')
    social_media = db.relationship('SocialMediaProfile', backref='officer', lazy='dynamic')
    department_history = db.relationship('OfficerDepartmentHistory', backref='officer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Officer {self.first_name} {self.last_name} ({self.badge_number})>'

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    jurisdiction = db.Column(db.String(100))  # city, county, state, federal
    location = db.Column(db.String(200))
    state = db.Column(db.String(2))
    website = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    officers = db.relationship('Officer', backref='department', lazy='dynamic')
    department_history = db.relationship('OfficerDepartmentHistory', backref='department', lazy='dynamic')
    
    def __repr__(self):
        return f'<Department {self.name}>'

class OfficerDepartmentHistory(db.Model):
    __tablename__ = 'officer_department_history'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    rank = db.Column(db.String(50))
    reason_for_transfer = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OfficerDepartmentHistory {self.officer_id} -> {self.department_id}>'

class Incident(db.Model):
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    incident_date = db.Column(db.Date, nullable=False)
    incident_type = db.Column(db.String(100), nullable=False)  # excessive force, misconduct, etc.
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200))
    outcome = db.Column(db.String(100))  # conviction, acquittal, settlement, pending
    charges_filed = db.Column(db.Boolean, default=False)
    conviction_date = db.Column(db.Date)
    sentence = db.Column(db.Text)
    settlement_amount = db.Column(db.Float)
    case_number = db.Column(db.String(50))
    court_jurisdiction = db.Column(db.String(100))
    source = db.Column(db.String(100))  # news article, court record, community report
    source_url = db.Column(db.String(500))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evidence = db.relationship('Evidence', backref='incident', lazy='dynamic')
    community_reports = db.relationship('CommunityReport', backref='incident', lazy='dynamic')
    
    def __repr__(self):
        return f'<Incident {self.incident_type} - {self.incident_date}>'

class Evidence(db.Model):
    __tablename__ = 'evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'))
    evidence_type = db.Column(db.String(50), nullable=False)  # photo, video, document, audio
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    source = db.Column(db.String(100))  # community upload, news media, court record
    uploader_name = db.Column(db.String(100))
    uploader_email = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Evidence {self.evidence_type} - {self.file_name}>'

class SocialMediaProfile(db.Model):
    __tablename__ = 'social_media_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, instagram, etc.
    username = db.Column(db.String(100), nullable=False)
    profile_url = db.Column(db.String(500))
    last_checked = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SocialMediaProfile {self.platform}: {self.username}>'

class CommunityReport(db.Model):
    __tablename__ = 'community_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'))
    reporter_name = db.Column(db.String(100))
    reporter_email = db.Column(db.String(100))
    reporter_phone = db.Column(db.String(20))
    report_type = db.Column(db.String(50))  # witness, victim, community member
    description = db.Column(db.Text, nullable=False)
    incident_date = db.Column(db.Date)
    location = db.Column(db.String(200))
    contact_ok = db.Column(db.Boolean, default=False)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CommunityReport from {self.reporter_name}>'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, moderator, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class TaxpayerCost(db.Model):
    __tablename__ = 'taxpayer_costs'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    cost_type = db.Column(db.String(50), nullable=False)  # lawsuit, settlement, fine, conviction
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    case_number = db.Column(db.String(100))
    court_jurisdiction = db.Column(db.String(100))
    date_occurred = db.Column(db.Date)
    date_paid = db.Column(db.Date)
    source = db.Column(db.String(200))
    source_url = db.Column(db.String(500))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    officer = db.relationship('Officer', backref='taxpayer_costs')
    
    def __repr__(self):
        return f'<TaxpayerCost {self.cost_type}: ${self.amount}>'

class OSINTProfile(db.Model):
    __tablename__ = 'osint_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, instagram, linkedin, etc.
    username = db.Column(db.String(100))
    profile_url = db.Column(db.String(500))
    full_name = db.Column(db.String(200))
    profile_picture_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    location = db.Column(db.String(200))
    last_activity = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    confidence_score = db.Column(db.Float)  # 0-1 confidence that this is the right person
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    officer = db.relationship('Officer', backref='osint_profiles')
    
    def __repr__(self):
        return f'<OSINTProfile {self.platform}: {self.username}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)  # create, update, delete, view
    field_name = db.Column(db.String(50))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.table_name}:{self.record_id}>'

class ContentModeration(db.Model):
    __tablename__ = 'content_moderation'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pending, approved, rejected, disputed
    moderator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reason_code = db.Column(db.String(50))  # insufficient_evidence, duplicate, inappropriate, etc.
    notes = db.Column(db.Text)
    disputed_by = db.Column(db.String(100))  # name/email of person disputing
    dispute_reason = db.Column(db.Text)
    dispute_date = db.Column(db.DateTime)
    resolution_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    moderator = db.relationship('User', backref='moderation_actions')
    
    def __repr__(self):
        return f'<ContentModeration {self.status} for {self.table_name}:{self.record_id}>'

class Dispute(db.Model):
    __tablename__ = 'disputes'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    dispute_type = db.Column(db.String(50), nullable=False)  # factual_error, privacy_violation, harassment, etc.
    description = db.Column(db.Text, nullable=False)
    disputer_name = db.Column(db.String(100))
    disputer_email = db.Column(db.String(100))
    disputer_phone = db.Column(db.String(20))
    evidence_provided = db.Column(db.Text)  # description of evidence supporting dispute
    status = db.Column(db.String(20), default='pending')  # pending, under_review, resolved, dismissed
    resolution = db.Column(db.Text)  # moderator's resolution notes
    moderator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolution_date = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    moderator = db.relationship('User', backref='dispute_resolutions')
    
    def __repr__(self):
        return f'<Dispute {self.dispute_type} for {self.table_name}:{self.record_id}>'
