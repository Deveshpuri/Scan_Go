import os
import mysql.connector
import json
from fastapi import FastAPI, HTTPException, Depends, status, Query, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
import pandas as pd
from io import StringIO
import uvicorn

# Add these to your existing imports at the top
import cv2
import numpy as np
import easyocr
import uuid
import logging

# Load environment variables
load_dotenv()

# FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://monitor-renewing-oarfish.ngrok-free.app",  "http://localhost:3000", "http://localhost:8000", "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MySQL connection
def get_db():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_DATABASE"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT"))
    )
    try:
        yield conn
    finally:
        conn.close()

# SMTP configuration
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Google Sheets setup
def get_google_sheets():
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        eval(os.getenv("GOOGLE_SHEETS_CREDENTIALS")),
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(credentials)
    return client.open("VehicleRegistry").sheet1

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# --- Password Handling Function ---
def validate_password_length(password: str):
    """
    Validates that the password does not exceed 72 bytes (bcrypt limit).
    Raises ValueError with a clean message if it does.
    """
    if len(password.encode('utf-8')) > 72:
        raise ValueError("Password cannot exceed 72 bytes. Please use a shorter password.")

# Pydantic models
class User(BaseModel):
    id: int
    username: str
    email: str
    role: str
    building_id: Optional[int]
    building_number: Optional[str]
    phone_number: Optional[str]
    flat_number: Optional[str]
    wing: Optional[str]
    status: str

class UserSignup(BaseModel):
    username: str
    email: str
    password: str
    building_id: int
    building_number: Optional[str] = None
    phone_number: Optional[str] = None
    flat_number: Optional[str] = None
    wing: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreateAdmin(BaseModel):
    username: str
    email: str
    password: str
    role: str
    building_id: Optional[int]
    building_number: Optional[str]
    phone_number: Optional[str]
    flat_number: Optional[str]
    wing: Optional[str]

class Vehicle(BaseModel):
    id: int
    license_plate: str
    chassis_number: Optional[str]
    model: Optional[str]
    vehicle_type: Optional[str]
    parking_slot: Optional[str]
    color: Optional[str]
    owner_id: int
    status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejected_reason: Optional[str]

class Log(BaseModel):
    id: int
    vehicle_id: Optional[int]
    unregistered_visit_id: Optional[int]
    license_plate: Optional[str]
    action: str
    result: str
    source: str
    timestamp: datetime
    guard_id: Optional[int]
    notes: Optional[str]
    snapshot_url: Optional[str]

class Notification(BaseModel):
    id: int
    user_id: int
    type: str
    message: str
    sent_at: datetime
    is_read: bool

class Building(BaseModel):
    id: int
    name: str
    address: Optional[str]
    cctv_settings: Optional[dict]

class VehicleCreate(BaseModel):
    license_plate: str
    chassis_number: Optional[str]
    model: Optional[str]
    vehicle_type: Optional[str]
    parking_slot: Optional[str]
    color: Optional[str]

class ScanRequest(BaseModel):
    license_plate: str
    camera_snapshot_url: Optional[str]

# ADD THESE MODELS WITH YOUR OTHER PYDANTIC MODELS:
class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    building_id: Optional[int] = None
    building_number: Optional[str] = None
    phone_number: Optional[str] = None
    flat_number: Optional[str] = None
    wing: Optional[str] = None
    status: str

class SignupResponse(BaseModel):
    user: UserResponse
    token: Token

# OCR Initialization
logger = logging.getLogger(__name__)
try:
    reader = easyocr.Reader(['en'])
    logger.info("EasyOCR initialized successfully")
except Exception as e:
    logger.error(f"EasyOCR initialization failed: {str(e)}")
    reader = None

# New Pydantic model for scan response
class ScanResponse(BaseModel):
    success: bool
    license_plate: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    vehicle_details: Optional[dict] = None

