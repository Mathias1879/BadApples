from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, FileField, BooleanField, SubmitField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, NumberRange
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
import re
import secrets
import csv
from io import StringIO

from models import (db, Officer, Department, Incident, Evidence, SocialMediaProfile, 
                   CommunityReport, User, OfficerDepartmentHistory, TaxpayerCost, 
                   OSINTProfile, AuditLog, ContentModeration, Dispute, Vehicle)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///badapples.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@badapples.org')

# OSINT API Keys (for future implementation)
app.config['TWITTER_API_KEY'] = os.getenv('TWITTER_API_KEY')
app.config['TWITTER_API_SECRET'] = os.getenv('TWITTER_API_SECRET')
app.config['FACEBOOK_API_KEY'] = os.getenv('FACEBOOK_API_KEY')

# Initialize extensions
db.init_app(app)
mail = Mail(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com;"
    return response

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
    """Enhanced OSINT search for social media profiles"""
    results = []
    
    # Search patterns
    search_terms = [name]
    if department:
        search_terms.append(f"{name} {department}")
    
    # Twitter/X API integration (if configured)
    if app.config.get('TWITTER_API_KEY'):
        try:
            # This is where you'd integrate with Twitter API
            # For now, this is a placeholder for future implementation
            twitter_results = search_twitter(name, department)
            results.extend(twitter_results)
        except Exception as e:
            print(f"Twitter search error: {e}")
    
    # Facebook API integration (if configured)
    if app.config.get('FACEBOOK_API_KEY'):
        try:
            # This is where you'd integrate with Facebook API
            # For now, this is a placeholder for future implementation
            facebook_results = search_facebook(name, department)
            results.extend(facebook_results)
        except Exception as e:
            print(f"Facebook search error: {e}")
    
    # Google Search fallback (public information only)
    try:
        google_results = google_search_public_info(name, department)
        results.extend(google_results)
    except Exception as e:
        print(f"Google search error: {e}")
    
    return results

def search_twitter(name, department=None):
    """Search Twitter/X for profiles (requires API key)"""
    # Placeholder for Twitter API integration
    # In production, use tweepy or similar library
    return []

def search_facebook(name, department=None):
    """Search Facebook for profiles (requires API key)"""
    # Placeholder for Facebook API integration
    # In production, use facebook-sdk or similar library
    return []

def google_search_public_info(name, department=None):
    """Search Google for public information"""
    # This uses basic web scraping for publicly available information
    # In production, use Google Custom Search API
    results = []
    
    try:
        search_query = f"{name}"
        if department:
            search_query += f" {department}"
        search_query += " police officer"
        
        # This is a basic example - in production use proper APIs
        # For now, return empty to avoid scraping issues
        
    except Exception as e:
        print(f"Google search error: {e}")
    
    return results

@app.route('/api/osint_scan/<int:officer_id>', methods=['POST'])
def api_osint_scan(officer_id):
    """Automated OSINT scan for an officer"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Access denied'}), 403
    
    officer = Officer.query.get_or_404(officer_id)
    department_name = officer.current_department.name if officer.current_department else None
    
    # Perform OSINT search
    results = search_social_media(
        f"{officer.first_name} {officer.last_name}",
        department_name
    )
    
    # Save results to database
    saved_count = 0
    for result in results:
        # Check if profile already exists
        existing = OSINTProfile.query.filter_by(
            officer_id=officer_id,
            platform=result.get('platform'),
            username=result.get('username')
        ).first()
        
        if not existing:
            profile = OSINTProfile(
                officer_id=officer_id,
                platform=result.get('platform'),
                username=result.get('username'),
                profile_url=result.get('url'),
                full_name=result.get('name'),
                confidence_score=result.get('confidence', 0.5),
                notes=f"Automatically discovered via OSINT scan"
            )
            db.session.add(profile)
            saved_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'officer_id': officer_id,
        'results_found': len(results),
        'profiles_saved': saved_count,
        'message': f'OSINT scan complete. Found {len(results)} results, saved {saved_count} new profiles.'
    })

def calculate_total_costs(officer_id):
    """Calculate total taxpayer costs for an officer"""
    costs = TaxpayerCost.query.filter_by(officer_id=officer_id).all()
    total = sum(cost.amount for cost in costs)
    return total, costs

def send_email_notification(subject, recipients, body_text, body_html=None):
    """Send email notification"""
    try:
        if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
            # Email not configured, skip silently
            return False
            
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            body=body_text,
            html=body_html or body_text
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def notify_admins_new_report(report_type, report_id):
    """Notify admins of new community report"""
    admin_users = User.query.filter(User.role.in_(['admin', 'moderator'])).all()
    if not admin_users:
        return
    
    recipients = [user.email for user in admin_users if user.email]
    if not recipients:
        return
    
    subject = f"New {report_type.title()} Report Submitted"
    body = f"""
A new {report_type} report has been submitted to the Bad Apples Database.

Report ID: {report_id}
Type: {report_type}

Please review this report in the admin panel:
{url_for('admin_panel', _external=True)}

---
This is an automated notification from the Bad Apples Database.
    """
    
    send_email_notification(subject, recipients, body)

def notify_admins_new_dispute(dispute_id, table_name, record_id):
    """Notify admins of new dispute"""
    admin_users = User.query.filter(User.role.in_(['admin', 'moderator'])).all()
    if not admin_users:
        return
    
    recipients = [user.email for user in admin_users if user.email]
    if not recipients:
        return
    
    subject = f"New Dispute Submitted - {table_name} #{record_id}"
    body = f"""
A new dispute has been submitted to the Bad Apples Database.

Dispute ID: {dispute_id}
Record Type: {table_name}
Record ID: {record_id}

Please review this dispute in the admin panel:
{url_for('admin_panel', _external=True)}

---
This is an automated notification from the Bad Apples Database.
    """
    
    send_email_notification(subject, recipients, body)

def notify_dispute_resolution(dispute, resolution_status):
    """Notify disputer of resolution"""
    if not dispute.disputer_email:
        return
    
    subject = f"Dispute Resolution - {dispute.table_name} #{dispute.record_id}"
    body = f"""
Your dispute has been reviewed and {resolution_status}.

Dispute ID: {dispute.id}
Record Type: {dispute.table_name}
Record ID: {dispute.record_id}
Status: {resolution_status.upper()}

{f"Resolution: {dispute.resolution}" if dispute.resolution else ""}

Thank you for helping us maintain the accuracy of the Bad Apples Database.

---
This is an automated notification from the Bad Apples Database.
    """
    
    send_email_notification(subject, [dispute.disputer_email], body)

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

class AdminRegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])
    confirm_password = StringField('Confirm Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('moderator', 'Moderator'), ('admin', 'Administrator')], validators=[DataRequired()])
    submit = SubmitField('Register Admin User')

class VehicleForm(FlaskForm):
    officer_id = SelectField('Officer', coerce=int, validators=[DataRequired()])
    vehicle_type = SelectField('Vehicle Type', choices=[
        ('patrol', 'Patrol Vehicle'),
        ('personal', 'Personal Vehicle'),
        ('unmarked', 'Unmarked'),
        ('undercover', 'Undercover'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    make = StringField('Make', validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    year = IntegerField('Year', validators=[Optional(), NumberRange(min=1900, max=2030)])
    color = StringField('Color', validators=[DataRequired()])
    license_plate = StringField('License Plate')
    state = StringField('State (2 letters)', validators=[Optional()])
    vin = StringField('VIN (17 characters)', validators=[Optional()])
    is_unmarked = BooleanField('Is Unmarked Vehicle')
    description = TextAreaField('Description/Notes')
    last_seen_location = StringField('Last Seen Location')
    last_seen_date = DateField('Last Seen Date', validators=[Optional()])
    source = StringField('Source of Information')
    submit = SubmitField('Add Vehicle')

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
    vehicles = [v for v in officer.vehicles if v.is_active]
    total_cost, costs = calculate_total_costs(officer_id)
    
    return render_template('officer_detail.html', 
                         officer=officer, 
                         incidents=incidents,
                         evidence=evidence,
                         social_media=social_media,
                         department_history=department_history,
                         vehicles=vehicles,
                         total_cost=total_cost,
                         costs=costs)

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
@limiter.limit("10 per hour")
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
        
        # Send email notification to admins
        notify_admins_new_report('community_report', report.id)
        
        flash('Community report submitted successfully! Administrators have been notified.', 'success')
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
@limiter.limit("30 per minute")
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

@app.route('/export_officers_csv')
def export_officers_csv():
    """Export all officers to CSV format"""
    officers = Officer.query.all()
    
    # Create CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    
    # Write header
    writer.writerow(['Badge Number', 'First Name', 'Last Name', 'Department', 'Rank', 'Status', 'Hire Date', 'Incident Count'])
    
    # Write data
    for officer in officers:
        writer.writerow([
            officer.badge_number,
            officer.first_name,
            officer.last_name,
            officer.current_department.name if officer.current_department else '',
            officer.rank or '',
            officer.status,
            officer.hire_date.strftime('%Y-%m-%d') if officer.hire_date else '',
            officer.incidents.count()
        ])
    
    # Create response
    output = si.getvalue()
    si.close()
    
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'officers_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/export_incidents_csv')
def export_incidents_csv():
    """Export all incidents to CSV format"""
    incidents = Incident.query.all()
    
    # Create CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    
    # Write header
    writer.writerow(['Date', 'Type', 'Officer Name', 'Badge Number', 'Department', 'Location', 'Description', 'Outcome', 'Charges Filed', 'Settlement Amount', 'Source'])
    
    # Write data
    for incident in incidents:
        writer.writerow([
            incident.incident_date.strftime('%Y-%m-%d'),
            incident.incident_type,
            f"{incident.officer.first_name} {incident.officer.last_name}",
            incident.officer.badge_number,
            incident.officer.current_department.name if incident.officer.current_department else '',
            incident.location or '',
            incident.description,
            incident.outcome or '',
            'Yes' if incident.charges_filed else 'No',
            incident.settlement_amount or '',
            incident.source or ''
        ])
    
    # Create response
    output = si.getvalue()
    si.close()
    
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'incidents_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/export_vehicles_csv')
def export_vehicles_csv():
    """Export all vehicles to CSV format"""
    vehicles = Vehicle.query.filter_by(is_active=True).all()
    
    # Create CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    
    # Write header
    writer.writerow(['Officer Name', 'Badge Number', 'Vehicle Type', 'Make', 'Model', 'Year', 'Color', 'License Plate', 'State', 'VIN', 'Is Unmarked', 'Last Seen Location', 'Last Seen Date'])
    
    # Write data
    for vehicle in vehicles:
        writer.writerow([
            f"{vehicle.officer.first_name} {vehicle.officer.last_name}",
            vehicle.officer.badge_number,
            vehicle.vehicle_type,
            vehicle.make,
            vehicle.model,
            vehicle.year or '',
            vehicle.color,
            vehicle.license_plate or '',
            vehicle.state or '',
            vehicle.vin or '',
            'Yes' if vehicle.is_unmarked else 'No',
            vehicle.last_seen_location or '',
            vehicle.last_seen_date.strftime('%Y-%m-%d') if vehicle.last_seen_date else ''
        ])
    
    # Create response
    output = si.getvalue()
    si.close()
    
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'vehicles_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

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
        
        # Send email notification to admins
        notify_admins_new_dispute(dispute.id, table_name, record_id)
        
        flash('Dispute submitted successfully! It will be reviewed by moderators and you will be notified of the resolution.', 'success')
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
@limiter.limit("5 per minute")
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

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    # Only allow admins to register new admin/moderator users
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('admin_login'))
    
    # Check if current user is admin (not just moderator)
    current_user = User.query.get(session.get('user_id'))
    if not current_user or current_user.role != 'admin':
        flash('Access denied. Only administrators can register new users.', 'error')
        return redirect(url_for('admin_panel'))
    
    form = AdminRegisterForm()
    
    if form.validate_on_submit():
        # Check if passwords match
        if form.password.data != form.confirm_password.data:
            flash('Passwords do not match.', 'error')
            return render_template('admin_register.html', form=form)
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists.', 'error')
            return render_template('admin_register.html', form=form)
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already exists.', 'error')
            return render_template('admin_register.html', form=form)
        
        # Create new user
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            is_active=True
        )
        new_user.set_password(form.password.data)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log the action
        log_audit('users', new_user.id, 'create', user_id=session.get('user_id'))
        
        flash(f'{form.role.data.title()} user {form.username.data} created successfully!', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('admin_register.html', form=form)

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

# API Endpoints
@app.route('/api/live_search')
@limiter.limit("60 per minute")
def api_live_search():
    """Real-time search API for AJAX requests"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 3:
        return jsonify({'officers': [], 'incidents': [], 'vehicles': []})
    
    # Search officers
    officers = Officer.query.filter(
        (Officer.first_name.contains(query)) |
        (Officer.last_name.contains(query)) |
        (Officer.badge_number.contains(query))
    ).limit(5).all()
    
    # Search incidents
    incidents = Incident.query.filter(
        (Incident.incident_type.contains(query)) |
        (Incident.description.contains(query))
    ).limit(5).all()
    
    # Search vehicles
    vehicles = Vehicle.query.filter(
        (Vehicle.make.contains(query)) |
        (Vehicle.model.contains(query)) |
        (Vehicle.license_plate.contains(query)) |
        (Vehicle.color.contains(query))
    ).filter_by(is_active=True).limit(5).all()
    
    return jsonify({
        'officers': [{
            'id': o.id,
            'first_name': o.first_name,
            'last_name': o.last_name,
            'badge_number': o.badge_number
        } for o in officers],
        'incidents': [{
            'id': i.id,
            'incident_type': i.incident_type,
            'officer_id': i.officer_id,
            'officer_name': f"{i.officer.first_name} {i.officer.last_name}"
        } for i in incidents],
        'vehicles': [{
            'id': v.id,
            'make': v.make,
            'model': v.model,
            'license_plate': v.license_plate,
            'officer_id': v.officer_id
        } for v in vehicles]
    })

@app.route('/api/officers', methods=['GET'])
def api_get_officers():
    """REST API: Get all officers"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    officers = Officer.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'data': [{
            'id': o.id,
            'badge_number': o.badge_number,
            'first_name': o.first_name,
            'last_name': o.last_name,
            'department': o.current_department.name if o.current_department else None,
            'status': o.status,
            'incident_count': o.incidents.count()
        } for o in officers.items],
        'page': officers.page,
        'per_page': officers.per_page,
        'total': officers.total,
        'pages': officers.pages
    })

@app.route('/api/officer/<int:officer_id>', methods=['GET'])
def api_get_officer(officer_id):
    """REST API: Get single officer"""
    officer = Officer.query.get_or_404(officer_id)
    
    return jsonify({
        'id': officer.id,
        'badge_number': officer.badge_number,
        'first_name': officer.first_name,
        'last_name': officer.last_name,
        'middle_name': officer.middle_name,
        'department': officer.current_department.name if officer.current_department else None,
        'rank': officer.rank,
        'status': officer.status,
        'hire_date': officer.hire_date.isoformat() if officer.hire_date else None,
        'incidents': [{
            'id': i.id,
            'date': i.incident_date.isoformat(),
            'type': i.incident_type,
            'description': i.description
        } for i in officer.incidents.all()]
    })

@app.route('/api/incidents', methods=['GET'])
def api_get_incidents():
    """REST API: Get all incidents"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    incidents = Incident.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'data': [{
            'id': i.id,
            'officer_id': i.officer_id,
            'officer_name': f"{i.officer.first_name} {i.officer.last_name}",
            'date': i.incident_date.isoformat(),
            'type': i.incident_type,
            'location': i.location,
            'description': i.description[:200]
        } for i in incidents.items],
        'page': incidents.page,
        'per_page': incidents.per_page,
        'total': incidents.total,
        'pages': incidents.pages
    })

