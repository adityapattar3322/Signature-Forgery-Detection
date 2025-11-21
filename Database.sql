-- Create a new database for your application
CREATE DATABASE signature_app_db;

-- Switch to the newly created database
USE signature_app_db;

-- Create a table to store user credentials
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);