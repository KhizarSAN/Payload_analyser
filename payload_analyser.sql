-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des patterns enrichie
CREATE TABLE IF NOT EXISTS patterns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    resume VARCHAR(255),
    description TEXT,
    categorie VARCHAR(100),
    criticite VARCHAR(50),
    regex TEXT,
    exemple_payload TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Table des analyses très riche
CREATE TABLE IF NOT EXISTS analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payload TEXT NOT NULL,
    pattern_id INT,
    pattern_nom VARCHAR(100),
    resume_court VARCHAR(255),
    description_faits TEXT,
    analyse_technique TEXT,
    resultat TEXT,
    justification TEXT,
    rapport_complet TEXT,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    tags VARCHAR(255),
    statut VARCHAR(50) DEFAULT 'nouveau',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (pattern_id) REFERENCES patterns(id)
);

-- Table des logs détaillée
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Utilisateur admin (hash à remplacer par le tien si besoin)
INSERT INTO users (username, password_hash, email, role)
VALUES (
  'khz',
  'scrypt:32768:8:1$DbF2WVM90FcC9oNf$cdabd82b75ca118e4969512d140ce444aa2ec66f92b8783b5e7a3bca537c34daef58486657e1b69771f03848fd993a2a7f5c11080a04adbc23bd8acc8dc4bb86',
  'khz@admin.local',
  'admin'
)
ON DUPLICATE KEY UPDATE username=username;