@app.route('/admin/batch_approve', methods=['POST'])
def batch_approve():
    """Batch approve multiple records"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    table_name = data.get('table_name')
    record_ids = data.get('record_ids', [])
    
    if not table_name or not record_ids:
        return jsonify({'error': 'Missing parameters'}), 400
    
    approved_count = 0
    
    for record_id in record_ids:
        if table_name == 'incidents':
            record = Incident.query.get(record_id)
            if record:
                record.verified = True
                approved_count += 1
        elif table_name == 'evidence':
            record = Evidence.query.get(record_id)
            if record:
                record.verified = True
                approved_count += 1
        elif table_name == 'community_reports':
            record = CommunityReport.query.get(record_id)
            if record:
                record.verified = True
                approved_count += 1
    
    db.session.commit()
    
    # Log the batch action
    log_audit(table_name, 0, 'batch_approve', 
              new_value=f"Approved {approved_count} records", 
              user_id=session.get('user_id'))
    
    return jsonify({
        'success': True,
        'approved': approved_count,
        'message': f'Successfully approved {approved_count} records'
    })

@app.route('/admin/batch_reject', methods=['POST'])
def batch_reject():
    """Batch reject multiple records"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    table_name = data.get('table_name')
    record_ids = data.get('record_ids', [])
    reason = data.get('reason', 'rejected')
    
    if not table_name or not record_ids:
        return jsonify({'error': 'Missing parameters'}), 400
    
    rejected_count = 0
    
    for record_id in record_ids:
        moderation = ContentModeration(
            table_name=table_name,
            record_id=record_id,
            status='rejected',
            moderator_id=session.get('user_id'),
            reason_code=reason
        )
        db.session.add(moderation)
        rejected_count += 1
    
    db.session.commit()
    
    # Log the batch action
    log_audit(table_name, 0, 'batch_reject', 
              new_value=f"Rejected {rejected_count} records", 
              user_id=session.get('user_id'))
    
    return jsonify({
        'success': True,
        'rejected': rejected_count,
        'message': f'Successfully rejected {rejected_count} records'
    })

