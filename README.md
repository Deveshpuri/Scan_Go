-- MySQL Database Schema for Vehicle Access App (Updated)

-- Societies Table: Stores top-level residential complexes/societies (e.g., Agrawal Paramount)
CREATE TABLE societies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Buildings Table: Stores buildings within a society (e.g., Tower 1, Wing A)
CREATE TABLE buildings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    society_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,  -- e.g., Tower 1
    building_number VARCHAR(50),  -- e.g., Building 1
    wing VARCHAR(50),  -- e.g., A, B
    address TEXT,
    cctv_settings JSON,  -- JSON for CCTV URLs, configs, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE
);

-- Users Table: Stores users with roles (resident, admin, guard, superadmin)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('resident', 'admin', 'guard', 'superadmin') NOT NULL,
    building_id INT,  -- Nullable for superadmin
    flat_number VARCHAR(50),  -- e.g., 101
    phone_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL
);

-- Vehicles Table: Stores vehicle registrations (replaced 'make' with 'chassis_number')
CREATE TABLE vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    license_plate VARCHAR(50) UNIQUE NOT NULL,
    chassis_number VARCHAR(100),  -- Replaced 'make'
    model VARCHAR(100),
    color VARCHAR(50),
    owner_id INT NOT NULL,  -- Resident user_id
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    approved_by INT,  -- Admin user_id
    approved_at TIMESTAMP,
    rejected_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Logs Table: Immutable audit logs for scans, entries, exits, verifications (already includes scanned by who/when/vehicle/number)
CREATE TABLE logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT,
    license_plate VARCHAR(50),  -- For cases where vehicle not found
    action ENUM('scan', 'verification', 'entry', 'exit', 'manual_entry') NOT NULL,
    result ENUM('registered', 'not_found', 'pending') NOT NULL,
    source ENUM('google_sheet', 'mysql', 'not_found') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guard_id INT NOT NULL,  -- Who scanned/verified
    notes TEXT,
    snapshot_url VARCHAR(255),  -- Optional S3 link to image snapshot
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL,
    FOREIGN KEY (guard_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Unregistered Vehicles Table: For visitor/delivery vehicles (e.g., Zepto delivery)
CREATE TABLE unregistered_vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    license_plate VARCHAR(50) NOT NULL,
    visitor_name VARCHAR(255),
    visitor_email VARCHAR(255),
    visited_user_id INT,  -- Resident being visited
    purpose TEXT,  -- e.g., Delivery to flat X
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guard_id INT NOT NULL,
    notes TEXT,
    snapshot_url VARCHAR(255),  -- Optional S3 link
    FOREIGN KEY (visited_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (guard_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Notifications Table: Stores notifications for push/email (optional, can be queued)
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('approval', 'rejection', 'suspicious_activity') NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_vehicles_license_plate ON vehicles(license_plate);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_vehicle_id ON logs(vehicle_id);
CREATE INDEX idx_logs_guard_id ON logs(guard_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_building_id ON users(building_id);
CREATE INDEX idx_unregistered_vehicles_license_plate ON unregistered_vehicles(license_plate);
CREATE INDEX idx_unregistered_vehicles_timestamp ON unregistered_vehicles(timestamp);
CREATE INDEX idx_unregistered_vehicles_guard_id ON unregistered_vehicles(guard_id);