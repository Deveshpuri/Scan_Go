from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import json
from datetime import datetime, timedelta
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from config import Config

# --- New Imports for OCR and Google Sheets ---
import os
import io
import base64
import cv2
import numpy as np
from PIL import Image
import pytesseract
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Store OTPs temporarily (in production, use Redis or a similar cache)
otp_storage = {}


# --- Database Models ---
class SuperAdmin(db.Model):
    __tablename__ = 'superadmins'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(191), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Enum('active', 'inactive'), default='active')
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(191), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'))
    status = db.Column(db.Enum('pending', 'approved'), default='pending')
    google_credentials = db.Column(db.Text) # For Google Sheets API
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Guard(db.Model):
    __tablename__ = 'guards'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(191), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'))
    status = db.Column(db.Enum('active', 'inactive'), default='active')
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Resident(db.Model):
    __tablename__ = 'residents'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(191), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False)
    building_number = db.Column(db.String(50), nullable=False)
    flat_number = db.Column(db.String(50), nullable=False)
    wing = db.Column(db.String(50))
    status = db.Column(db.Enum('pending', 'approved'), default='approved')
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Building(db.Model):
    __tablename__ = 'buildings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    cctv_settings = db.Column(db.Text)
    google_sheet_id = db.Column(db.String(255))  # New column
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))  # New column
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    admin = db.relationship('Admin', backref='buildings', foreign_keys=[admin_id])


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    license_plate = db.Column(db.String(50), unique=True, nullable=False)
    chassis_number = db.Column(db.String(100))
    model = db.Column(db.String(100))
    vehicle_type = db.Column(db.Enum('2_wheeler', '3_wheeler', '4_wheeler'))
    parking_slot = db.Column(db.String(50))
    color = db.Column(db.String(50))
    registration_image = db.Column(db.String(500))
    vehicle_image = db.Column(db.String(500))
    owner_type = db.Column(db.Enum('resident', 'rental'), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending')
    approved_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    approved_at = db.Column(db.DateTime)
    rejected_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    unregistered_visit_id = db.Column(db.Integer, db.ForeignKey('unregistered_visits.id'))
    license_plate = db.Column(db.String(50))
    action = db.Column(db.Enum('scan', 'verification', 'entry', 'exit', 'manual_entry'), nullable=False)
    result = db.Column(db.Enum('registered', 'not_found', 'pending', 'unregistered', 'approved'), nullable=False)
    source = db.Column(db.Enum('google_sheet', 'mysql', 'not_found'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    guard_id = db.Column(db.Integer, db.ForeignKey('guards.id'))
    notes = db.Column(db.Text)
    snapshot_url = db.Column(db.String(500))
    captured_image = db.Column(db.String(500))

class UnregisteredVisit(db.Model):
    __tablename__ = 'unregistered_visits'
    id = db.Column(db.Integer, primary_key=True)
    license_plate = db.Column(db.String(50), nullable=False)
    visitor_name = db.Column(db.String(255))
    visitor_email = db.Column(db.String(255))
    visited_resident_id = db.Column(db.Integer, db.ForeignKey('residents.id'))
    entry_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    exit_timestamp = db.Column(db.DateTime)
    guard_id = db.Column(db.Integer, db.ForeignKey('guards.id'))
    notes = db.Column(db.Text)
    vehicle_image = db.Column(db.String(500))
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.Enum('resident', 'rental', 'admin', 'guard', 'superadmin'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Enum('approval', 'rejection', 'suspicious_activity'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


# --- Utility Functions ---
def check_password(password_hash, password):
    """Check password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password check error: {str(e)}")
        return False

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    """Send OTP via email"""
    try:
        message = MIMEMultipart()
        message['From'] = app.config['SMTP_USER']
        message['To'] = email
        message['Subject'] = 'Your OTP Code'
        
        body = f"Your OTP code for vehicle access system is: {otp}\n\nThis OTP will expire in 10 minutes."
        message.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(app.config['SMTP_HOST'], app.config['SMTP_PORT']) as server:
            server.starttls()
            server.login(app.config['SMTP_USER'], app.config['SMTP_PASSWORD'])
            server.send_message(message)
        
        return True
    except Exception as e:
        logger.error(f"Email sending error: {str(e)}")
        return False

def create_notification(user_type, user_id, notification_type, message):
    """Create a new notification"""
    try:
        notification = Notification(
            user_type=user_type,
            user_id=user_id,
            type=notification_type,
            message=message
        )
        db.session.add(notification)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Notification creation error: {str(e)}")
        db.session.rollback()
        return False

# --- OCR & Google Sheets Functionality ---

# OCR Configuration
def preprocess_image(image_data):
    """Preprocess image for better OCR results"""
    try:
        # Convert base64 to image if needed
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # Extract base64 data from data URL
            image_data = image_data.split(',')[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply noise reduction
        denoised = cv2.medianBlur(gray, 5)
        
        # Apply thresholding
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    except Exception as e:
        logger.error(f"Image preprocessing error: {str(e)}")
        return None

def extract_license_plate(image_data):
    """Extract license plate number from image using OCR"""
    try:
        processed_image = preprocess_image(image_data)
        if processed_image is None:
            return None, "Image processing failed"
        
        # Configure Tesseract for license plates
        custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        # Extract text
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # Clean and validate license plate
        license_plate = clean_license_plate(text)
        
        if license_plate:
            return license_plate, "License plate extracted successfully"
        else:
            return None, "No valid license plate found in image"
            
    except Exception as e:
        logger.error(f"OCR extraction error: {str(e)}")
        return None, f"OCR processing error: {str(e)}"

def clean_license_plate(text):
    """Clean and validate license plate format"""
    if not text:
        return None
    
    # Remove unwanted characters and whitespace
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper().strip())
    
    # Basic validation for Indian license plates
    # Format: XX00XX0000 or similar variations
    if len(cleaned) >= 6 and len(cleaned) <= 10:
        # Check if it has both letters and numbers
        has_letters = any(c.isalpha() for c in cleaned)
        has_numbers = any(c.isdigit() for c in cleaned)
        
        if has_letters and has_numbers:
            return cleaned
    
    return None

# Google Sheets Integration
def get_google_sheets_service(admin_id):
    """Get Google Sheets service for admin"""
    try:
        # In production, store credentials in database
        admin = Admin.query.get(admin_id)
        if not admin or not admin.google_credentials:
            return None
        
        creds = Credentials.from_authorized_user_info(
            json.loads(admin.google_credentials)
        )
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Google Sheets service error: {str(e)}")
        return None

def check_google_sheet(license_plate, building_id):
    """Check license plate in Google Sheet with better error handling"""
    try:
        logger.info(f"Checking Google Sheet for license plate: {license_plate} in building: {building_id}")
        
        building = Building.query.get(building_id)
        if not building:
            logger.warning(f"Building {building_id} not found")
            return None
        
        if not building.google_sheet_id:
            logger.warning(f"No Google Sheet ID configured for building {building_id}")
            return None
        
        logger.info(f"Google Sheet ID: {building.google_sheet_id}")
        
        # Get admin for this building
        admin = Admin.query.get(building.admin_id)
        if not admin:
            logger.warning(f"No admin found for building {building_id}")
            return None
        
        logger.info(f"Found admin: {admin.user_name} (ID: {admin.id})")
        
        # Check if admin has Google credentials
        if not admin.google_credentials:
            logger.warning(f"Admin {admin.id} has no Google credentials configured")
            # Try to use service account or public sheet access as fallback
            return check_google_sheet_public(license_plate, building.google_sheet_id)
        
        service = get_google_sheets_service(admin.id)
        if not service:
            logger.warning(f"Google Sheets service creation failed for admin {admin.id}")
            # Fallback to public access
            return check_google_sheet_public(license_plate, building.google_sheet_id)
        
        # Read data from Google Sheet
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=building.google_sheet_id,
            range='A:E'  # Specific range for your columns
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            logger.info(f"No data found in Google Sheet")
            return {'found': False, 'source': 'google_sheet'}
        
        # Skip header row if exists
        start_index = 0
        if values and any('License Plate' in str(cell) for cell in values[0]):
            start_index = 1  # Skip header row
            logger.info("Skipping header row")
        
        # Search for license plate in first column
        target_plate = license_plate.upper().strip()
        logger.info(f"Searching for: {target_plate}")
        
        for row_index, row in enumerate(values[start_index:], start_index + 1):
            if row and len(row) > 0:
                sheet_plate = str(row[0]).upper().strip()
                logger.info(f"Checking row {row_index}: {sheet_plate}")
                
                if sheet_plate == target_plate:
                    logger.info(f"✅ FOUND in Google Sheet at row {row_index}: {row}")
                    return {
                        'found': True,
                        'source': 'google_sheet',
                        'data': row,
                        'row_index': row_index
                    }
        
        logger.info(f"❌ NOT FOUND in Google Sheet")
        return {'found': False, 'source': 'google_sheet'}
        
    except Exception as e:
        logger.error(f"Google Sheet check error: {str(e)}")
        # Fallback to public access on error
        try:
            if building and building.google_sheet_id:
                return check_google_sheet_public(license_plate, building.google_sheet_id)
        except:
            pass
        return None

def check_google_sheet_public(license_plate, google_sheet_id):
    """Fallback method to check Google Sheet without authentication"""
    try:
        logger.info(f"Trying public access for sheet: {google_sheet_id}")
        
        # For public sheets, you can use this URL format
        import requests
        
        # Convert to CSV export URL
        csv_url = f"https://docs.google.com/spreadsheets/d/{google_sheet_id}/export?format=csv"
        
        response = requests.get(csv_url, timeout=10)
        if response.status_code == 200:
            import csv
            import io
            
            # Parse CSV content
            csv_content = response.content.decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_content))
            
            target_plate = license_plate.upper().strip()
            
            for row_index, row in enumerate(csv_reader):
                if row and len(row) > 0:
                    sheet_plate = str(row[0]).upper().strip()
                    if sheet_plate == target_plate:
                        logger.info(f"✅ FOUND in public Google Sheet: {row}")
                        return {
                            'found': True,
                            'source': 'google_sheet_public',
                            'data': row,
                            'row_index': row_index + 1
                        }
            
            logger.info(f"❌ NOT FOUND in public Google Sheet")
            return {'found': False, 'source': 'google_sheet_public'}
        else:
            logger.warning(f"Public access failed with status: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Public Google Sheet check error: {str(e)}")
        return None

def verify_license_plate(license_plate, building_id):
    """Two-layer verification: Google Sheet -> MySQL"""
    try:
        # First check Google Sheet
        google_result = check_google_sheet(license_plate, building_id)
        
        if google_result and google_result.get('found'):
            return {
                'status': 'registered',  # Changed from 'approved' to match your Log enum
                'source': 'google_sheet',
                'data': google_result.get('data')
            }
        
        # If not found in Google Sheet, check MySQL
        vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
        if vehicle:
            return {
                'status': vehicle.status,  # 'approved', 'pending', or 'rejected'
                'source': 'mysql',
                'vehicle_id': vehicle.id,
                'data': {
                    'owner_name': vehicle.owner_name,
                    'model': vehicle.model,
                    'vehicle_type': vehicle.vehicle_type
                }
            }
        
        return {'status': 'not_found', 'source': 'mysql'}
    
    except Exception as e:
        logger.error(f"License plate verification error: {str(e)}")
        return {'status': 'not_found', 'source': 'error'}

# --- Health & Debugging Endpoints ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        db.session.execute('SELECT 1')
        return jsonify({'message': 'Database connection successful'}), 200
    except Exception as e:
        logger.error(f"Database test error: {str(e)}")
        return jsonify({'error': f'Database connection failed: {str(e)}'}), 500


# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500


# --- AUTH APIs ---
@app.route('/auth/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        admin = Admin.query.filter_by(email=email, status='approved').first()
        if admin and check_password(admin.password_hash, password):
            additional_claims = {'role': 'admin', 'building_id': admin.building_id, 'user_name': admin.user_name}
            access_token = create_access_token(
                identity=str(admin.id),
                additional_claims=additional_claims
            )
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': {
                    'id': admin.id,
                    'user_name': admin.user_name,
                    'email': admin.email,
                    'role': 'admin',
                    'building_id': admin.building_id
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials or account not approved'}), 401
            
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/auth/guard/login', methods=['POST'])
def guard_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        guard = Guard.query.filter_by(email=email, status='active').first()
        if guard and check_password(guard.password_hash, password):
            additional_claims = {'role': 'guard', 'building_id': guard.building_id, 'user_name': guard.user_name}
            access_token = create_access_token(
                identity=str(guard.id),
                additional_claims=additional_claims
            )
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': {
                    'id': guard.id,
                    'user_name': guard.user_name,
                    'email': guard.email,
                    'building_id': guard.building_id,
                    'role': 'guard'
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials or account inactive'}), 401
            
    except Exception as e:
        logger.error(f"Guard login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/auth/user/login', methods=['POST'])
def user_login():
    """User login with email/phone and password"""
    try:
        data = request.get_json()
        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data.get('password')
        
        if not password or (not email and not phone_number):
            return jsonify({'error': 'Email or phone number and password required'}), 400
        
        # Find user by email or phone number
        user = None
        if email:
            user = Resident.query.filter_by(email=email, status='approved').first()
        elif phone_number:
            user = Resident.query.filter_by(phone_number=phone_number, status='approved').first()
        
        if not user:
            return jsonify({'error': 'User not found or not approved'}), 404
        
        # Check password
        if check_password(user.password_hash, password):
            additional_claims = {
                'role': 'resident', 
                'building_id': user.building_id, 
                'user_name': user.user_name
            }
            access_token = create_access_token(
                identity=str(user.id), # Corrected line
                additional_claims=additional_claims
            )
            
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'user_name': user.user_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'building_id': user.building_id,
                    'building_number': user.building_number,
                    'flat_number': user.flat_number,
                    'wing': user.wing,
                    'role': 'resident'
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid password'}), 401
        
    except Exception as e:
        logger.error(f"User login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/auth/user/register', methods=['POST'])
def register_user():
    """User self-registration (no authentication required)"""
    try:
        data = request.get_json()
        logger.info(f"Registration attempt with data: {data}")
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Required fields
        user_name = data.get('user_name')
        email = data.get('email')
        password = data.get('password')
        phone_number = data.get('phone_number')
        building_id = data.get('building_id')
        building_number = data.get('building_number')
        flat_number = data.get('flat_number')
        wing = data.get('wing')
        
        # Validation
        required_fields = ['user_name', 'email', 'password', 'phone_number', 'building_id', 'building_number', 'flat_number']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Missing fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user already exists
        existing_email = Resident.query.filter_by(email=email).first()
        if existing_email:
            logger.warning(f"Email already exists: {email}")
            return jsonify({'error': 'User with this email already exists'}), 409
        
        existing_username = Resident.query.filter_by(user_name=user_name).first()
        if existing_username:
            logger.warning(f"Username already exists: {user_name}")
            return jsonify({'error': 'User with this username already exists'}), 409
        
        existing_phone = Resident.query.filter_by(phone_number=phone_number).first()
        if existing_phone:
            logger.warning(f"Phone number already exists: {phone_number}")
            return jsonify({'error': 'User with this phone number already exists'}), 409
        
        # Check if building exists
        building = Building.query.get(building_id)
        if not building:
            logger.warning(f"Building not found: {building_id}")
            return jsonify({'error': 'Building not found'}), 404
        
        # Hash password
        try:
            password_hash = hash_password(password)
            logger.info("Password hashed successfully")
        except Exception as hash_error:
            logger.error(f"Password hashing error: {hash_error}")
            return jsonify({'error': 'Password processing failed'}), 500
        
        # Create resident user
        new_resident = Resident(
            user_name=user_name,
            email=email,
            password_hash=password_hash,
            phone_number=phone_number,
            building_id=building_id,
            building_number=building_number,
            flat_number=flat_number,
            wing=wing,
            status='pending',  # Requires admin approval
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_resident)
        logger.info("New resident added to session")
        
        # Notify admins about new user registration
        admins = Admin.query.filter_by(building_id=building_id).all()
        logger.info(f"Found {len(admins)} admins for building {building_id}")
        
        for admin in admins:
            create_notification(
                user_type='admin',
                user_id=admin.id,
                notification_type='approval',
                message=f'New resident {user_name} from {building_number}/{flat_number} is awaiting approval.'
            )
        
        # Commit to database
        db.session.commit()
        logger.info(f"User registered successfully: {user_name} (ID: {new_resident.id})")
        
        return jsonify({
            'message': 'User registered successfully. Waiting for admin approval.',
            'user': {
                'id': new_resident.id,
                'user_name': new_resident.user_name,
                'email': new_resident.email,
                'phone_number': new_resident.phone_number,
                'building_id': new_resident.building_id,
                'building_number': new_resident.building_number,
                'flat_number': new_resident.flat_number,
                'wing': new_resident.wing,
                'status': new_resident.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"User registration error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500
    
@app.route('/buildings', methods=['GET'])
def get_buildings():
    buildings = Building.query.all()
    return jsonify({'buildings': [{'id': b.id, 'name': b.name} for b in buildings]})
    
@app.route('/admin/residents/create', methods=['POST'])
@jwt_required()
def create_resident_by_admin():
    """Create resident user by Admin (auto-approved)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Required fields
        user_name = data.get('user_name')
        email = data.get('email')
        password = data.get('password')
        phone_number = data.get('phone_number')
        building_id = data.get('building_id')
        building_number = data.get('building_number')
        flat_number = data.get('flat_number')
        wing = data.get('wing')
        
        # Validation
        required_fields = ['user_name', 'email', 'password', 'phone_number', 'building_id', 'building_number', 'flat_number']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Check if user already exists
        if Resident.query.filter_by(email=email).first():
            return jsonify({'error': 'User with this email already exists'}), 409
        
        if Resident.query.filter_by(user_name=user_name).first():
            return jsonify({'error': 'User with this username already exists'}), 409
        
        if Resident.query.filter_by(phone_number=phone_number).first():
            return jsonify({'error': 'User with this phone number already exists'}), 409
        
        # Check if building exists and belongs to admin
        building = Building.query.get(building_id)
        if not building:
            return jsonify({'error': 'Building not found'}), 404
        
        if building.admin_id != int(get_jwt_identity()): # Cast to integer
            return jsonify({'error': 'Access denied to this building'}), 403
        
        # Create resident user (auto-approved when created by admin)
        new_resident = Resident(
            user_name=user_name,
            email=email,
            password_hash=hash_password(password),
            phone_number=phone_number,
            building_id=building_id,
            building_number=building_number,
            flat_number=flat_number,
            wing=wing,
            status='approved',  # Auto-approved when created by admin
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_resident)
        db.session.commit()
        
        return jsonify({
            'message': 'Resident created successfully',
            'resident': {
                'id': new_resident.id,
                'user_name': new_resident.user_name,
                'email': new_resident.email,
                'phone_number': new_resident.phone_number,
                'building_id': new_resident.building_id,
                'building_number': new_resident.building_number,
                'flat_number': new_resident.flat_number,
                'wing': new_resident.wing,
                'status': new_resident.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create resident error: {str(e)}")
        return jsonify({'error': 'Failed to create resident'}), 500
    
    
    
    
@app.route('/admin/residents/<int:resident_id>/approve', methods=['POST'])
@jwt_required()
def approve_resident(resident_id):
    """Approve a pending resident"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        resident = Resident.query.get(resident_id)
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        # Check if resident belongs to admin's building
        if resident.building_id != claims.get('building_id'):
            return jsonify({'error': 'Access denied to this resident'}), 403
        
        resident.status = 'approved'
        db.session.commit()
        
        # Create notification for resident
        create_notification(
            user_type='resident',
            user_id=resident.id,
            notification_type='approval',
            message='Your account has been approved. You can now login and register vehicles.'
        )
        
        return jsonify({
            'message': 'Resident approved successfully',
            'resident': {
                'id': resident.id,
                'user_name': resident.user_name,
                'status': resident.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Approve resident error: {str(e)}")
        return jsonify({'error': 'Failed to approve resident'}), 500




@app.route('/admin/residents', methods=['GET'])
@jwt_required()
def list_residents():
    """List all residents for admin's building"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        admin_building_id = claims.get('building_id')
        status_filter = request.args.get('status')  # pending, approved
        
        query = Resident.query.filter_by(building_id=admin_building_id)
        
        if status_filter in ['pending', 'approved']:
            query = query.filter(Resident.status == status_filter)
        
        residents = query.order_by(Resident.created_at.desc()).all()
        
        residents_data = [{
            'id': resident.id,
            'user_name': resident.user_name,
            'email': resident.email,
            'phone_number': resident.phone_number,
            'building_number': resident.building_number,
            'flat_number': resident.flat_number,
            'wing': resident.wing,
            'status': resident.status,
            'created_at': resident.created_at.isoformat()
        } for resident in residents]
        
        return jsonify({'residents': residents_data}), 200
        
    except Exception as e:
        logger.error(f"List residents error: {str(e)}")
        return jsonify({'error': 'Failed to get residents list'}), 500
    
    
    
    
    
    
@app.route('/admin/residents/<int:resident_id>/reject', methods=['POST'])
@jwt_required()
def reject_resident(resident_id):
    """Reject a pending resident"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        resident = Resident.query.get(resident_id)
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        # Check if resident belongs to admin's building
        if resident.building_id != claims.get('building_id'):
            return jsonify({'error': 'Access denied to this resident'}), 403
        
        # Delete the rejected resident
        db.session.delete(resident)
        db.session.commit()
        
        return jsonify({
            'message': f'Resident rejected: {reason}',
            'resident_id': resident_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Reject resident error: {str(e)}")
        return jsonify({'error': 'Failed to reject resident'}), 500    
    
    
@app.route('/admin/guards/create', methods=['POST'])
@jwt_required()
def create_guard():
    """Create a new guard user (Admin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Required fields
        user_name = data.get('user_name')
        email = data.get('email')
        password = data.get('password')
        phone_number = data.get('phone_number')
        building_id = data.get('building_id')
        
        # Validation
        if not all([user_name, email, password, phone_number, building_id]):
            return jsonify({'error': 'All fields are required: user_name, email, password, phone_number, building_id'}), 400
        
        # Check if user already exists
        if Guard.query.filter_by(email=email).first():
            return jsonify({'error': 'Guard with this email already exists'}), 409
        
        if Guard.query.filter_by(user_name=user_name).first():
            return jsonify({'error': 'Guard with this username already exists'}), 409
        
        # Check if building exists
        building = Building.query.get(building_id)
        if not building:
            return jsonify({'error': 'Building not found'}), 404
        
        # Create guard
        new_guard = Guard(
            user_name=user_name,
            email=email,
            password_hash=hash_password(password),
            phone_number=phone_number,
            building_id=building_id,
            status='active',
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_guard)
        db.session.commit()
        
        return jsonify({
            'message': 'Guard created successfully',
            'guard': {
                'id': new_guard.id,
                'user_name': new_guard.user_name,
                'email': new_guard.email,
                'phone_number': new_guard.phone_number,
                'building_id': new_guard.building_id,
                'status': new_guard.status,
                'created_at': new_guard.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create guard error: {str(e)}")
        return jsonify({'error': 'Failed to create guard'}), 500
    
@app.route('/auth/admin/register', methods=['POST'])
def register_admin():
    """Admin self-registration with automatic building creation"""
    try:
        data = request.get_json()
        
        # Required fields
        user_name = data.get('user_name')
        email = data.get('email')
        password = data.get('password')
        phone_number = data.get('phone_number')
        building_name = data.get('building_name')
        building_address = data.get('building_address')
        
        # Validation
        required_fields = ['user_name', 'email', 'password', 'phone_number', 'building_name']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Check if user already exists
        if Admin.query.filter_by(email=email).first():
            return jsonify({'error': 'Admin with this email already exists'}), 409
        
        if Admin.query.filter_by(user_name=user_name).first():
            return jsonify({'error': 'Admin with this username already exists'}), 409
        
        # Get the next available building ID (auto-increment)
        last_building = Building.query.order_by(Building.id.desc()).first()
        new_building_id = (last_building.id + 1) if last_building else 1
        
        # Create new building for this admin
        new_building = Building(
            id=new_building_id,
            name=building_name,
            address=building_address,
            google_sheet_id=data.get('google_sheet_id'),  # Optional
            admin_id=None,  # Will be set after admin creation
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_building)
        db.session.flush()  # Get the building ID without committing
        
        # Create admin with pending status and link to new building
        new_admin = Admin(
            user_name=user_name,
            email=email,
            password_hash=hash_password(password),
            phone_number=phone_number,
            building_id=new_building.id,  # Link to the new building
            status='pending',  # Set as pending for approval
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_admin)
        db.session.flush()  # Get the admin ID without committing
        
        # Update building with admin_id
        new_building.admin_id = new_admin.id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Admin registered successfully. Waiting for SuperAdmin approval.',
            'admin': {
                'id': new_admin.id,
                'user_name': new_admin.user_name,
                'email': new_admin.email,
                'phone_number': new_admin.phone_number,
                'building_id': new_admin.building_id,
                'status': new_admin.status,
                'created_at': new_admin.created_at.isoformat()
            },
            'building': {
                'id': new_building.id,
                'name': new_building.name,
                'address': new_building.address,
                'google_sheet_id': new_building.google_sheet_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin registration error: {str(e)}")
        return jsonify({'error': 'Failed to register admin'}), 500
    
    
    
@app.route('/superadmin/admins/<int:admin_id>/approve', methods=['POST'])
@jwt_required()
def approve_admin(admin_id):
    """Approve a pending admin (SuperAdmin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'superadmin':
            return jsonify({'error': 'Access denied. SuperAdmin access required'}), 403
        
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        admin.status = 'approved'
        db.session.commit()
        
        return jsonify({
            'message': 'Admin approved successfully',
            'admin': {
                'id': admin.id,
                'user_name': admin.user_name,
                'status': admin.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Approve admin error: {str(e)}")
        return jsonify({'error': 'Failed to approve admin'}), 500

@app.route('/superadmin/admins/<int:admin_id>/reject', methods=['POST'])
@jwt_required()
def reject_admin(admin_id):
    """Reject a pending admin (SuperAdmin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'superadmin':
            return jsonify({'error': 'Access denied. SuperAdmin access required'}), 403
        
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        # Delete the rejected admin
        db.session.delete(admin)
        db.session.commit()
        
        return jsonify({
            'message': f'Admin rejected: {reason}',
            'admin_id': admin_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Reject admin error: {str(e)}")
        return jsonify({'error': 'Failed to reject admin'}), 500
    
    
@app.route('/superadmin/admins/pending', methods=['GET'])
@jwt_required()
def list_pending_admins():
    """List all pending admins (SuperAdmin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'superadmin':
            return jsonify({'error': 'Access denied. SuperAdmin access required'}), 403
        
        pending_admins = Admin.query.filter_by(status='pending').order_by(Admin.created_at.desc()).all()
        
        admins_data = [{
            'id': admin.id,
            'user_name': admin.user_name,
            'email': admin.email,
            'phone_number': admin.phone_number,
            'building_id': admin.building_id,
            'created_at': admin.created_at.isoformat()
        } for admin in pending_admins]
        
        return jsonify({'pending_admins': admins_data}), 200
        
    except Exception as e:
        logger.error(f"List pending admins error: {str(e)}")
        return jsonify({'error': 'Failed to get pending admins list'}), 500    
   
@app.route('/superadmin/admins/create', methods=['POST'])
@jwt_required()
def create_admin():
    """Create a new admin user with building (SuperAdmin only)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'superadmin':
            return jsonify({'error': 'Access denied. SuperAdmin access required'}), 403
        
        data = request.get_json()
        
        # Required fields
        user_name = data.get('user_name')
        email = data.get('email')
        password = data.get('password')
        phone_number = data.get('phone_number')
        building_name = data.get('building_name')
        building_address = data.get('building_address')
        
        # Validation
        required_fields = ['user_name', 'email', 'password', 'phone_number', 'building_name']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Check if user already exists
        if Admin.query.filter_by(email=email).first():
            return jsonify({'error': 'Admin with this email already exists'}), 409
        
        if Admin.query.filter_by(user_name=user_name).first():
            return jsonify({'error': 'Admin with this username already exists'}), 409
        
        # Get the next available building ID
        last_building = Building.query.order_by(Building.id.desc()).first()
        new_building_id = (last_building.id + 1) if last_building else 1
        
        # Create new building
        new_building = Building(
            id=new_building_id,
            name=building_name,
            address=building_address,
            google_sheet_id=data.get('google_sheet_id'),
            admin_id=None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_building)
        db.session.flush()
        
        # Create admin (auto-approved when created by superadmin)
        new_admin = Admin(
            user_name=user_name,
            email=email,
            password_hash=hash_password(password),
            phone_number=phone_number,
            building_id=new_building.id,
            status='approved',  # Auto-approve when created by superadmin
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_admin)
        db.session.flush()
        
        # Update building with admin_id
        new_building.admin_id = new_admin.id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Admin and building created successfully',
            'admin': {
                'id': new_admin.id,
                'user_name': new_admin.user_name,
                'email': new_admin.email,
                'phone_number': new_admin.phone_number,
                'building_id': new_admin.building_id,
                'status': new_admin.status,
                'created_at': new_admin.created_at.isoformat()
            },
            'building': {
                'id': new_building.id,
                'name': new_building.name,
                'address': new_building.address,
                'google_sheet_id': new_building.google_sheet_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create admin error: {str(e)}")
        return jsonify({'error': 'Failed to create admin'}), 500
    
@app.route('/admin/building', methods=['GET'])
@jwt_required()
def get_admin_building():
    """Get admin's building details"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        admin_id = get_jwt_identity()
        building_id = claims.get('building_id')
        
        building = Building.query.get(building_id)
        if not building:
            return jsonify({'error': 'Building not found'}), 404
        
        return jsonify({
            'building': {
                'id': building.id,
                'name': building.name,
                'address': building.address,
                'google_sheet_id': building.google_sheet_id,
                'cctv_settings': json.loads(building.cctv_settings) if building.cctv_settings else None,
                'created_at': building.created_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get building error: {str(e)}")
        return jsonify({'error': 'Failed to get building details'}), 500

@app.route('/admin/building/update', methods=['PUT'])
@jwt_required()
def update_admin_building():
    """Update admin's building details"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        admin_id = get_jwt_identity()
        building_id = claims.get('building_id')
        data = request.get_json()
        
        building = Building.query.get(building_id)
        if not building:
            return jsonify({'error': 'Building not found'}), 404
        
        # Update fields if provided
        if 'name' in data:
            building.name = data['name']
        if 'address' in data:
            building.address = data['address']
        if 'google_sheet_id' in data:
            building.google_sheet_id = data['google_sheet_id']
        if 'cctv_settings' in data:
            building.cctv_settings = json.dumps(data['cctv_settings'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Building updated successfully',
            'building': {
                'id': building.id,
                'name': building.name,
                'address': building.address,
                'google_sheet_id': building.google_sheet_id,
                'cctv_settings': json.loads(building.cctv_settings) if building.cctv_settings else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update building error: {str(e)}")
        return jsonify({'error': 'Failed to update building'}), 500
    
        
@app.route('/admin/guards', methods=['GET'])
@jwt_required()
def list_guards():
    """List all guards for admin's building"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        admin_building_id = claims.get('building_id')
        
        # Get guards for admin's building
        guards = Guard.query.filter_by(building_id=admin_building_id).all()
        
        guards_data = [{
            'id': guard.id,
            'user_name': guard.user_name,
            'email': guard.email,
            'phone_number': guard.phone_number,
            'status': guard.status,
            'created_at': guard.created_at.isoformat(),
            'updated_at': guard.updated_at.isoformat()
        } for guard in guards]
        
        return jsonify({'guards': guards_data}), 200
        
    except Exception as e:
        logger.error(f"List guards error: {str(e)}")
        return jsonify({'error': 'Failed to get guards list'}), 500
    
@app.route('/admin/guards/<int:guard_id>/status', methods=['PATCH'])
@jwt_required()
def update_guard_status(guard_id):
    """Activate or deactivate a guard"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['active', 'inactive']:
            return jsonify({'error': 'Status must be "active" or "inactive"'}), 400
        
        guard = Guard.query.get(guard_id)
        if not guard:
            return jsonify({'error': 'Guard not found'}), 404
        
        # Check if guard belongs to admin's building
        if guard.building_id != claims.get('building_id'):
            return jsonify({'error': 'Access denied to this guard'}), 403
        
        guard.status = status
        db.session.commit()
        
        return jsonify({
            'message': f'Guard status updated to {status}',
            'guard': {
                'id': guard.id,
                'user_name': guard.user_name,
                'status': guard.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update guard status error: {str(e)}")
        return jsonify({'error': 'Failed to update guard status'}), 500
    
    
    
@app.route('/auth/superadmin/login', methods=['POST'])
def superadmin_login():
    """SuperAdmin login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        superadmin = SuperAdmin.query.filter_by(email=email, status='active').first()
        if superadmin and check_password(superadmin.password_hash, password):
            additional_claims = {'role': 'superadmin', 'user_name': superadmin.user_name}
            access_token = create_access_token(
                identity=str(superadmin.id),
                additional_claims=additional_claims
            )
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': {
                    'id': superadmin.id,
                    'user_name': superadmin.user_name,
                    'email': superadmin.email,
                    'role': 'superadmin'
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials or account inactive'}), 401
            
    except Exception as e:
        logger.error(f"SuperAdmin login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500            
    
# @app.route('/auth/user/verify', methods=['POST'])
# def user_verify_otp():
#     """Verify OTP and login user"""
#     try:
#         data = request.get_json()
#         user_id = data.get('user_id')
#         otp = data.get('otp')
        
#         if not user_id or not otp:
#             return jsonify({'error': 'User ID and OTP required'}), 400
        
#         otp_data = otp_storage.get(int(user_id))
#         if not otp_data:
#             return jsonify({'error': 'OTP not found or expired. Please request a new one.'}), 404
        
#         if datetime.utcnow() - otp_data['timestamp'] > timedelta(minutes=10):
#             del otp_storage[int(user_id)]
#             return jsonify({'error': 'OTP expired'}), 400
        
#         if otp_data['otp'] == otp:
#             user = Resident.query.get(int(user_id))
#             if not user:
#                 return jsonify({'error': 'User not found'}), 404
            
#             additional_claims = {'role': 'resident', 'building_id': user.building_id, 'user_name': user.user_name}
#             access_token = create_access_token(
#                 identity=user.id,
#                 additional_claims=additional_claims
#             )
            
#             del otp_storage[int(user_id)]
            
#             return jsonify({
#                 'message': 'Login successful',
#                 'access_token': access_token,
#                 'user': {
#                     'id': user.id,
#                     'user_name': user.user_name,
#                     'email': user.email,
#                     'building_id': user.building_id,
#                     'role': 'resident'
#                 }
#             }), 200
#         else:
#             return jsonify({'error': 'Invalid OTP'}), 401
            
#     except Exception as e:
#         logger.error(f"OTP verification error: {str(e)}")
#         return jsonify({'error': 'Verification failed'}), 500

@app.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logout successful'}), 200


# --- GUARD APP APIs ---
@app.route('/guard/dashboard/stats', methods=['GET'])
@jwt_required()
def guard_dashboard_stats():
    try:
        claims = get_jwt()
        if claims.get('role') != 'guard':
            return jsonify({'error': 'Access denied'}), 403
        
        guard_id = get_jwt_identity()
        today = datetime.utcnow().date()
        
        total_scans = Log.query.filter_by(guard_id=guard_id).count()
        total_entries = Log.query.filter_by(guard_id=guard_id, action='entry').count()
        total_exits = Log.query.filter_by(guard_id=guard_id, action='exit').count()
        today_scans = Log.query.filter(
            Log.guard_id == guard_id,
            db.func.date(Log.timestamp) == today
        ).count()
        
        return jsonify({
            'stats': {
                'total_scans': total_scans,
                'total_entries': total_entries,
                'total_exits': total_exits,
                'today_scans': today_scans
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Guard stats error: {str(e)}")
        return jsonify({'error': 'Failed to get stats'}), 500

@app.route('/guard/dashboard/last-scan', methods=['GET'])
@jwt_required()
def guard_last_scan():
    try:
        claims = get_jwt()
        if claims.get('role') != 'guard':
            return jsonify({'error': 'Access denied'}), 403
        
        guard_id = get_jwt_identity()
        
        last_scan = Log.query.filter_by(guard_id=guard_id).order_by(Log.timestamp.desc()).first()
        
        if last_scan:
            scan_data = {
                'license_plate': last_scan.license_plate,
                'action': last_scan.action,
                'result': last_scan.result,
                'timestamp': last_scan.timestamp.isoformat(),
                'notes': last_scan.notes
            }
            return jsonify({'last_scan': scan_data}), 200
        else:
            return jsonify({'last_scan': None}), 200
            
    except Exception as e:
        logger.error(f"Last scan error: {str(e)}")
        return jsonify({'error': 'Failed to get last scan'}), 500

# --- NEW OCR ENDPOINTS ---
@app.route('/guard/scan/ocr', methods=['POST'])
@jwt_required()
def ocr_scan_upload_fixed():
    """OCR scan endpoint with fixed response format for React app"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'guard':
            return jsonify({'error': 'Access denied'}), 403
        
        guard_id = get_jwt_identity()
        building_id = claims.get('building_id')
        
        # Check if image is provided
        data = request.get_json()
        if not data or 'image_data' not in data:
            return jsonify({'error': 'No image_data provided in JSON body'}), 400

        image_data = data.get('image_data')


        # Extract license plate using OCR
        license_plate, message = extract_license_plate(image_data)
        
        if not license_plate:
            return jsonify({
                'success': False,
                'message': message,
                'data': None
            }), 200
        
        # Verify license plate
        verification_result = verify_license_plate(license_plate, building_id)
        
        # Prepare response data for React app
        response_data = {
            'numberPlate': license_plate,
            'vehicleType': verification_result.get('data', {}).get('vehicle_type', 'Unknown'),
            'ownerName': verification_result.get('data', {}).get('owner_name', 'Unknown'),
            'status': verification_result.get('status', 'not_found')
        }
        
        # Log the scan
        log_entry = Log(
            license_plate=license_plate,
            action='scan',
            result=verification_result.get('status', 'not_found'),
            source=verification_result.get('source', 'not_found'),
            guard_id=guard_id,
            notes=f'OCR scan: {message}',
            captured_image=image_data[:100] + '...' if image_data else None  # Store partial image data
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'License plate extracted successfully',
            'data': response_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"OCR scan error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'OCR processing failed: {str(e)}',
            'data': None
        }), 500
        
        
        

@app.route('/guard/scan/quick-verify', methods=['POST'])
@jwt_required()
def quick_verify():
    """Quick verify endpoint that combines OCR + verification in one call"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'guard':
            return jsonify({'error': 'Access denied'}), 403
        
        guard_id = get_jwt_identity()
        building_id = claims.get('building_id')
        
        data = request.get_json()
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Step 1: Extract license plate using OCR
        license_plate, ocr_message = extract_license_plate(image_data)
        
        if not license_plate:
            # Log failed OCR attempt
            log_entry = Log(
                license_plate='UNKNOWN',
                action='scan',
                result='not_found',
                source='not_found',
                guard_id=guard_id,
                notes=f'OCR failed: {ocr_message}',
                captured_image=image_data
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({
                'success': False,
                'message': ocr_message,
                'license_plate': None,
                'verified': False
            }), 200
        
        # Step 2: Verify license plate
        verification_result = verify_license_plate(license_plate, building_id)
        
        # Step 3: Map verification status to log result
        result_status = verification_result['status']
        if result_status == 'registered':  # From Google Sheets
            log_result = 'registered'
        elif result_status == 'approved':  # From MySQL - approved vehicle
            log_result = 'approved'  
        elif result_status == 'pending':   # From MySQL - pending approval
            log_result = 'pending'
        elif result_status == 'rejected':  # From MySQL - rejected vehicle
            log_result = 'not_found'  # Treat rejected as not found for access purposes
        else:
            log_result = 'not_found'  # Default for not_found or other statuses
        
        # Step 4: Log the action
        log_entry = Log(
            license_plate=license_plate,
            action='scan',
            result=log_result,
            source=verification_result['source'],
            guard_id=guard_id,
            notes=f'Quick verify: {ocr_message} | Verification: {result_status}',
            captured_image=image_data
        )
        
        # Add vehicle ID if found in MySQL (not from Google Sheets)
        if verification_result['source'] == 'mysql' and 'vehicle_id' in verification_result:
            log_entry.vehicle_id = verification_result['vehicle_id']
        
        db.session.add(log_entry)
        db.session.commit()
        
        # Step 5: Prepare response - consider vehicle "verified" if registered or approved
        is_verified = result_status in ['registered', 'approved']
        
        response_data = {
            'success': True,
            'message': f'License plate extracted: {license_plate}',
            'license_plate': license_plate,
            'verified': is_verified,
            'verification_details': verification_result,
            'log_result': log_result  # For debugging
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Quick verify error: {str(e)}")
        return jsonify({'error': 'Quick verification failed'}), 500
# --- END NEW OCR ENDPOINTS ---

@app.route('/guard/scan/register', methods=['POST'])
@jwt_required()
def register_vehicle():
    """Register a new vehicle (for manual entry after OCR fails)"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'guard':
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Extract vehicle data
        license_plate = data.get('numberPlate')
        vehicle_type = data.get('vehicleType')
        owner_name = data.get('ownerName')
        vehicle_model = data.get('vehicleModel')
        color = data.get('color')
        
        if not license_plate or not vehicle_type:
            return jsonify({'error': 'Number plate and vehicle type are required'}), 400
        
        # Check if vehicle already exists
        existing_vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
        if existing_vehicle:
            return jsonify({'error': 'Vehicle with this license plate already exists'}), 409
        
        # Create new vehicle (pending approval)
        new_vehicle = Vehicle(
            license_plate=license_plate,
            model=vehicle_model,
            vehicle_type=vehicle_type,
            color=color,
            owner_type='resident',  # Default to resident
            owner_name=owner_name or 'Unknown',
            status='pending',
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_vehicle)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Vehicle registered successfully and pending approval',
            'vehicle_id': new_vehicle.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Vehicle registration error: {str(e)}")
        return jsonify({'error': 'Failed to register vehicle'}), 500

@app.route('/guard/scan/manual-entry', methods=['POST'])
@jwt_required()
def manual_plate_entry():
    try:
        claims = get_jwt()
        if claims.get('role') != 'guard':
            return jsonify({'error': 'Access denied'}), 403
        
        guard_id = get_jwt_identity()
        building_id = claims.get('building_id')
        data = request.get_json()
        
        license_plate = data.get('license_plate')
        if not license_plate:
            return jsonify({'error': 'License plate required'}), 400
        
        notes = data.get('notes', '')
        
        logger.info(f"Manual entry request: {license_plate} for building {building_id}")
        
        # TWO-LAYER VERIFICATION: Google Sheets → MySQL
        
        # Step 1: First check Google Sheet
        google_result = check_google_sheet(license_plate, building_id)
        
        if google_result:
            if google_result.get('found'):
                # Found in Google Sheet - registered vehicle
                log_entry = Log(
                    license_plate=license_plate,
                    action='manual_entry',
                    result='registered',
                    source=google_result.get('source', 'google_sheet'),
                    guard_id=guard_id,
                    notes=f'{notes} | Sheet data: {google_result.get("data")}'
                )
                result_msg = f'Vehicle registered ({google_result.get("source", "Google Sheet")})'
                result_type = 'registered'
                
            else:
                # Google Sheet accessible but plate not found
                logger.info("Google Sheet accessible but plate not found, checking MySQL...")
                # Continue to MySQL check
                google_result = None
        else:
            # Google Sheet not accessible
            logger.warning("Google Sheet not accessible, checking MySQL directly...")
        
        # Step 2: If not found in Google Sheet (or not accessible), check MySQL database
        if not google_result or not google_result.get('found'):
            vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
            
            if vehicle:
                # Found in MySQL database
                log_entry = Log(
                    vehicle_id=vehicle.id,
                    license_plate=license_plate,
                    action='manual_entry',
                    result='registered',
                    source='mysql',
                    guard_id=guard_id,
                    notes=notes
                )
                result_msg = 'Vehicle registered (Database)'
                result_type = 'registered'
                source = 'mysql'
            else:
                # Not found in either Google Sheet or MySQL - unregistered vehicle
                unregistered_visit = UnregisteredVisit(
                    license_plate=license_plate,
                    guard_id=guard_id,
                    notes=notes,
                    building_id=building_id
                )
                db.session.add(unregistered_visit)
                db.session.flush()
                
                log_entry = Log(
                    unregistered_visit_id=unregistered_visit.id,
                    license_plate=license_plate,
                    action='manual_entry',
                    result='unregistered',
                    source='not_found',
                    guard_id=guard_id,
                    notes=f'{notes} | Checked: Google Sheet & Database'
                )
                result_msg = 'Unregistered vehicle logged'
                result_type = 'unregistered'
                source = 'not_found'
        
        db.session.add(log_entry)
        db.session.commit()
        
        logger.info(f"Manual entry result: {result_msg}")
        
        return jsonify({
            'message': result_msg,
            'result': result_type,
            'license_plate': license_plate,
            'source': log_entry.source
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Manual entry error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to log manual entry'}), 500

@app.route('/guard/scan/confirm-entry', methods=['POST'])
@jwt_required()
def confirm_entry():
    try:
        claims = get_jwt()
        if claims.get('role') != 'guard':
            return jsonify({'error': 'Access denied'}), 403
        
        guard_id = get_jwt_identity()
        data = request.get_json()
        
        license_plate = data.get('license_plate')
        captured_image = data.get('captured_image')
        
        if not license_plate:
            return jsonify({'error': 'License plate required'}), 400
        
        vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
        
        if vehicle and vehicle.status == 'approved':
            log_entry = Log(
                vehicle_id=vehicle.id,
                license_plate=license_plate,
                action='entry',
                result='registered',
                source='mysql',
                guard_id=guard_id,
                captured_image=captured_image,
                notes='Vehicle entry confirmed'
            )
            result_type = 'registered'
        else:
            unregistered_visit = UnregisteredVisit(
                license_plate=license_plate,
                guard_id=guard_id,
                building_id=claims.get('building_id'),
                vehicle_image=captured_image
            )
            db.session.add(unregistered_visit)
            db.session.flush()
            
            log_entry = Log(
                unregistered_visit_id=unregistered_visit.id,
                license_plate=license_plate,
                action='entry',
                result='unregistered',
                source='mysql',
                guard_id=guard_id,
                captured_image=captured_image,
                notes='Unregistered vehicle entry'
            )
            result_type = 'unregistered'
            
            # Here you might want to notify all admins of this building
            admins = Admin.query.filter_by(building_id=claims.get('building_id')).all()
            for admin in admins:
                create_notification(
                    user_type='admin',
                    user_id=admin.id,
                    notification_type='suspicious_activity',
                    message=f'Unregistered vehicle {license_plate} entered the premises'
                )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'message': 'Entry confirmed',
            'result': result_type,
            'license_plate': license_plate
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Confirm entry error: {str(e)}")
        return jsonify({'error': 'Failed to confirm entry'}), 500

@app.route('/guard/scan/confirm-exit', methods=['POST'])
@jwt_required()
def confirm_exit():
    try:
        claims = get_jwt()
        if claims.get('role') != 'guard':
            return jsonify({'error': 'Access denied'}), 403
        
        guard_id = get_jwt_identity()
        data = request.get_json()
        license_plate = data.get('license_plate')
        
        if not license_plate:
            return jsonify({'error': 'License plate required'}), 400
        
        unregistered_visit = UnregisteredVisit.query.filter_by(
            license_plate=license_plate,
            exit_timestamp=None
        ).order_by(UnregisteredVisit.entry_timestamp.desc()).first()
        
        visit_id = None
        result_type = 'registered'
        if unregistered_visit:
            unregistered_visit.exit_timestamp = datetime.utcnow()
            visit_id = unregistered_visit.id
            result_type = 'unregistered'
        
        vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
        
        log_entry = Log(
            vehicle_id=vehicle.id if vehicle else None,
            unregistered_visit_id=visit_id,
            license_plate=license_plate,
            action='exit',
            result=result_type,
            source='mysql',
            guard_id=guard_id,
            notes='Vehicle exit confirmed'
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'message': 'Exit confirmed',
            'result': result_type,
            'license_plate': license_plate
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Confirm exit error: {str(e)}")
        return jsonify({'error': 'Failed to confirm exit'}), 500

@app.route('/guard/logs/my-scans', methods=['GET'])
@jwt_required()
def guard_my_scans():
    try:
        claims = get_jwt()
        if claims.get('role') != 'guard':
            return jsonify({'error': 'Access denied'}), 403
        
        guard_id = get_jwt_identity()
        filter_type = request.args.get('filter', 'today') # today, week, all
        
        query = Log.query.filter_by(guard_id=guard_id)
        
        today = datetime.utcnow().date()
        if filter_type == 'today':
            # FIX: Use datetime.utcnow() instead of just datetime
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Log.timestamp >= start_date)
        elif filter_type == 'week':
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
            query = query.filter(Log.timestamp >= start_date)
        
        logs = query.order_by(Log.timestamp.desc()).limit(50).all()
        
        logs_data = [{
            'id': log.id,
            'license_plate': log.license_plate,
            'action': log.action,
            'result': log.result,
            'source': log.source,
            'timestamp': log.timestamp.isoformat(),
            'notes': log.notes,
            'snapshot_url': log.snapshot_url
        } for log in logs]
        
        return jsonify({'logs': logs_data}), 200
        
    except Exception as e:
        logger.error(f"Guard logs error: {str(e)}")
        return jsonify({'error': 'Failed to get logs'}), 500


# --- USER APP APIs ---
@app.route('/user/vehicles', methods=['GET'])
@jwt_required()
def get_my_vehicles():
    try:
        claims = get_jwt()
        user_name = claims.get('user_name')
        
        if claims.get('role') not in ['resident', 'rental']:
            return jsonify({'error': 'Access denied'}), 403
        
        vehicles = Vehicle.query.filter_by(owner_name=user_name).all()
        
        vehicles_data = [{
            'id': vehicle.id,
            'license_plate': vehicle.license_plate,
            'model': vehicle.model,
            'vehicle_type': vehicle.vehicle_type,
            'color': vehicle.color,
            'status': vehicle.status,
            'rejected_reason': vehicle.rejected_reason,
            'created_at': vehicle.created_at.isoformat() if vehicle.created_at else None
        } for vehicle in vehicles]
        
        return jsonify({'vehicles': vehicles_data}), 200
        
    except Exception as e:
        logger.error(f"Get vehicles error: {str(e)}")
        return jsonify({'error': 'Failed to get vehicles'}), 500

@app.route('/user/vehicles/add', methods=['POST'])
@jwt_required()
def add_vehicle():
    try:
        claims = get_jwt()
        if claims.get('role') not in ['resident', 'rental']:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        license_plate = data.get('license_plate')
        if not license_plate:
            return jsonify({'error': 'License plate required'}), 400
        
        if Vehicle.query.filter_by(license_plate=license_plate).first():
            return jsonify({'error': 'Vehicle with this license plate already exists'}), 409
        
        new_vehicle = Vehicle(
            license_plate=license_plate,
            model=data.get('model'),
            vehicle_type=data.get('vehicle_type'),
            color=data.get('color'),
            vehicle_image=data.get('vehicle_image'),
            owner_type=claims.get('role'),
            owner_name=claims.get('user_name'),
            status='pending',
            created_at=datetime.utcnow()
        )
        db.session.add(new_vehicle)
        
        admins = Admin.query.filter_by(building_id=claims.get('building_id')).all()
        for admin in admins:
            create_notification(
                user_type='admin',
                user_id=admin.id,
                notification_type='approval',
                message=f'New vehicle {license_plate} from {claims.get("user_name")} is awaiting approval.'
            )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Vehicle added successfully and is pending approval',
            'vehicle_id': new_vehicle.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Add vehicle error: {str(e)}")
        return jsonify({'error': 'Failed to add vehicle'}), 500

@app.route('/user/history', methods=['GET'])
@jwt_required()
def get_parking_history():
    try:
        claims = get_jwt()
        if claims.get('role') not in ['resident', 'rental']:
            return jsonify({'error': 'Access denied'}), 403
        
        user_vehicles = Vehicle.query.filter_by(owner_name=claims.get('user_name')).all()
        license_plates = [v.license_plate for v in user_vehicles]
        
        if not license_plates:
            return jsonify({'history': []}), 200

        logs = Log.query.filter(Log.license_plate.in_(license_plates)) \
            .order_by(Log.timestamp.desc()).limit(50).all()
        
        history_data = [{
            'license_plate': log.license_plate,
            'action': log.action,
            'result': log.result,
            'timestamp': log.timestamp.isoformat(),
            'notes': log.notes
        } for log in logs]
        
        return jsonify({'history': history_data}), 200
        
    except Exception as e:
        logger.error(f"Parking history error: {str(e)}")
        return jsonify({'error': 'Failed to get parking history'}), 500


# --- ADMIN DASHBOARD APIs ---
@app.route('/admin/dashboard/overview', methods=['GET'])
@jwt_required()
def admin_dashboard_overview():
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        building_id = claims.get('building_id')
        
        resident_vehicles_query = db.session.query(Vehicle).join(Resident, Vehicle.owner_name == Resident.user_name).filter(Resident.building_id == building_id)

        total_residents = Resident.query.filter_by(building_id=building_id).count()
        total_vehicles = resident_vehicles_query.count()
        pending_vehicles = resident_vehicles_query.filter(Vehicle.status == 'pending').count()

        today_logs = Log.query.join(Guard, Log.guard_id == Guard.id).filter(
            Guard.building_id == building_id,
            db.func.date(Log.timestamp) == datetime.utcnow().date()
        ).count()
        
        return jsonify({
            'stats': {
                'total_residents': total_residents,
                'total_vehicles': total_vehicles,
                'pending_vehicles': pending_vehicles,
                'today_logs': today_logs
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500

@app.route('/admin/vehicles', methods=['GET'])
@jwt_required()
def admin_list_vehicles():
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        status_filter = request.args.get('status')
        building_id = claims.get('building_id')
        
        query = Vehicle.query.join(Resident, Vehicle.owner_name == Resident.user_name).filter(Resident.building_id == building_id)
        
        if status_filter in ['pending', 'approved', 'rejected']:
            query = query.filter(Vehicle.status == status_filter)
        
        vehicles = query.order_by(Vehicle.created_at.desc()).all()
        
        vehicles_data = [{
            'id': vehicle.id,
            'license_plate': vehicle.license_plate,
            'model': vehicle.model,
            'vehicle_type': vehicle.vehicle_type,
            'color': vehicle.color,
            'owner_name': vehicle.owner_name,
            'status': vehicle.status,
            'rejected_reason': vehicle.rejected_reason,
            'created_at': vehicle.created_at.isoformat() if vehicle.created_at else None
        } for vehicle in vehicles]
        
        return jsonify({'vehicles': vehicles_data}), 200
        
    except Exception as e:
        logger.error(f"Admin vehicles list error: {str(e)}")
        return jsonify({'error': 'Failed to get vehicles list'}), 500

@app.route('/admin/vehicles/<int:vehicle_id>/approve', methods=['POST'])
@jwt_required()
def admin_approve_vehicle(vehicle_id):
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        vehicle.status = 'approved'
        vehicle.approved_by_admin_id = get_jwt_identity()
        vehicle.approved_at = datetime.utcnow()
        
        owner = Resident.query.filter_by(user_name=vehicle.owner_name).first()
        if owner:
            create_notification(
                user_type='resident',
                user_id=owner.id,
                notification_type='approval',
                message=f'Your vehicle {vehicle.license_plate} has been approved.'
            )
        
        db.session.commit()
        return jsonify({'message': 'Vehicle approved successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Approve vehicle error: {str(e)}")
        return jsonify({'error': 'Failed to approve vehicle'}), 500

@app.route('/admin/vehicles/<int:vehicle_id>/reject', methods=['POST'])
@jwt_required()
def admin_reject_vehicle(vehicle_id):
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        reason = request.json.get('reason', 'No reason provided.')
        
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        vehicle.status = 'rejected'
        vehicle.rejected_reason = reason
        
        owner = Resident.query.filter_by(user_name=vehicle.owner_name).first()
        if owner:
            create_notification(
                user_type='resident',
                user_id=owner.id,
                notification_type='rejection',
                message=f'Your vehicle {vehicle.license_plate} was rejected: {reason}'
            )
            
        db.session.commit()
        return jsonify({'message': 'Vehicle rejected successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Reject vehicle error: {str(e)}")
        return jsonify({'error': 'Failed to reject vehicle'}), 500


# --- NOTIFICATIONS APIs ---
@app.route('/notifications/my', methods=['GET'])
@jwt_required()
def get_my_notifications():
    try:
        claims = get_jwt()
        user_id = get_jwt_identity()
        user_role = claims.get('role')
        
        notifications = Notification.query.filter_by(
            user_type=user_role,
            user_id=user_id
        ).order_by(Notification.sent_at.desc()).limit(20).all()
        
        notifications_data = [{
            'id': notification.id,
            'type': notification.type,
            'message': notification.message,
            'sent_at': notification.sent_at.isoformat(),
            'is_read': notification.is_read
        } for notification in notifications]
        
        return jsonify({'notifications': notifications_data}), 200
        
    except Exception as e:
        logger.error(f"Get notifications error: {str(e)}")
        return jsonify({'error': 'Failed to get notifications'}), 500

@app.route('/notifications/<int:notification_id>/mark-read', methods=['PATCH'])
@jwt_required()
def mark_notification_read(notification_id):
    try:
        claims = get_jwt()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_type=claims.get('role'),
            user_id=get_jwt_identity()
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found or access denied'}), 404
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Notification marked as read'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Mark notification read error: {str(e)}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500


if __name__ == '__main__':
    with app.app_context():
        try:
            logger.info("Attempting to connect to the database...")
            db.engine.connect()
            logger.info("Database connection successful.")
            db.create_all()
            logger.info("Database tables checked/created.")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            # Exit or handle as needed, for now we just log it
    
    app.run(debug=True, host='0.0.0.0', port=5000)