@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    form = VehicleForm()
    form.officer_id.choices = [(o.id, f"{o.first_name} {o.last_name} ({o.badge_number})") for o in Officer.query.all()]
    
    if form.validate_on_submit():
        vehicle = Vehicle(
            officer_id=form.officer_id.data,
            vehicle_type=form.vehicle_type.data,
            make=form.make.data,
            model=form.model.data,
            year=form.year.data,
            color=form.color.data,
            license_plate=form.license_plate.data,
            state=form.state.data,
            vin=form.vin.data,
            is_unmarked=form.is_unmarked.data,
            description=form.description.data,
            last_seen_location=form.last_seen_location.data,
            last_seen_date=form.last_seen_date.data,
            source=form.source.data
        )
        db.session.add(vehicle)
        db.session.commit()
        
        # Log the audit trail
        log_audit('vehicles', vehicle.id, 'create', user_id=session.get('user_id'))
        
        flash('Vehicle added successfully!', 'success')
        return redirect(url_for('officer_detail', officer_id=vehicle.officer_id))
    
    return render_template('add_vehicle.html', form=form)

@app.route('/vehicles')
def vehicles():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Vehicle.query.filter_by(is_active=True)
    if search:
        query = query.join(Officer).filter(
            (Vehicle.make.contains(search)) |
            (Vehicle.model.contains(search)) |
            (Vehicle.license_plate.contains(search)) |
            (Vehicle.color.contains(search)) |
            (Officer.first_name.contains(search)) |
            (Officer.last_name.contains(search))
        )
    
    vehicles = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('vehicles.html', vehicles=vehicles, search=search)