# Scan Utility Functions
def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for better OCR results
    """
    try:
        # Convert to grayscale if it's a color image
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
        
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        return image

def extract_license_plate_text(texts: list) -> Optional[str]:
    """
    Extract and validate license plate text from OCR results
    """
    license_plate_candidates = []
    
    for detection in texts:
        text = detection[1]  # The recognized text
        confidence = detection[2]  # Confidence score
        
        if confidence < 0.3:  # Skip low confidence results
            continue
            
        # Clean the text - remove spaces and special characters
        cleaned_text = ''.join(c for c in text.upper() if c.isalnum())
        
        # Indian license plate validation (adjust for your country)
        if len(cleaned_text) >= 6 and len(cleaned_text) <= 12:
            # Check if it contains both letters and numbers
            has_letters = any(c.isalpha() for c in cleaned_text)
            has_digits = any(c.isdigit() for c in cleaned_text)
            
            if has_letters and has_digits:
                license_plate_candidates.append((cleaned_text, confidence))
    
    if license_plate_candidates:
        # Return the highest confidence candidate
        best_candidate = max(license_plate_candidates, key=lambda x: x[1])
        logger.info(f"Selected license plate: {best_candidate[0]} with confidence: {best_candidate[1]}")
        return best_candidate[0]
    
    logger.warning("No valid license plate candidates found")
    return None

async def process_license_plate_image(image_path: str) -> Optional[str]:
    """
    Process image to extract license plate text
    """
    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            logger.error("Failed to read image file")
            return None
        
        logger.info(f"Image loaded successfully: {image.shape}")
        
        # Preprocess image
        processed_image = preprocess_image(image)
        
        # Perform OCR
        results = reader.readtext(processed_image)
        
        logger.info(f"OCR found {len(results)} text regions")
        
        # Extract license plate text
        license_plate = extract_license_plate_text(results)
        
        if license_plate:
            logger.info(f"License plate detected: {license_plate}")
        else:
            logger.warning("No license plate detected in image")
            
        return license_plate
        
    except Exception as e:
        logger.error(f"License plate processing failed: {str(e)}")
        return None

def save_uploaded_file(file: UploadFile, upload_dir: str = "uploads") -> str:
    """
    Save uploaded file to disk and return file path
    """
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)
        
        logger.info(f"File saved successfully: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")

async def verify_license_plate_db(license_plate: str, db) -> dict:
    """
    Verify license plate in database (Google Sheets → MySQL fallback)
    """
    try:
        # First try Google Sheets
        try:
            sheet = get_google_sheets()
            records = sheet.get_all_records()
            
            for record in records:
                if record.get("license_plate", "").upper() == license_plate.upper():
                    logger.info(f"License plate found in Google Sheets: {license_plate}")
                    return {
                        "status": record.get("status", "unknown"),
                        "source": "google_sheet",
                        "vehicle_details": record
                    }
        except Exception as e:
            logger.warning(f"Google Sheets lookup failed: {str(e)}")
        
        # Fallback to MySQL
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.*, u.username, u.building_number, u.flat_number 
            FROM vehicles v 
            LEFT JOIN users u ON v.owner_id = u.id 
            WHERE v.license_plate = %s
        """, (license_plate,))
        
        vehicle = cursor.fetchone()
        cursor.close()
        
        if vehicle:
            logger.info(f"License plate found in MySQL: {license_plate}")
            return {
                "status": vehicle["status"],
                "source": "mysql",
                "vehicle_details": {
                    "license_plate": vehicle["license_plate"],
                    "model": vehicle["model"],
                    "color": vehicle["color"],
                    "owner": vehicle["username"],
                    "building": vehicle["building_number"],
                    "flat": vehicle["flat_number"],
                    "vehicle_type": vehicle["vehicle_type"]
                }
            }
        else:
            # Check unregistered visits
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM unregistered_visits 
                WHERE license_plate = %s AND exit_timestamp IS NULL
                ORDER BY entry_timestamp DESC LIMIT 1
            """, (license_plate,))
            
            visit = cursor.fetchone()
            cursor.close()
            
            if visit:
                logger.info(f"License plate found in unregistered visits: {license_plate}")
                return {
                    "status": "unregistered",
                    "source": "mysql",
                    "vehicle_details": {
                        "license_plate": visit["license_plate"],
                        "visitor_name": visit["visitor_name"],
                        "notes": visit["notes"],
                        "entry_time": visit["entry_timestamp"].isoformat() if visit["entry_timestamp"] else None
                    }
                }
        
        logger.info(f"License plate not found: {license_plate}")
        return {
            "status": "not_found",
            "source": "not_found",
            "vehicle_details": None
        }
        
    except Exception as e:
        logger.error(f"License plate verification failed: {str(e)}")
        return {
            "status": "error",
            "source": "error",
            "vehicle_details": None
        }

# JWT helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND status = 'approved'", (username,))
        user = cursor.fetchone()
        cursor.close()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found or not approved")
        return User(**user)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def send_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {str(e)}") # Log error instead of raising HTTPException

# --- Authentication & User Endpoints (Updated) ---

@app.post("/api/auth/signup", response_model=SignupResponse)
async def signup(user: UserSignup, db=Depends(get_db)):
    # 1. Validate password first
    try:
        validate_password_length(user.password)
        hashed_password = pwd_context.hash(user.password)
    except ValueError:
        raise HTTPException(status_code=400, detail="Password cannot exceed 72 bytes. Please use a shorter password.")

    # 2. Proceed with database operations
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, building_id, building_number, phone_number, flat_number, wing, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                user.username,
                user.email,
                hashed_password,
                "resident",
                user.building_id,
                user.building_number,
                user.phone_number,
                user.flat_number,
                user.wing,
                "approved"
            )
        )
        db.commit()
        
        # Get the newly created user
        cursor.execute("SELECT * FROM users WHERE id = LAST_INSERT_ID()")
        new_user = cursor.fetchone()
        
        # Create access token for immediate login
        access_token = create_access_token({"sub": new_user["username"]})
        
        send_email(user.email, "Account Created", f"Welcome, {user.username}! Your resident account has been created successfully.")
        
        # RETURN BOTH USER AND TOKEN
        return {
            "user": {
                "id": new_user["id"],
                "username": new_user["username"],
                "email": new_user["email"],
                "role": new_user["role"],
                "building_id": new_user["building_id"],
                "building_number": new_user["building_number"],
                "phone_number": new_user["phone_number"],
                "flat_number": new_user["flat_number"],
                "wing": new_user["wing"],
                "status": new_user["status"]
            },
            "token": {
                "access_token": access_token,
                "token_type": "bearer"
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")
    finally:
        cursor.close()


@app.post("/api/auth/login")
async def login(request: dict, db=Depends(get_db)):
    """
    Login endpoint that works with raw JSON
    """
    print("🔍 LOGIN DEBUG - Received:", request)
    
    username = request.get("username")
    password = request.get("password")
    
    if not username:
        raise HTTPException(status_code=422, detail="Username is required")
    if not password:
        raise HTTPException(status_code=422, detail="Password is required")
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s AND status = 'approved'", (username,))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        raise HTTPException(status_code=401, detail="User not found or not approved")
        
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Add this endpoint anywhere in your api.py file (preferably after imports)
@app.get("/api/test")
async def test():
    return {"message": "API is working!"}
@app.post("/api/debug-json")
async def debug_json(data: dict):
    return {"received_data": data, "message": "JSON is working!"}
@app.post("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.patch("/api/users/{user_id}/password")
async def change_password(user_id: int, new_password: str, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.id != user_id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 1. Validate password first
    try:
        validate_password_length(new_password)
        hashed_password = pwd_context.hash(new_password)
    except ValueError:
        raise HTTPException(status_code=400, detail="Password cannot exceed 72 bytes. Please use a shorter password.")
    
    # 2. Proceed with database operation
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_password, user_id))
        db.commit()
        return {"message": "Password updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating password: {str(e)}")
    finally:
        cursor.close()

@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "guard", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@app.post("/api/admin/users", response_model=User)
async def create_user(
    user: UserCreateAdmin,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 1. Validate password first
    try:
        validate_password_length(user.password)
        hashed_password = pwd_context.hash(user.password)
    except ValueError:
        raise HTTPException(status_code=400, detail="Password cannot exceed 72 bytes. Please use a shorter password.")
    
    # 2. Proceed with database operations
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        status = "pending" if user.role == "admin" else "approved"
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, building_id, building_number, phone_number, flat_number, wing, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                user.username,
                user.email,
                hashed_password,
                user.role,
                user.building_id,
                user.building_number,
                user.phone_number,
                user.flat_number,
                user.wing,
                status
            )
        )
        db.commit()
        cursor.execute("SELECT * FROM users WHERE id = LAST_INSERT_ID()")
        new_user = cursor.fetchone()
        
        send_email(user.email, "Account Created", f"Your {user.role} account has been created.{' Awaiting superadmin approval.' if status == 'pending' else ''}")
        
        if user.role == "admin":
            cursor.execute("SELECT email FROM users WHERE role = 'superadmin'")
            superadmins = cursor.fetchall()
            for superadmin in superadmins:
                send_email(
                    superadmin["email"],
                    "New Admin Account Awaiting Approval",
                    f"A new admin account ({user.username}) has been created and requires your approval."
                )
        
        return User(**new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")
    finally:
        cursor.close()

# --- Keep all other existing endpoints and code unchanged ---

# Dashboard Metrics
@app.get("/api/admin/metrics")
async def get_metrics(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total_vehicles FROM vehicles")
        total_vehicles = cursor.fetchone()["total_vehicles"]
        cursor.execute("""
            SELECT COUNT(*) as currently_inside 
            FROM logs 
            WHERE action = 'entry' 
            AND id NOT IN (SELECT id FROM logs WHERE action = 'exit')
        """)
        currently_inside = cursor.fetchone()["currently_inside"]
        cursor.execute("SELECT COUNT(*) as pending_requests FROM vehicles WHERE status = 'pending'")
        pending_requests = cursor.fetchone()["pending_requests"]
        cursor.execute("""
            SELECT v.*, l.action, l.timestamp 
            FROM vehicles v 
            LEFT JOIN logs l ON v.id = l.vehicle_id 
            ORDER BY v.created_at DESC LIMIT 10
        """)
        recent_requests = cursor.fetchall()
        return {
            "total_vehicles": total_vehicles,
            "currently_inside": currently_inside,
            "pending_requests": pending_requests,
            "recent_requests": recent_requests
        }
    finally:
        cursor.close()

# Vehicles
@app.get("/api/admin/vehicles", response_model=List[Vehicle])
async def list_vehicles(
    status: Optional[str] = Query(None),
    license_plate: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    query = "SELECT * FROM vehicles WHERE 1=1"
    params = []
    if status:
        query += " AND status = %s"
        params.append(status)
    if license_plate:
        query += " AND license_plate LIKE %s"
        params.append(f"%{license_plate}%")
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    vehicles = cursor.fetchall()
    cursor.close()
    return [Vehicle(**v) for v in vehicles]

@app.get("/api/admin/vehicles/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))
    vehicle = cursor.fetchone()
    cursor.close()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return Vehicle(**vehicle)

@app.patch("/api/admin/vehicles/{vehicle_id}/block")
async def block_vehicle(vehicle_id: int, block: bool, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    status = "rejected" if block else "approved"
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE vehicles SET status = %s, approved_by = %s, approved_at = %s WHERE id = %s",
            (status, current_user.id, datetime.utcnow(), vehicle_id)
        )
        db.commit()
        return {"message": f"Vehicle {'blocked' if block else 'unblocked'}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating vehicle: {str(e)}")
    finally:
        cursor.close()

@app.patch("/api/admin/vehicles/{vehicle_id}/approve")
async def approve_vehicle(vehicle_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))
        vehicle = cursor.fetchone()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        cursor.execute(
            "UPDATE vehicles SET status = %s, approved_by = %s, approved_at = %s WHERE id = %s",
            ("approved", current_user.id, datetime.utcnow(), vehicle_id)
        )
        db.commit()
        cursor.execute("SELECT email FROM users WHERE id = %s", (vehicle["owner_id"],))
        owner = cursor.fetchone()
        if owner:
            send_email(owner["email"], "Vehicle Approved", f"Your vehicle {vehicle['license_plate']} has been approved.")
        return {"message": "Vehicle approved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error approving vehicle: {str(e)}")
    finally:
        cursor.close()

@app.patch("/api/admin/vehicles/{vehicle_id}/reject")
async def reject_vehicle(vehicle_id: int, reason: str, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))
        vehicle = cursor.fetchone()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        cursor.execute(
            "UPDATE vehicles SET status = %s, approved_by = %s, approved_at = %s, rejected_reason = %s WHERE id = %s",
            ("rejected", current_user.id, datetime.utcnow(), reason, vehicle_id)
        )
        db.commit()
        cursor.execute("SELECT email FROM users WHERE id = %s", (vehicle["owner_id"],))
        owner = cursor.fetchone()
        if owner:
            send_email(owner["email"], "Vehicle Rejected", f"Your vehicle {vehicle['license_plate']} was rejected: {reason}")
        return {"message": "Vehicle rejected"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error rejecting vehicle: {str(e)}")
    finally:
        cursor.close()

@app.get("/api/admin/vehicles/{vehicle_id}/qr")
async def get_vehicle_qr(vehicle_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT license_plate FROM vehicles WHERE id = %s", (vehicle_id,))
    vehicle = cursor.fetchone()
    cursor.close()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    qr_data = f"vehicle:{vehicle['license_plate']}"
    return {"qr_data": qr_data}

@app.post("/api/resident/vehicles", response_model=Vehicle)
async def create_vehicle(vehicle: VehicleCreate, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "resident":
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO vehicles (license_plate, chassis_number, model, vehicle_type, parking_slot, color, owner_id, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
            """,
            (
                vehicle.license_plate,
                vehicle.chassis_number,
                vehicle.model,
                vehicle.vehicle_type,
                vehicle.parking_slot,
                vehicle.color,
                current_user.id
            )
        )
        db.commit()
        cursor.execute("SELECT * FROM vehicles WHERE id = LAST_INSERT_ID()")
        new_vehicle = cursor.fetchone()
        cursor.execute("SELECT email FROM users WHERE role IN ('admin', 'superadmin')")
        admins = cursor.fetchall()
        for admin in admins:
            send_email(admin["email"], "New Vehicle Request", f"New vehicle {vehicle.license_plate} awaiting approval.")
        return Vehicle(**new_vehicle)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating vehicle: {str(e)}")
    finally:
        cursor.close()

