#!/usr/bin/env python3
"""
Bad Apples Database Setup Script
Creates initial database and admin user
"""

import os
import sys
from flask import Flask
from werkzeug.security import generate_password_hash

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def create_admin_user():
    """Create initial admin user"""
    with app.app_context():
        # Check if admin user already exists
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@badapples.local',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')  # Change this password!
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️  IMPORTANT: Change the default password immediately!")

def create_sample_data():
    """Create sample data for testing"""
    with app.app_context():
        from models import Department, Officer
        
        # Create sample department
        dept = Department.query.filter_by(name='Sample Police Department').first()
        if not dept:
            dept = Department(
                name='Sample Police Department',
                jurisdiction='City',
                location='Sample City, ST',
                state='ST',
                website='https://example.com',
                phone='(555) 123-4567'
            )
            db.session.add(dept)
            db.session.commit()
            print("✅ Sample department created")
        
        # Create sample officer
        officer = Officer.query.filter_by(badge_number='12345').first()
        if not officer:
            officer = Officer(
                badge_number='12345',
                first_name='John',
                last_name='Doe',
                current_department_id=dept.id,
                status='active'
            )
            db.session.add(officer)
            db.session.commit()
            print("✅ Sample officer created")

def main():
    """Main setup function"""
    print("🚨 Bad Apples Database Setup")
    print("=" * 40)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")
    
    # Create admin user
    create_admin_user()
    
    # Create sample data
    create_sample_data()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Open: http://localhost:5000")
    print("3. Login to admin panel with admin/admin123")
    print("4. Change the default admin password!")
    print("\n⚠️  Security Notice:")
    print("- Change default passwords immediately")
    print("- Use HTTPS in production")
    print("- Regularly backup the database")
    print("- Monitor audit logs for suspicious activity")

if __name__ == '__main__':
    main()
