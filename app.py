from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, FileField, BooleanField, SubmitField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, NumberRange
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
import re

from models import (db, Officer, Department, Incident, Evidence, SocialMediaProfile, 
                   CommunityReport, User, OfficerDepartmentHistory, TaxpayerCost, 
                   OSINTProfile, AuditLog, ContentModeration, Dispute)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///badapples.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db.init_app(app)

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Utility functions
def log_audit(table_name, record_id, action, field_name=None, old_value=None, new_value=None, user_id=None):
    """Log all database changes for audit trail"""
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    user_agent = request.environ.get('HTTP_USER_AGENT', '')
    
    audit_log = AuditLog(
        table_name=table_name,
        record_id=record_id,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
        user_id=user_id
    )
    db.session.add(audit_log)
    db.session.commit()

def get_client_ip():
    """Get client IP address"""
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    return request.environ.get('REMOTE_ADDR', 'unknown')

def search_social_media(name, department=None):
    """Basic OSINT search for social media profiles"""
    # This is a simplified example - in production, you'd use proper OSINT tools
    results = []
    
    # Search patterns
    search_terms = [name]
    if department:
        search_terms.append(f"{name} {department}")
    
    # This would integrate with actual OSINT tools
    # For now, return mock data
    return results

def calculate_total_costs(officer_id):
    """Calculate total taxpayer costs for an officer"""
    costs = TaxpayerCost.query.filter_by(officer_id=officer_id).all()
    total = sum(cost.amount for cost in costs)
    return total, costs

# Forms
class OfficerForm(FlaskForm):
    badge_number = StringField('Badge Number', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    middle_name = StringField('Middle Name')
    date_of_birth = DateField('Date of Birth')
    department_id = SelectField('Department', coerce=int)
    rank = StringField('Rank')
    hire_date = DateField('Hire Date')
    status = SelectField('Status', choices=[('active', 'Active'), ('suspended', 'Suspended'), ('terminated', 'Terminated'), ('retired', 'Retired')])
    submit = SubmitField('Add Officer')

class IncidentForm(FlaskForm):
    officer_id = SelectField('Officer', coerce=int, validators=[DataRequired()])
    incident_date = DateField('Incident Date', validators=[DataRequired()])
    incident_type = StringField('Incident Type', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location')
    outcome = StringField('Outcome')
    charges_filed = BooleanField('Charges Filed')
    conviction_date = DateField('Conviction Date')
    sentence = TextAreaField('Sentence')
    settlement_amount = StringField('Settlement Amount')
    case_number = StringField('Case Number')
    court_jurisdiction = StringField('Court Jurisdiction')
    source = StringField('Source')
    source_url = StringField('Source URL')
    submit = SubmitField('Add Incident')

class EvidenceForm(FlaskForm):
    officer_id = SelectField('Officer', coerce=int, validators=[DataRequired()])
    incident_id = SelectField('Incident (Optional)', coerce=int)
    evidence_type = SelectField('Evidence Type', choices=[('photo', 'Photo'), ('video', 'Video'), ('document', 'Document'), ('audio', 'Audio')], validators=[DataRequired()])
    file = FileField('File', validators=[DataRequired()])
    description = TextAreaField('Description')
    source = StringField('Source')
    uploader_name = StringField('Your Name')
    uploader_email = StringField('Your Email')
    submit = SubmitField('Upload Evidence')

class CommunityReportForm(FlaskForm):
    incident_id = SelectField('Related Incident (Optional)', coerce=int)
    reporter_name = StringField('Your Name')
    reporter_email = StringField('Your Email')
    reporter_phone = StringField('Your Phone')
    report_type = SelectField('Report Type', choices=[('witness', 'Witness'), ('victim', 'Victim'), ('community', 'Community Member')])
    description = TextAreaField('Description', validators=[DataRequired()])
    incident_date = DateField('Incident Date')
    location = StringField('Location')
    contact_ok = BooleanField('OK to contact for follow-up')
    submit = SubmitField('Submit Report')

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired()])
    jurisdiction = StringField('Jurisdiction')
    location = StringField('Location')
    state = StringField('State')
    website = StringField('Website')
    phone = StringField('Phone')
    submit = SubmitField('Add Department')

