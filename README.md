# Bad Apples Database

A community-driven database for tracking law enforcement officers with histories of misconduct, violence, and abuse of power. This system helps communities document and share information about problematic officers who have been transferred rather than held accountable.

## Features

### Core Functionality
- **Officer Database**: Track officers with detailed profiles including badge numbers, departments, and status
- **Incident Documentation**: Record incidents with dates, descriptions, outcomes, and legal details
- **Evidence Management**: Upload and manage photos, videos, documents, and audio files
- **Community Reports**: Allow community members to submit reports and share experiences
- **Social Media Tracking**: Monitor officers' social media profiles for concerning content
- **Department History**: Track officer transfers between departments
- **Search & Filter**: Powerful search capabilities across all data
- **Export Functionality**: Download officer data for community advocacy

### Modern Web Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Clean Navigation**: Intuitive interface with easy-to-use forms
- **Real-time Search**: Instant search results as you type
- **File Upload**: Drag-and-drop file uploads with preview
- **Data Validation**: Comprehensive form validation and error handling
- **Print Support**: Print-friendly layouts for documentation

### Community Safety Features
- **Evidence Download**: Community members can download evidence for town hall meetings
- **Export Reports**: Generate comprehensive reports for advocacy
- **Privacy Protection**: Secure handling of community input
- **Verification System**: Mark evidence and reports as verified
- **Source Tracking**: Document sources of information for credibility

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or Download the Project**
   ```bash
   cd /path/to/BadApples
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the Database**
   ```bash
   python app.py
   ```
   This will create the SQLite database and all necessary tables.

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the Application**
   Open your web browser and go to: `http://localhost:5000`

## Usage

### Adding Data

1. **Add Departments**: Start by adding police departments and agencies
2. **Add Officers**: Create officer profiles with badge numbers and personal information
3. **Record Incidents**: Document specific incidents with dates, descriptions, and outcomes
4. **Upload Evidence**: Add photos, videos, documents, and other supporting materials
5. **Community Reports**: Allow community members to submit their own reports

### Searching and Filtering

- Use the search bar to find officers by name, badge number, or department
- Filter by incident type, date range, or outcome
- Browse by department or officer status
- Export data for community advocacy

### Community Features

- **Report Incidents**: Community members can submit detailed reports
- **Upload Evidence**: Share photos, videos, and documents
- **Download Materials**: Get evidence for town hall meetings and advocacy
- **Track Patterns**: Identify officers with multiple incidents across departments

## Database Schema

### Core Tables
- **Officers**: Officer profiles with personal and professional information
- **Departments**: Police departments and agencies
- **Incidents**: Documented incidents with full details
- **Evidence**: Files and media associated with officers/incidents
- **Community Reports**: Reports submitted by community members
- **Social Media Profiles**: Tracked social media accounts
- **Department History**: Officer transfer history between departments

### Key Relationships
- Officers belong to Departments
- Incidents are associated with Officers
- Evidence is linked to Officers and optionally to Incidents
- Community Reports can be linked to specific Incidents
- Officers can have multiple Department assignments over time

## Security Considerations

### Data Protection
- All file uploads are validated for type and size
- Personal information is protected and not publicly displayed
- Community reporters can choose to remain anonymous
- Evidence is stored securely with access controls

### Verification
- Evidence can be marked as verified by administrators
- Community reports are reviewed before publication
- Source information is tracked for credibility
- Multiple sources can be linked to the same incident

## Community Advocacy

### Using the Database for Change
1. **Document Patterns**: Track officers who move between departments
2. **Gather Evidence**: Collect photos, videos, and documents
3. **Export Reports**: Generate comprehensive reports for officials
4. **Town Hall Preparation**: Download materials for community meetings
5. **Media Outreach**: Provide verified information to journalists

### Legal Considerations
- All information should be publicly available or legally obtained
- Respect privacy laws and regulations
- Focus on documented incidents and public records
- Maintain accuracy and verification standards

## Technical Details

### Technology Stack
- **Backend**: Flask (Python web framework)
- **Database**: SQLite (portable, file-based database)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **File Handling**: Werkzeug for secure file uploads
- **Forms**: WTForms for form validation

### File Structure
```
BadApples/
├── app.py                 # Main Flask application
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── templates/           # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── officers.html
│   ├── officer_detail.html
│   ├── add_officer.html
│   ├── add_incident.html
│   ├── add_evidence.html
│   ├── community_report.html
│   ├── add_department.html
│   └── search_results.html
├── static/              # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── uploads/             # File upload directory
```

## Contributing

### Adding Features
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Reporting Issues
- Use the issue tracker for bugs and feature requests
- Provide detailed descriptions and steps to reproduce
- Include screenshots for UI issues

## Legal Disclaimer

This database is intended for community safety and accountability purposes only. All information should be:
- Publicly available or legally obtained
- Factual and verifiable
- Used responsibly and ethically
- Compliant with local laws and regulations

The creators of this system are not responsible for how the information is used or any legal consequences that may arise from its use.

## Support

For technical support or questions about the system:
- Check the documentation first
- Search existing issues
- Create a new issue with detailed information
- Contact the development team

## License

This project is open source and available under the MIT License. See the LICENSE file for details.

---

**Remember**: This tool is designed to promote community safety and police accountability. Use it responsibly and in accordance with all applicable laws and regulations.
