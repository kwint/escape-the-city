# Digital Scavenger Hunt App

A Django-based web application for managing digital scavenger hunts with QR codes.

## Features

- **QR Code Based System**: Each checkpoint has a unique QR code that groups can scan
- **Group Authentication**: Groups authenticate using passwords to log their progress
- **Timestamp Tracking**: All scans are logged with precise timestamps
- **Points System**: Automatic scoring based on scan order - first group to scan gets max points, subsequent groups get decreasing points
- **PDF Instructions**: After scanning, groups download PDF instructions for the next checkpoint
- **Admin Interface**: Comprehensive admin panel for managing groups, posts, and viewing scan history
- **QR Code Generation**: Built-in QR code generator accessible from the admin interface
- **Live Progress Overview**: Real-time dashboard showing which groups have completed which checkpoints with live scoring

## Installation & Setup

### 1. Create a superuser account
```bash
uv run python manage.py createsuperuser
```

### 2. Run the development server
```bash
uv run python manage.py runserver
```

### 3. Access the admin interface
Open your browser and go to: `http://localhost:8000/admin/`

## Usage Guide

### Setting Up Your Scavenger Hunt

1. **Log in to the admin interface** at `http://localhost:8000/admin/`

2. **Create Groups**:
   - Go to "Groups" section
   - Add groups with scout group name and team name
   - Passwords are automatically generated from a list of Dutch food words
   - After creating a group, click to edit it to view the assigned password
   - Groups are displayed as "scout_group name" throughout the app
   - Share the passwords with each team

3. **Create Posts (Checkpoints)**:
   - Go to "Posts" section
   - For each checkpoint:
     - Enter name and location description
     - Set the order number (for sequencing)
     - Upload a PDF file with instructions
   - Save the post

4. **Generate QR Codes**:
   - In the Posts list, click "View QR Code" for each post
   - Download or print the QR code
   - Place it at the physical location

### How Groups Use the System

1. Group arrives at a checkpoint
2. Scans the QR code with their phone
3. Enters their group password
4. System logs the scan with timestamp
5. PDF instructions automatically download
6. Group proceeds to next checkpoint

### Monitoring Progress

- **Live Overview Dashboard**:
  - Click "View Overview Dashboard" on the admin home page
  - Or visit `http://localhost:8000/` directly
  - **Top Statistics**:
    - Farthest Post Reached: Shows which post (by order) has been scanned, indicating overall progress
    - First Place: Shows the leading group and their points
    - Scans Remaining: Shows how many scans are left until completion
  - **Matrix Table**:
    - Groups as rows and posts as columns
    - First column (group names) stays visible when scrolling horizontally
    - Green checkmarks (✓) with points indicate completed scans
    - Points are awarded based on scan order: 1st place gets N points, 2nd gets N-1, etc. (where N = number of groups)
    - Hover over checkmarks to see scan timestamps and points earned
    - Total and Points columns on the right show each group's progress
    - Bottom row shows how many groups completed each post

- **In Admin Interface**:
  - Go to "Scans" to see all scan activity
  - Filter by group, post, or date
  - View timestamps for each scan

- **On Post Detail Page**:
  - Click on any post to see which groups have scanned it
  - View scan times inline

## Project Structure

```
escape-the-city/
├── hunt/                      # Main app
│   ├── models.py             # Group, Post, Scan models
│   ├── views.py              # Scan, download, and QR generation views
│   ├── admin.py              # Admin interface configuration
│   ├── utils.py              # QR code generation utilities
│   └── templates/            # HTML templates
├── media/                     # Uploaded PDF files
├── scavenger_hunt/           # Django project settings
└── manage.py                 # Django management script
```

## Models

### Group
- `scout_group`: Scout group name/identifier
- `name`: Group/team name (unique together with scout_group)
- `password`: Authentication password (auto-generated from Dutch food words, guaranteed unique)
- `created_at`: Creation timestamp
- Groups are displayed as "scout_group name"
- Passwords are automatically assigned when creating new groups
- System ensures no two groups have the same password

### Post
- `name`: Checkpoint name
- `description`: Description/location shown on scan page
- `qr_code_identifier`: UUID for the QR code URL
- `pdf_file`: Instructions PDF
- `order`: Sequence number
- `created_at`: Creation timestamp

### Scan
- `group`: Which group scanned
- `post`: Which post was scanned
- `scanned_at`: When it was scanned
- Unique constraint: Each group can only scan each post once

## URLs

- `/` - Live progress overview dashboard (admin only)
- `/admin/` - Admin interface
- `/scan/<uuid>/` - Scan endpoint (from QR code)
- `/download/<uuid>/<group_id>/` - PDF download after authentication
- `/generate-qr/<post_id>/` - QR code generation (admin only)

## Security Notes

- Group passwords are stored in plain text for simplicity
- Passwords are auto-generated from a list of 50 Dutch food words (see `hunt/passwords.py`)
- Each password is unique - already-used passwords are excluded when generating new ones
- If more than 50 groups are created, passwords will have numeric suffixes (e.g., "appel123")
- Admin access required for QR code generation and overview dashboard
- File uploads are restricted to the `media/instructions/` directory
- Each group can only scan each post once (enforced at database level)

## Technologies Used

- **Django 5.2**: Web framework
- **Python 3.13**: Programming language
- **UV**: Package manager
- **qrcode**: QR code generation
- **Pillow**: Image processing
- **SQLite**: Database (default)

## Development

To add more features or customize:

1. Modify models in `hunt/models.py`
2. Update views in `hunt/views.py`
3. Customize admin in `hunt/admin.py`
4. Run migrations: `uv run python manage.py makemigrations && uv run python manage.py migrate`

## Tips

- Use the "order" field to control the sequence of checkpoints
- QR codes can be regenerated at any time
- Scan history cannot be manually created (prevents cheating)
- Export scan data from the admin interface for analysis