class TaxpayerCostForm(FlaskForm):
    officer_id = SelectField('Officer', coerce=int, validators=[DataRequired()])
    cost_type = SelectField('Cost Type', choices=[
        ('lawsuit', 'Lawsuit Settlement'),
        ('fine', 'Fine/Penalty'),
        ('conviction', 'Conviction Costs'),
        ('disciplinary', 'Disciplinary Action'),
        ('training', 'Retraining Costs'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    amount = FloatField('Amount ($)', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[DataRequired()])
    case_number = StringField('Case Number')
    court_jurisdiction = StringField('Court/Jurisdiction')
    date_occurred = DateField('Date Occurred')
    date_paid = DateField('Date Paid')
    source = StringField('Source')
    source_url = StringField('Source URL')
    submit = SubmitField('Add Cost')

class OSINTProfileForm(FlaskForm):
    officer_id = SelectField('Officer', coerce=int, validators=[DataRequired()])
    platform = SelectField('Platform', choices=[
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    username = StringField('Username/Handle')
    profile_url = StringField('Profile URL')
    full_name = StringField('Full Name')
    bio = TextAreaField('Bio/Description')
    location = StringField('Location')
    confidence_score = FloatField('Confidence Score (0-1)', validators=[NumberRange(min=0, max=1)])
    notes = TextAreaField('Notes')
    submit = SubmitField('Add OSINT Profile')

class DisputeForm(FlaskForm):
    table_name = StringField('Record Type', validators=[DataRequired()])
    record_id = IntegerField('Record ID', validators=[DataRequired()])
    dispute_type = SelectField('Dispute Type', choices=[
        ('factual_error', 'Factual Error'),
        ('privacy_violation', 'Privacy Violation'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('duplicate', 'Duplicate Information'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    description = TextAreaField('Dispute Description', validators=[DataRequired()])
    disputer_name = StringField('Your Name')
    disputer_email = StringField('Your Email')
    disputer_phone = StringField('Your Phone')
    evidence_provided = TextAreaField('Evidence Supporting Dispute')
    submit = SubmitField('Submit Dispute')

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Routes
@app.route('/')
def index():
    recent_incidents = Incident.query.order_by(Incident.created_at.desc()).limit(5).all()
    total_officers = Officer.query.count()
    total_incidents = Incident.query.count()
    total_evidence = Evidence.query.count()
    
    return render_template('index.html', 
                         recent_incidents=recent_incidents,
                         total_officers=total_officers,
                         total_incidents=total_incidents,
                         total_evidence=total_evidence)

@app.route('/officers')
def officers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Officer.query
    if search:
        query = query.filter(
            (Officer.first_name.contains(search)) |
            (Officer.last_name.contains(search)) |
            (Officer.badge_number.contains(search))
        )
    
    officers = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('officers.html', officers=officers, search=search)

@app.route('/officer/<int:officer_id>')
def officer_detail(officer_id):
    officer = Officer.query.get_or_404(officer_id)
    incidents = officer.incidents.order_by(Incident.incident_date.desc()).all()
    evidence = officer.evidence.order_by(Evidence.created_at.desc()).all()
    social_media = officer.social_media.all()
    department_history = officer.department_history.order_by(OfficerDepartmentHistory.start_date.desc()).all()
    
    return render_template('officer_detail.html', 
                         officer=officer, 
                         incidents=incidents,
                         evidence=evidence,
                         social_media=social_media,
                         department_history=department_history)

@app.route('/add_officer', methods=['GET', 'POST'])
def add_officer():
    form = OfficerForm()
    form.department_id.choices = [(d.id, d.name) for d in Department.query.all()]
    
    if form.validate_on_submit():
        officer = Officer(
            badge_number=form.badge_number.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            middle_name=form.middle_name.data,
            date_of_birth=form.date_of_birth.data,
            current_department_id=form.department_id.data,
            rank=form.rank.data,
            hire_date=form.hire_date.data,
            status=form.status.data
        )
        db.session.add(officer)
        db.session.commit()
        flash('Officer added successfully!', 'success')
        return redirect(url_for('officer_detail', officer_id=officer.id))
    
    return render_template('add_officer.html', form=form)

@app.route('/add_incident', methods=['GET', 'POST'])
def add_incident():
    form = IncidentForm()
    form.officer_id.choices = [(o.id, f"{o.first_name} {o.last_name} ({o.badge_number})") for o in Officer.query.all()]
    
    if form.validate_on_submit():
        incident = Incident(
            officer_id=form.officer_id.data,
            incident_date=form.incident_date.data,
            incident_type=form.incident_type.data,
            description=form.description.data,
            location=form.location.data,
            outcome=form.outcome.data,
            charges_filed=form.charges_filed.data,
            conviction_date=form.conviction_date.data,
            sentence=form.sentence.data,
            settlement_amount=float(form.settlement_amount.data) if form.settlement_amount.data else None,
            case_number=form.case_number.data,
            court_jurisdiction=form.court_jurisdiction.data,
            source=form.source.data,
            source_url=form.source_url.data
        )
        db.session.add(incident)
        db.session.commit()
        flash('Incident added successfully!', 'success')
        return redirect(url_for('officer_detail', officer_id=incident.officer_id))
    
    return render_template('add_incident.html', form=form)

@app.route('/add_evidence', methods=['GET', 'POST'])
def add_evidence():
    form = EvidenceForm()
    form.officer_id.choices = [(o.id, f"{o.first_name} {o.last_name} ({o.badge_number})") for o in Officer.query.all()]
    form.incident_id.choices = [(0, 'Not related to specific incident')] + [(i.id, f"{i.incident_type} - {i.incident_date}") for i in Incident.query.all()]
    
    if form.validate_on_submit():
        file = form.file.data
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            evidence = Evidence(
                officer_id=form.officer_id.data,
                incident_id=form.incident_id.data if form.incident_id.data and form.incident_id.data != 0 else None,
                evidence_type=form.evidence_type.data,
                file_path=file_path,
                file_name=filename,
                file_size=os.path.getsize(file_path),
                description=form.description.data,
                source=form.source.data,
                uploader_name=form.uploader_name.data,
                uploader_email=form.uploader_email.data
            )
            db.session.add(evidence)
            db.session.commit()
            flash('Evidence uploaded successfully!', 'success')
            return redirect(url_for('officer_detail', officer_id=evidence.officer_id))
    
    return render_template('add_evidence.html', form=form)

@app.route('/community_report', methods=['GET', 'POST'])
def community_report():
    form = CommunityReportForm()
    form.incident_id.choices = [(0, 'Not related to specific incident')] + [(i.id, f"{i.incident_type} - {i.incident_date}") for i in Incident.query.all()]
    
    if form.validate_on_submit():
        report = CommunityReport(
            incident_id=form.incident_id.data if form.incident_id.data and form.incident_id.data != 0 else None,
            reporter_name=form.reporter_name.data,
            reporter_email=form.reporter_email.data,
            reporter_phone=form.reporter_phone.data,
            report_type=form.report_type.data,
            description=form.description.data,
            incident_date=form.incident_date.data,
            location=form.location.data,
            contact_ok=form.contact_ok.data
        )
        db.session.add(report)
        db.session.commit()
        flash('Community report submitted successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('community_report.html', form=form)

@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    form = DepartmentForm()
    
    if form.validate_on_submit():
        department = Department(
            name=form.name.data,
            jurisdiction=form.jurisdiction.data,
            location=form.location.data,
            state=form.state.data,
            website=form.website.data,
            phone=form.phone.data
        )
        db.session.add(department)
        db.session.commit()
        flash('Department added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_department.html', form=form)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
    
    # Search officers
    officers = Officer.query.filter(
        (Officer.first_name.contains(query)) |
        (Officer.last_name.contains(query)) |
        (Officer.badge_number.contains(query))
    ).all()
    
    # Search incidents
    incidents = Incident.query.filter(
        (Incident.incident_type.contains(query)) |
        (Incident.description.contains(query)) |
        (Incident.location.contains(query))
    ).all()
    
    return render_template('search_results.html', 
                         query=query, 
                         officers=officers, 
                         incidents=incidents)

@app.route('/download_evidence/<int:evidence_id>')
def download_evidence(evidence_id):
    evidence = Evidence.query.get_or_404(evidence_id)
    if os.path.exists(evidence.file_path):
        return send_file(evidence.file_path, as_attachment=True, download_name=evidence.file_name)
    else:
        abort(404)

@app.route('/export_officer/<int:officer_id>')
def export_officer(officer_id):
    officer = Officer.query.get_or_404(officer_id)
    incidents = officer.incidents.all()
    evidence = officer.evidence.all()
    total_cost, costs = calculate_total_costs(officer_id)
    
    export_data = {
        'officer': {
            'name': f"{officer.first_name} {officer.last_name}",
            'badge_number': officer.badge_number,
            'department': officer.current_department.name if officer.current_department else None,
            'status': officer.status
        },
        'incidents': [
            {
                'date': incident.incident_date.isoformat(),
                'type': incident.incident_type,
                'description': incident.description,
                'outcome': incident.outcome,
                'charges_filed': incident.charges_filed,
                'conviction_date': incident.conviction_date.isoformat() if incident.conviction_date else None,
                'sentence': incident.sentence,
                'settlement_amount': incident.settlement_amount
            } for incident in incidents
        ],
        'evidence_count': len(evidence),
        'total_taxpayer_cost': total_cost,
        'costs': [
            {
                'type': cost.cost_type,
                'amount': cost.amount,
                'description': cost.description,
                'date': cost.date_occurred.isoformat() if cost.date_occurred else None
            } for cost in costs
        ]
    }
    
    return jsonify(export_data)

# New routes for advanced features

@app.route('/add_taxpayer_cost', methods=['GET', 'POST'])
def add_taxpayer_cost():
    form = TaxpayerCostForm()
    form.officer_id.choices = [(o.id, f"{o.first_name} {o.last_name} ({o.badge_number})") for o in Officer.query.all()]
    
    if form.validate_on_submit():
        cost = TaxpayerCost(
            officer_id=form.officer_id.data,
            cost_type=form.cost_type.data,
            amount=form.amount.data,
            description=form.description.data,
            case_number=form.case_number.data,
            court_jurisdiction=form.court_jurisdiction.data,
            date_occurred=form.date_occurred.data,
            date_paid=form.date_paid.data,
            source=form.source.data,
            source_url=form.source_url.data
        )
        db.session.add(cost)
        db.session.commit()
        
        # Log the audit trail
        log_audit('taxpayer_costs', cost.id, 'create', user_id=session.get('user_id'))
        
        flash('Taxpayer cost added successfully!', 'success')
        return redirect(url_for('officer_detail', officer_id=cost.officer_id))
    
    return render_template('add_taxpayer_cost.html', form=form)

@app.route('/add_osint_profile', methods=['GET', 'POST'])
def add_osint_profile():
    form = OSINTProfileForm()
    form.officer_id.choices = [(o.id, f"{o.first_name} {o.last_name} ({o.badge_number})") for o in Officer.query.all()]
    
    if form.validate_on_submit():
        profile = OSINTProfile(
            officer_id=form.officer_id.data,
            platform=form.platform.data,
            username=form.username.data,
            profile_url=form.profile_url.data,
            full_name=form.full_name.data,
            bio=form.bio.data,
            location=form.location.data,
            confidence_score=form.confidence_score.data,
            notes=form.notes.data
        )
        db.session.add(profile)
        db.session.commit()
        
        # Log the audit trail
        log_audit('osint_profiles', profile.id, 'create', user_id=session.get('user_id'))
        
        flash('OSINT profile added successfully!', 'success')
        return redirect(url_for('officer_detail', officer_id=profile.officer_id))
    
    return render_template('add_osint_profile.html', form=form)

@app.route('/dispute/<string:table_name>/<int:record_id>', methods=['GET', 'POST'])
def dispute_record(table_name, record_id):
    form = DisputeForm()
    form.table_name.data = table_name
    form.record_id.data = record_id
    
    if form.validate_on_submit():
        dispute = Dispute(
            table_name=table_name,
            record_id=record_id,
            dispute_type=form.dispute_type.data,
            description=form.description.data,
            disputer_name=form.disputer_name.data,
            disputer_email=form.disputer_email.data,
            disputer_phone=form.disputer_phone.data,
            evidence_provided=form.evidence_provided.data,
            ip_address=get_client_ip()
        )
        db.session.add(dispute)
        db.session.commit()
        
        # Log the audit trail
        log_audit(table_name, record_id, 'dispute', new_value=f"Disputed: {form.dispute_type.data}")
        
        flash('Dispute submitted successfully! It will be reviewed by moderators.', 'success')
        return redirect(url_for('index'))
    
    return render_template('dispute_record.html', form=form, table_name=table_name, record_id=record_id)

@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Get pending items for moderation
    pending_incidents = Incident.query.filter_by(verified=False).count()
    pending_evidence = Evidence.query.filter_by(verified=False).count()
    pending_reports = CommunityReport.query.filter_by(verified=False).count()
    pending_disputes = Dispute.query.filter_by(status='pending').count()
    
    # Get recent activity
    recent_audit_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('admin_panel.html',
                         pending_incidents=pending_incidents,
                         pending_evidence=pending_evidence,
                         pending_reports=pending_reports,
                         pending_disputes=pending_disputes,
                         recent_audit_logs=recent_audit_logs)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.role in ['admin', 'moderator']:
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid credentials or insufficient privileges.', 'error')
    
    return render_template('admin_login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/moderate/<string:table_name>/<int:record_id>')
def moderate_record(table_name, record_id):
    if not session.get('is_admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    # Get the record based on table name
    if table_name == 'incidents':
        record = Incident.query.get_or_404(record_id)
    elif table_name == 'evidence':
        record = Evidence.query.get_or_404(record_id)
    elif table_name == 'community_reports':
        record = CommunityReport.query.get_or_404(record_id)
    else:
        flash('Invalid record type.', 'error')
        return redirect(url_for('admin_panel'))
    
    return render_template('moderate_record.html', record=record, table_name=table_name)

@app.route('/admin/approve/<string:table_name>/<int:record_id>')
def approve_record(table_name, record_id):
    if not session.get('is_admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    # Update the record
    if table_name == 'incidents':
        record = Incident.query.get_or_404(record_id)
        record.verified = True
    elif table_name == 'evidence':
        record = Evidence.query.get_or_404(record_id)
        record.verified = True
    elif table_name == 'community_reports':
        record = CommunityReport.query.get_or_404(record_id)
        record.verified = True
    
    db.session.commit()
    
    # Log the audit trail
    log_audit(table_name, record_id, 'approve', user_id=session.get('user_id'))
    
    flash('Record approved successfully!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/reject/<string:table_name>/<int:record_id>')
def reject_record(table_name, record_id):
    if not session.get('is_admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    # Create moderation record
    moderation = ContentModeration(
        table_name=table_name,
        record_id=record_id,
        status='rejected',
        moderator_id=session.get('user_id'),
        reason_code=request.args.get('reason', 'inappropriate')
    )
    db.session.add(moderation)
    db.session.commit()
    
    # Log the audit trail
    log_audit(table_name, record_id, 'reject', user_id=session.get('user_id'))
    
    flash('Record rejected successfully!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/osint_search')
def osint_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # Basic OSINT search (in production, integrate with real OSINT tools)
    results = search_social_media(query)
    return jsonify(results)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