@app.route('/analytics')
def analytics():
    """Analytics dashboard with statistics and trends"""
    # Basic statistics
    total_officers = Officer.query.count()
    total_incidents = Incident.query.count()
    total_evidence = Evidence.query.count()
    total_costs = db.session.query(db.func.sum(TaxpayerCost.amount)).scalar() or 0
    total_vehicles = Vehicle.query.filter_by(is_active=True).count()
    unmarked_vehicles = Vehicle.query.filter_by(is_active=True, is_unmarked=True).count()
    
    # Status breakdown
    active_officers = Officer.query.filter_by(status='active').count()
    terminated_officers = Officer.query.filter_by(status='terminated').count()
    suspended_officers = Officer.query.filter_by(status='suspended').count()
    retired_officers = Officer.query.filter_by(status='retired').count()
    
    # Incident types
    incident_types = db.session.query(
        Incident.incident_type,
        db.func.count(Incident.id)
    ).group_by(Incident.incident_type).order_by(db.func.count(Incident.id).desc()).limit(10).all()
    
    # Top officers by incident count
    top_officers = db.session.query(
        Officer,
        db.func.count(Incident.id).label('incident_count')
    ).join(Incident).group_by(Officer.id).order_by(db.func.count(Incident.id).desc()).limit(10).all()
    
    # Top officers by cost
    top_cost_officers = db.session.query(
        Officer,
        db.func.sum(TaxpayerCost.amount).label('total_cost')
    ).join(TaxpayerCost).group_by(Officer.id).order_by(db.func.sum(TaxpayerCost.amount).desc()).limit(10).all()
    
    # Departments with most incidents
    department_stats = db.session.query(
        Department,
        db.func.count(Incident.id).label('incident_count')
    ).join(Officer).join(Incident).group_by(Department.id).order_by(db.func.count(Incident.id).desc()).limit(10).all()
    
    # Monthly incident trends (last 12 months)
    from dateutil.relativedelta import relativedelta
    twelve_months_ago = datetime.now() - relativedelta(months=12)
    monthly_incidents = db.session.query(
        db.func.strftime('%Y-%m', Incident.incident_date).label('month'),
        db.func.count(Incident.id).label('count')
    ).filter(Incident.incident_date >= twelve_months_ago).group_by('month').order_by('month').all()
    
    # Pending moderation counts
    pending_incidents = Incident.query.filter_by(verified=False).count()
    pending_evidence = Evidence.query.filter_by(verified=False).count()
    pending_reports = CommunityReport.query.filter_by(verified=False).count()
    pending_disputes = Dispute.query.filter_by(status='pending').count()
    
    return render_template('analytics.html',
                         total_officers=total_officers,
                         total_incidents=total_incidents,
                         total_evidence=total_evidence,
                         total_costs=total_costs,
                         total_vehicles=total_vehicles,
                         unmarked_vehicles=unmarked_vehicles,
                         active_officers=active_officers,
                         terminated_officers=terminated_officers,
                         suspended_officers=suspended_officers,
                         retired_officers=retired_officers,
                         incident_types=incident_types,
                         top_officers=top_officers,
                         top_cost_officers=top_cost_officers,
                         department_stats=department_stats,
                         monthly_incidents=monthly_incidents,
                         pending_incidents=pending_incidents,
                         pending_evidence=pending_evidence,
                         pending_reports=pending_reports,
                         pending_disputes=pending_disputes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
