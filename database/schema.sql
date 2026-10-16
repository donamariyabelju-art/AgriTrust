-- AgriTrust MySQL Database Schema
-- Version: 1.0.0
-- Charset: utf8mb4

CREATE DATABASE IF NOT EXISTS agritrust_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE agritrust_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'FARMER',
    full_name VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    location VARCHAR(150),
    bio TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Farms Table
CREATE TABLE IF NOT EXISTS farms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    location VARCHAR(200) NOT NULL,
    land_area FLOAT NOT NULL,
    soil_type VARCHAR(80) NOT NULL,
    irrigation_method VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_farm_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Crops Table
CREATE TABLE IF NOT EXISTS crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    farm_id INT NULL,
    crop_name VARCHAR(100) NOT NULL,
    planting_date DATE NOT NULL,
    growth_stage VARCHAR(80) NOT NULL DEFAULT 'Vegetative',
    growth_percentage INT NOT NULL DEFAULT 10,
    expected_harvest_date DATE NOT NULL,
    expected_yield FLOAT NOT NULL,
    production_cost FLOAT NOT NULL DEFAULT 0.0,
    expected_revenue FLOAT NOT NULL DEFAULT 0.0,
    health_status VARCHAR(50) NOT NULL DEFAULT 'Healthy',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE SET NULL,
    INDEX idx_crop_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Products Table (Direct Marketplace)
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    crop_id INT NULL,
    batch_id INT NULL,
    title VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL DEFAULT 'Vegetables',
    quantity FLOAT NOT NULL,
    initial_quantity FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL DEFAULT 'kg',
    price_per_unit FLOAT NOT NULL,
    location VARCHAR(150) NOT NULL,
    harvest_date DATE NOT NULL,
    image_url VARCHAR(255),
    quality_grade VARCHAR(50) NOT NULL DEFAULT 'Grade A',
    description TEXT,
    availability_status VARCHAR(30) NOT NULL DEFAULT 'Available',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (crop_id) REFERENCES crops(id) ON DELETE SET NULL,
    INDEX idx_product_category (category),
    INDEX idx_product_status (availability_status),
    INDEX idx_product_batch (batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    buyer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity FLOAT NOT NULL,
    unit_price FLOAT NOT NULL,
    total_amount FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending Payment',
    payment_status VARCHAR(80) NOT NULL DEFAULT 'Pending Payment (Pay on Delivery / Demo)',
    delivery_address TEXT NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_order_buyer (buyer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Future Harvests Table
CREATE TABLE IF NOT EXISTS future_harvests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    crop_name VARCHAR(100) NOT NULL,
    expected_harvest_date DATE NOT NULL,
    expected_quantity FLOAT NOT NULL,
    reserved_quantity FLOAT NOT NULL DEFAULT 0.0,
    target_price_per_kg FLOAT NOT NULL,
    location VARCHAR(150) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Open for Reservation',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_harvest_farmer (farmer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Reservations Table
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    future_harvest_id INT NULL,
    farmer_id INT NOT NULL,
    crop_name VARCHAR(100) NOT NULL,
    reserved_quantity FLOAT NOT NULL,
    unit_price FLOAT NOT NULL,
    total_estimated_amount FLOAT NOT NULL,
    expected_harvest_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Confirmed',
    contact_phone VARCHAR(20),
    delivery_address TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (future_harvest_id) REFERENCES future_harvests(id) ON DELETE SET NULL,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_reservation_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Harvest Batches & Traceability
CREATE TABLE IF NOT EXISTS harvest_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_code VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    farm_id INT NULL,
    crop_id INT NULL,
    crop_name VARCHAR(100) NOT NULL,
    category VARCHAR(80) NOT NULL DEFAULT 'Vegetables',
    description TEXT,
    location VARCHAR(150),
    harvest_date DATE NOT NULL,
    quantity FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL DEFAULT 'kg',
    asking_price FLOAT DEFAULT 0.0,
    image_url VARCHAR(255),
    document_url VARCHAR(255),
    document_name VARCHAR(150),
    verification_stage VARCHAR(50) NOT NULL DEFAULT 'Submitted',
    verification_status VARCHAR(50) NOT NULL DEFAULT 'Registered',
    is_independently_verified BOOLEAN DEFAULT FALSE,
    verifier_name VARCHAR(120),
    verification_date DATE,
    quality_grade VARCHAR(50) NOT NULL DEFAULT 'Grade A',
    quality_score INT NOT NULL DEFAULT 90,
    admin_feedback TEXT,
    internal_notes TEXT,
    review_reason TEXT,
    reviewed_by_id INT NULL,
    reviewed_at DATETIME NULL,
    journey_stage VARCHAR(50) NOT NULL DEFAULT 'Harvested',
    storage_conditions VARCHAR(150) DEFAULT 'Cool Dry Warehouse (18°C)',
    packaging_date DATE,
    dispatch_date DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE SET NULL,
    FOREIGN KEY (crop_id) REFERENCES crops(id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_batch_code (batch_code),
    INDEX idx_batch_stage (verification_stage)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8b. Batch Verification Stage History & Audit Logs
CREATE TABLE IF NOT EXISTS batch_verification_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    previous_stage VARCHAR(50) NULL,
    new_stage VARCHAR(50) NOT NULL,
    action_by_id INT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    comments TEXT NULL,
    internal_notes TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES harvest_batches(id) ON DELETE CASCADE,
    FOREIGN KEY (action_by_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_log_batch (batch_id),
    INDEX idx_log_actor (action_by_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Buyer Demands Table
CREATE TABLE IF NOT EXISTS buyer_demands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    buyer_id INT NOT NULL,
    crop_name VARCHAR(100) NOT NULL,
    required_quantity FLOAT NOT NULL,
    available_supply FLOAT NOT NULL DEFAULT 0.0,
    unit VARCHAR(20) NOT NULL DEFAULT 'kg',
    location VARCHAR(150) NOT NULL,
    demand_level VARCHAR(30) NOT NULL DEFAULT 'High',
    target_price FLOAT NULL,
    required_date DATE NOT NULL,
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'Active',
    is_sample_data BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_demand_crop (crop_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Crop Health Scans Table
CREATE TABLE IF NOT EXISTS crop_health_scans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    crop_name VARCHAR(100) NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    detected_disease VARCHAR(150) NOT NULL,
    confidence_score FLOAT NOT NULL,
    health_status VARCHAR(50) NOT NULL,
    symptoms TEXT,
    possible_causes TEXT,
    preventive_measures TEXT,
    recommended_steps TEXT,
    is_demo_mode BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_scan_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NULL,
    buyer_id INT NOT NULL,
    farmer_id INT NOT NULL,
    rating INT NOT NULL DEFAULT 5,
    comment TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
