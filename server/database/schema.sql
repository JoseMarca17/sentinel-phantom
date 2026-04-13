-- ╔══════════════════════════════════════════════════════════════╗
-- ║  SENTINEL PHANTOM — SQL Server Schema (Laptop del equipo)   ║
-- ║  Escuela Militar de Ingeniería (EMI) — Open House 2026      ║
-- ╚══════════════════════════════════════════════════════════════╝
-- Ejecutar una vez para crear la base de datos central.
-- Compatible con SQL Server 2017+

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'SentinelPhantom')
BEGIN
    CREATE DATABASE SentinelPhantom
        COLLATE Latin1_General_CI_AS;
    PRINT 'Base de datos SentinelPhantom creada.';
END
GO

USE SentinelPhantom;
GO

-- ── Sesiones ──────────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='sessions' AND xtype='U')
CREATE TABLE sessions (
    id          NVARCHAR(36)  NOT NULL PRIMARY KEY,
    device_id   NVARCHAR(64)  NOT NULL,
    started_at  DATETIME2     NOT NULL,
    ended_at    DATETIME2     NULL,
    notes       NVARCHAR(500) NULL,
    synced_at   DATETIME2     DEFAULT GETUTCDATE(),
    created_at  DATETIME2     DEFAULT GETUTCDATE()
);
GO

-- ── Dispositivos detectados ───────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='devices' AND xtype='U')
CREATE TABLE devices (
    id            NVARCHAR(64)   NOT NULL PRIMARY KEY,
    session_id    NVARCHAR(36)   NULL REFERENCES sessions(id),
    first_seen    DATETIME2      NOT NULL,
    last_seen     DATETIME2      NOT NULL,
    device_type   NVARCHAR(32)   NOT NULL,
    mac           NVARCHAR(17)   NULL,
    vendor        NVARCHAR(128)  NULL,
    ssid          NVARCHAR(256)  NULL,
    signal_dbm    INT            NULL,
    extra         NVARCHAR(MAX)  NULL,
    threat_level  NVARCHAR(16)   DEFAULT 'INFO',
    synced_at     DATETIME2      DEFAULT GETUTCDATE()
);
GO

-- ── Eventos (log táctico) ─────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='events' AND xtype='U')
CREATE TABLE events (
    id          BIGINT         NOT NULL,  -- ID original de la Pi
    session_id  NVARCHAR(36)   NULL REFERENCES sessions(id),
    timestamp   DATETIME2      NOT NULL,
    module      NVARCHAR(32)   NOT NULL,
    event_type  NVARCHAR(64)   NOT NULL,
    payload     NVARCHAR(MAX)  NULL,
    synced_at   DATETIME2      DEFAULT GETUTCDATE(),
    PRIMARY KEY (id, session_id)
);
GO

-- ── Alertas de seguridad ──────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='alerts' AND xtype='U')
CREATE TABLE alerts (
    id            BIGINT         NOT NULL,
    session_id    NVARCHAR(36)   NULL REFERENCES sessions(id),
    timestamp     DATETIME2      NOT NULL,
    module        NVARCHAR(32)   NOT NULL,
    alert_type    NVARCHAR(64)   NOT NULL,
    severity      NVARCHAR(16)   NOT NULL,
    description   NVARCHAR(1000) NOT NULL,
    device_mac    NVARCHAR(17)   NULL,
    extra         NVARCHAR(MAX)  NULL,
    acknowledged  BIT            DEFAULT 0,
    synced_at     DATETIME2      DEFAULT GETUTCDATE(),
    PRIMARY KEY (id, session_id)
);
GO

-- ── Índices ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_events_module    ON events(module);
CREATE INDEX IF NOT EXISTS idx_events_ts        ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_severity  ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_ts        ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_devices_mac      ON devices(mac);
CREATE INDEX IF NOT EXISTS idx_devices_type     ON devices(device_type);
GO