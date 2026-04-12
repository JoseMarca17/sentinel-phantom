# Este archivo define lo que se guardará para el análisis de vulnerabilidades [cite: 18]
# Ayuda a generar la relación entre hardware abierto y optimización de detección [cite: 139]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rfid_captures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    uid TEXT NOT NULL,
    card_type TEXT,
    success_clone BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    module TEXT,
    level TEXT,
    description TEXT
);
"""