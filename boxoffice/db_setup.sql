-- Database Setup Script
-- Run this script in MySQL Workbench to initialize the database and user.

-- 1. Create the database
CREATE DATABASE IF NOT EXISTS boxoffice_db;
USE boxoffice_db;

-- 2. Create the user 'boxoffice_user' with password 'boxoffice_pass'
-- Checks if user exists first to avoid errors (MariaDB/MySQL 5.7+ compatible syntax)
CREATE USER IF NOT EXISTS 'boxoffice_user'@'localhost' IDENTIFIED BY 'boxoffice_pass';

-- 3. Grant privileges to the user
GRANT ALL PRIVILEGES ON boxoffice_db.* TO 'boxoffice_user'@'localhost';
FLUSH PRIVILEGES;

-- 4. Create Tables (Initial Schema)

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL
);

-- Movies Table
CREATE TABLE IF NOT EXISTS movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    genre VARCHAR(255) NOT NULL,
    duration INT NOT NULL
);

-- Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    movie_title VARCHAR(255) NOT NULL,
    booking_date DATE NOT NULL,
    tickets INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- 5. Seed Initial Data
INSERT IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin');
INSERT IGNORE INTO users (username, password, role) VALUES ('tech', 'tech123', 'Tech Admin');
INSERT IGNORE INTO users (username, password, role) VALUES ('user', 'user123', 'Customer');

SELECT "Database setup completed successfully!" AS Status;
