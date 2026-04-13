-- ╔══════════════════════════════════════════════════════════════╗
-- ║  SENTINEL PHANTOM — Vistas SQL Server (reportes forenses)   ║
-- ╚══════════════════════════════════════════════════════════════╝

USE SentinelPhantom;
GO

-- ── 1. Resumen diario de actividad ────────────────────────────────────────────
CREATE OR ALTER VIEW vw_daily_summary AS
SELECT
    CAST(e.timestamp AS DATE)               AS fecha,
    e.module,
    COUNT(*)                                AS total_eventos,
    COUNT(DISTINCT e.session_id)            AS sesiones_activas
FROM events e
GROUP BY CAST(e.timestamp AS DATE), e.module;
GO

-- ── 2. Top amenazas (últimas 24h) ─────────────────────────────────────────────
CREATE OR ALTER VIEW vw_top_threats AS
SELECT TOP 50
    a.alert_type,
    a.module,
    a.severity,
    COUNT(*)                                AS ocurrencias,
    MAX(a.timestamp)                        AS ultima_vez,
    a.device_mac
FROM alerts a
WHERE a.timestamp >= DATEADD(HOUR, -24, GETUTCDATE())
GROUP BY a.alert_type, a.module, a.severity, a.device_mac
ORDER BY ocurrencias DESC;
GO

-- ── 3. Dispositivos por sesión ────────────────────────────────────────────────
CREATE OR ALTER VIEW vw_session_devices AS
SELECT
    s.id                                    AS session_id,
    s.device_id,
    s.started_at,
    s.ended_at,
    DATEDIFF(MINUTE, s.started_at,
        ISNULL(s.ended_at, GETUTCDATE()))   AS duracion_minutos,
    COUNT(DISTINCT d.id)                    AS total_dispositivos,
    COUNT(DISTINCT CASE WHEN d.threat_level IN ('HIGH','CRITICAL')
          THEN d.id END)                    AS dispositivos_criticos,
    COUNT(DISTINCT al.id)                   AS total_alertas
FROM sessions s
LEFT JOIN devices d  ON d.session_id = s.id
LEFT JOIN alerts  al ON al.session_id = s.id
GROUP BY s.id, s.device_id, s.started_at, s.ended_at;
GO

-- ── 4. Timeline de alertas críticas ──────────────────────────────────────────
CREATE OR ALTER VIEW vw_critical_timeline AS
SELECT
    a.id,
    a.timestamp,
    a.module,
    a.alert_type,
    a.severity,
    a.description,
    a.device_mac,
    d.vendor                                AS device_vendor,
    d.ssid                                  AS device_ssid,
    s.device_id
FROM alerts a
LEFT JOIN sessions s ON s.id = a.session_id
LEFT JOIN devices  d ON d.mac = a.device_mac AND d.session_id = a.session_id
WHERE a.severity IN ('HIGH', 'CRITICAL')
-- ORDER BY a.timestamp DESC  -- usar al consultar la vista
;
GO

-- ── 5. Estadísticas por módulo ────────────────────────────────────────────────
CREATE OR ALTER VIEW vw_module_stats AS
SELECT
    e.module,
    COUNT(*)                                AS total_eventos,
    COUNT(DISTINCT e.session_id)            AS sesiones,
    MIN(e.timestamp)                        AS primer_evento,
    MAX(e.timestamp)                        AS ultimo_evento,
    (SELECT COUNT(*) FROM alerts a
     WHERE a.module = e.module)             AS total_alertas
FROM events e
GROUP BY e.module;
GO