@app.patch("/api/resident/vehicles/{vehicle_id}", response_model=Vehicle)
async def update_vehicle(vehicle_id: int, vehicle: VehicleCreate, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "resident":
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM vehicles WHERE id = %s AND owner_id = %s", (vehicle_id, current_user.id))
        existing_vehicle = cursor.fetchone()
        if not existing_vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found or not owned")
        cursor.execute(
            """
            UPDATE vehicles 
            SET license_plate = %s, chassis_number = %s, model = %s, vehicle_type = %s, 
                parking_slot = %s, color = %s, status = 'pending'
            WHERE id = %s
            """,
            (
                vehicle.license_plate,
                vehicle.chassis_number,
                vehicle.model,
                vehicle.vehicle_type,
                vehicle.parking_slot,
                vehicle.color,
                vehicle_id
            )
        )
        db.commit()
        cursor.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))
        updated_vehicle = cursor.fetchone()
        return Vehicle(**updated_vehicle)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating vehicle: {str(e)}")
    finally:
        cursor.close()

@app.delete("/api/resident/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "resident":
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM vehicles WHERE id = %s AND owner_id = %s", (vehicle_id, current_user.id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vehicle not found or not owned")
        db.commit()
        return {"message": "Vehicle deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting vehicle: {str(e)}")
    finally:
        cursor.close()

