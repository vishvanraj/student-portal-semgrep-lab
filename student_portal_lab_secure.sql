-- Reference secure MySQL schema for student portal lab
CREATE DATABASE IF NOT EXISTS student_portal_lab_secure;
USE student_portal_lab_secure;

DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(30) DEFAULT NULL
);

CREATE TABLE assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_code VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_assignment_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_user_id INT NOT NULL,
    recipient_username VARCHAR(50) NOT NULL,
    message_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_message_sender FOREIGN KEY (sender_user_id) REFERENCES users(id)
);

-- Passwords below correspond to:
-- student1 / password123
-- student2 / password123
-- lecturer1 / password123
-- admin1 / admin123
INSERT INTO users (username, password_hash, role, full_name, email, phone) VALUES
('student1', 'scrypt:32768:8:1$YOVZ6NCSHMHnPJ6z$bb6ca0f8d1702c51417145abd8f23d07d82e14c7299bbf6523a0651c7ef2f72af8dfe95d5d4dd20535524c2e4d59845dddcc1323e1f98cbe4fb5e74f46b263aa', 'student', 'Ali Student', 'ali@student.edu', '0123456789'),
('student2', 'scrypt:32768:8:1$ohYoUda3oPKqy9IN$d66f83c6ec5f845011a167bfedce71f32029fa58cfe4e480deeff8c3f302dce4df0ad67112917d31475c53459a7b5dce18b54e97ac4b46ed793ff9dd6198f314', 'student', 'Siti Student', 'siti@student.edu', '0198765432'),
('lecturer1', 'scrypt:32768:8:1$8T0U4vQYklmPk76P$df9be19a9d524af615653e1ae6d44e900a1d841f679f85a4e5991d739662c4a95a617239c98b47ca299864e0fa934f4c22bcde861d6cde8ea1f63a4ad4bc1580', 'lecturer', 'Dr Kumar', 'kumar@university.edu', '0111111111'),
('admin1', 'scrypt:32768:8:1$CRnXhRbJBrL37vhm$4654442c3862eb32254c715ca26b433df6f73059b91551d8887fdb2570fd9e17aa6f17b5780cb61a6f2a5d3635da738eb947cf8c2992692d79070931cd4efef1', 'admin', 'System Admin', 'admin@university.edu', '0100000000');

INSERT INTO messages (sender_user_id, recipient_username, message_text) VALUES
(1, 'lecturer1', 'Hello doctor, I submitted my assignment.'),
(3, 'student1', 'Received. Please review the feedback next week.');

INSERT INTO assignments (user_id, course_code, title, original_filename, stored_filename) VALUES
(1, 'SEC401', 'Threat Modeling Lab', 'lab3_report.pdf', '8bb9a3f93e2f4b6897a5737e8e2ed001.pdf');