# Vehicle Requests
@app.get("/api/admin/requests", response_model=List[Vehicle])
async def list_requests(status: Optional[str] = Query("pending"), current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehicles WHERE status = %s", (status,))
    requests = cursor.fetchall()
    cursor.close()
    return [Vehicle(**r) for r in requests]

@app.patch("/api/admin/requests/{request_id}/approve")
async def approve_request(request_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    return await approve_vehicle(request_id, current_user, db)

@app.patch("/api/admin/requests/{request_id}/reject")
async def reject_request(request_id: int, reason: str, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    return await reject_vehicle(request_id, reason, current_user, db)

# Logs / In-Out History
@app.get("/api/admin/logs", response_model=List[Log])
async def list_logs(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    guard_id: Optional[int] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    building_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    query = """
        SELECT l.* FROM logs l 
        LEFT JOIN vehicles v ON l.vehicle_id = v.id 
        LEFT JOIN unregistered_visits uv ON l.unregistered_visit_id = uv.id 
        WHERE 1=1
    """
    params = []
    if date_from:
        query += " AND l.timestamp >= %s"
        params.append(date_from)
    if date_to:
        query += " AND l.timestamp <= %s"
        params.append(date_to)
    if guard_id:
        query += " AND l.guard_id = %s"
        params.append(guard_id)
    if vehicle_id:
        query += " AND l.vehicle_id = %s"
        params.append(vehicle_id)
    if building_id:
        query += " AND (v.owner_id IN (SELECT id FROM users WHERE building_id = %s) OR uv.building_id = %s)"
        params.extend([building_id, building_id])
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    logs = cursor.fetchall()
    cursor.close()
    return [Log(**log) for log in logs]

@app.get("/api/admin/logs/export")
async def export_logs(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM logs")
    logs = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(logs)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    return {"csv_data": csv_buffer.getvalue()}

@app.get("/api/guard/logs", response_model=List[Log])
async def guard_logs(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "guard":
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM logs WHERE guard_id = %s OR building_id = %s", (current_user.id, current_user.building_id))
    logs = cursor.fetchall()
    cursor.close()
    return [Log(**log) for log in logs]

@app.post("/api/guard/logs")
async def create_manual_log(
    license_plate: str,
    visitor_name: Optional[str],
    visitor_email: Optional[str],
    notes: Optional[str],
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != "guard":
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO unregistered_visits (license_plate, visitor_name, visitor_email, guard_id, building_id, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (license_plate, visitor_name, visitor_email, current_user.id, current_user.building_id, notes)
        )
        db.commit()
        cursor.execute("SELECT LAST_INSERT_ID() as id")
        visit_id = cursor.fetchone()["id"]
        cursor.execute(
            """
            INSERT INTO logs (unregistered_visit_id, license_plate, action, result, source, guard_id, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (visit_id, license_plate, "manual_entry", "unregistered", "mysql", current_user.id, notes)
        )
        db.commit()
        return {"message": "Manual log created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating log: {str(e)}")
    finally:
        cursor.close()

@app.post("/api/scan")
async def scan_vehicle(scan: ScanRequest, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "guard":
        raise HTTPException(status_code=403, detail="Not authorized")
    license_plate = scan.license_plate
    try:
        sheet = get_google_sheets()
        records = sheet.get_all_records()
        for record in records:
            if record["license_plate"] == license_plate:
                cursor = db.cursor()
                cursor.execute(
                    """
                    INSERT INTO logs (license_plate, action, result, source, guard_id, snapshot_url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (license_plate, "scan", record["status"], "google_sheet", current_user.id, scan.camera_snapshot_url)
                )
                db.commit()
                cursor.close()
                return {"result": record["status"], "source": "google_sheet"}
    except Exception:
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM vehicles WHERE license_plate = %s", (license_plate,))
            vehicle = cursor.fetchone()
            if vehicle:
                result = vehicle["status"]
                source = "mysql"
            else:
                result = "not_found"
                source = "not_found"
            cursor.execute(
                """
                INSERT INTO logs (license_plate, action, result, source, guard_id, snapshot_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (license_plate, "scan", result, source, current_user.id, scan.camera_snapshot_url)
            )
            db.commit()
            return {"result": result, "source": source}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error scanning vehicle: {str(e)}")
        finally:
            cursor.close()

# Users
@app.get("/api/admin/users", response_model=List[User])
async def list_users(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    return [User(**u) for u in users]

@app.get("/api/admin/users/{user_id}", response_model=User)
async def get_user_admin(user_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    return await get_user(user_id, current_user, db)

@app.patch("/api/admin/users/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    username: Optional[str],
    email: Optional[str],
    role: Optional[str],
    building_id: Optional[int],
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        query = "UPDATE users SET "
        params = []
        if username:
            query += "username = %s, "
            params.append(username)
        if email:
            query += "email = %s, "
            params.append(email)
        if role:
            query += "role = %s, "
            params.append(role)
        if building_id is not None:
            query += "building_id = %s, "
            params.append(building_id)
        query = query.rstrip(", ") + " WHERE id = %s"
        params.append(user_id)
        cursor.execute(query, params)
        db.commit()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        updated_user = cursor.fetchone()
        return User(**updated_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")
    finally:
        cursor.close()

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        db.commit()
        return {"message": "User deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
    finally:
        cursor.close()

@app.patch("/api/superadmin/users/{user_id}/approve", response_model=User)
async def approve_user(user_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'admin' AND status = 'pending'", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Pending admin user not found")
        
        cursor.execute("UPDATE users SET status = 'approved' WHERE id = %s", (user_id,))
        db.commit()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        updated_user = cursor.fetchone()
        
        send_email(user["email"], "Admin Account Approved", f"Your admin account ({user['username']}) has been approved by the superadmin.")
        return User(**updated_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error approving user: {str(e)}")
    finally:
        cursor.close()

@app.patch("/api/superadmin/users/{user_id}/reject")
async def reject_user(user_id: int, reason: str, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'admin' AND status = 'pending'", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Pending admin user not found")
        
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()
        
        send_email(user["email"], "Admin Account Rejected", f"Your admin account ({user['username']}) was rejected: {reason}")
        return {"message": "Admin account rejected and deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error rejecting user: {str(e)}")
    finally:
        cursor.close()

# Guards
@app.get("/api/admin/guards", response_model=List[User])
async def list_guards(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE role = 'guard'")
    guards = cursor.fetchall()
    cursor.close()
    return [User(**g) for g in guards]

@app.post("/api/admin/guards", response_model=User)
async def create_guard(
    username: str,
    email: str,
    password: str,
    building_id: Optional[int],
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    return await create_user(
        UserCreateAdmin(
            username=username,
            email=email,
            password=password,
            role="guard",
            building_id=building_id
        ),
        current_user,
        db
    )

@app.patch("/api/admin/guards/{guard_id}/assign")
async def assign_guard(guard_id: int, building_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE users SET building_id = %s WHERE id = %s AND role = 'guard'", (building_id, guard_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Guard not found")
        db.commit()
        return {"message": "Guard assigned to building"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error assigning guard: {str(e)}")
    finally:
        cursor.close()

@app.patch("/api/admin/guards/{guard_id}/block")
async def block_guard(guard_id: int, block: bool, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE users SET building_id = NULL WHERE id = %s AND role = 'guard'", (guard_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Guard not found")
        db.commit()
        return {"message": f"Guard {'blocked' if block else 'unblocked'}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error blocking guard: {str(e)}")
    finally:
        cursor.close()

# Notifications
@app.get("/api/notifications", response_model=List[Notification])
async def list_notifications(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["resident", "guard"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM notifications WHERE user_id = %s", (current_user.id,))
    notifications = cursor.fetchall()
    cursor.close()
    return [Notification(**n) for n in notifications]

@app.patch("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["resident", "guard"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s", (notification_id, current_user.id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        db.commit()
        return {"message": "Notification marked as read"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating notification: {str(e)}")
    finally:
        cursor.close()

# Dues & Payments
@app.get("/api/admin/dues")
async def list_dues(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return {"dues": []}  # Placeholder

@app.patch("/api/admin/dues/{due_id}/paid")
async def mark_due_paid(due_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return {"message": "Due marked as paid"}  # Placeholder

# Audit Logs
@app.get("/api/admin/audit", response_model=List[Log])
async def list_audit_logs(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    query = "SELECT * FROM logs WHERE 1=1"
    params = []
    if date_from:
        query += " AND timestamp >= %s"
        params.append(date_from)
    if date_to:
        query += " AND timestamp <= %s"
        params.append(date_to)
    if user_id:
        query += " AND guard_id = %s"
        params.append(user_id)
    if action:
        query += " AND action = %s"
        params.append(action)
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    logs = cursor.fetchall()
    cursor.close()
    return [Log(**log) for log in logs]

# Settings
@app.get("/api/admin/settings")
async def get_settings(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return {
        "qr_expiry": "30 days",
        "ocr_enabled": True,
        "notification_templates": {
            "approval": "Your vehicle {license_plate} has been approved.",
            "rejection": "Your vehicle {license_plate} was rejected: {reason}"
        }
    }

@app.patch("/api/admin/settings")
async def update_settings(settings: dict, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return {"message": "Settings updated"}  # Placeholder

# Building / CCTV
@app.get("/api/admin/buildings", response_model=List[Building])
async def list_buildings(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM buildings")
    buildings = cursor.fetchall()
    cursor.close()
    return [Building(**b) for b in buildings]

@app.post("/api/admin/buildings", response_model=Building)
async def create_building(
    name: str,
    address: Optional[str],
    cctv_settings: Optional[dict],
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO buildings (name, address, cctv_settings, created_at)
            VALUES (%s, %s, %s, NOW())
            """,
            (name, address, json.dumps(cctv_settings) if cctv_settings else None)
        )
        db.commit()
        cursor.execute("SELECT * FROM buildings WHERE id = LAST_INSERT_ID()")
        new_building = cursor.fetchone()
        return Building(**new_building)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating building: {str(e)}")
    finally:
        cursor.close()

@app.patch("/api/admin/buildings/{building_id}", response_model=Building)
async def update_building(
    building_id: int,
    name: Optional[str],
    address: Optional[str],
    cctv_settings: Optional[dict],
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM buildings WHERE id = %s", (building_id,))
        building = cursor.fetchone()
        if not building:
            raise HTTPException(status_code=404, detail="Building not found")
        query = "UPDATE buildings SET "
        params = []
        if name:
            query += "name = %s, "
            params.append(name)
        if address:
            query += "address = %s, "
            params.append(address)
        if cctv_settings is not None:
            query += "cctv_settings = %s, "
            params.append(json.dumps(cctv_settings))
        query = query.rstrip(", ") + " WHERE id = %s"
        params.append(building_id)
        cursor.execute(query, params)
        db.commit()
        cursor.execute("SELECT * FROM buildings WHERE id = %s", (building_id,))
        updated_building = cursor.fetchone()
        return Building(**updated_building)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating building: {str(e)}")
    finally:
        cursor.close()

@app.delete("/api/admin/buildings/{building_id}")
async def delete_building(building_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM buildings WHERE id = %s", (building_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Building not found")
        db.commit()
        return {"message": "Building deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting building: {str(e)}")
    finally:
        cursor.close()

# Add these endpoints at the END of your file, before the main block

@app.post("/api/scan/plate", response_model=ScanResponse)
async def scan_license_plate(
    file: UploadFile = File(...),
    camera_snapshot_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Scan license plate from image and verify in database
    """
    if current_user.role != "guard":
        raise HTTPException(status_code=403, detail="Only guards can scan vehicles")
    
    if reader is None:
        return ScanResponse(
            success=False,
            error="OCR system not available. Please contact administrator."
        )
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        return ScanResponse(
            success=False,
            error="File must be an image (JPEG, PNG, etc.)"
        )
    
    file_path = None
    try:
        logger.info(f"Starting scan for user {current_user.username}")
        
        # Save uploaded file
        file_path = save_uploaded_file(file)
        
        # Process image to extract license plate
        license_plate = await process_license_plate_image(file_path)
        
        if not license_plate:
            return ScanResponse(
                success=False,
                error="Could not detect license plate in image. Please try again with a clearer image of the license plate."
            )
        
        # Verify license plate in database
        verification_result = await verify_license_plate_db(license_plate, db)
        
        # Log the scan
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO logs (license_plate, action, result, source, guard_id, snapshot_url, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                license_plate,
                "scan",
                verification_result["status"],
                verification_result["source"],
                current_user.id,
                camera_snapshot_url
            )
        )
        db.commit()
        cursor.close()
        
        logger.info(f"Scan completed successfully: {license_plate} - {verification_result['status']}")
        
        return ScanResponse(
            success=True,
            license_plate=license_plate,
            status=verification_result["status"],
            source=verification_result["source"],
            confidence=0.8,
            vehicle_details=verification_result["vehicle_details"]
        )
        
    except Exception as e:
        logger.error(f"Scan endpoint error: {str(e)}")
        return ScanResponse(
            success=False,
            error=f"Scan failed: {str(e)}"
        )
        
    finally:
        # Clean up uploaded file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("Temporary file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {str(e)}")

@app.post("/api/scan/quick")
async def quick_scan(
    license_plate: str = Query(..., description="Direct license plate input"),
    camera_snapshot_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Quick scan with direct license plate input (manual entry fallback)
    """
    if current_user.role != "guard":
        raise HTTPException(status_code=403, detail="Only guards can scan vehicles")
    
    try:
        # Clean the license plate input
        license_plate_clean = ''.join(c for c in license_plate.upper() if c.isalnum())
        
        if len(license_plate_clean) < 6:
            raise HTTPException(status_code=400, detail="Invalid license plate format")
        
        # Verify license plate in database
        verification_result = await verify_license_plate_db(license_plate_clean, db)
        
        # Log the scan
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO logs (license_plate, action, result, source, guard_id, snapshot_url, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                license_plate_clean,
                "manual_scan",
                verification_result["status"],
                verification_result["source"],
                current_user.id,
                camera_snapshot_url
            )
        )
        db.commit()
        cursor.close()
        
        return {
            "success": True,
            "license_plate": license_plate_clean,
            "status": verification_result["status"],
            "source": verification_result["source"],
            "vehicle_details": verification_result["vehicle_details"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick scan error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

