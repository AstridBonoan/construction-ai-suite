-- PostgreSQL Schema for Phase 23 Real-Time Alert Service
-- This schema provides persistent storage for construction site alerts
-- Last Updated: 2024

-- Create enum types for alert properties
CREATE TYPE alert_type AS ENUM (
    'sensor_anomaly',
    'sensor_offline',
    'low_battery',
    'equipment_failure',
    'safety_hazard',
    'weather_critical',
    'work_stoppable',
    'air_quality',
    'restricted_area_breach',
    'maintenance_urgent'
);

CREATE TYPE alert_severity AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE alert_escalation_level AS ENUM (
    'level_1',
    'level_2',
    'level_3',
    'level_4'
);

CREATE TYPE notification_channel AS ENUM (
    'sms',
    'email',
    'slack',
    'push',
    'monday_com',
    'dashboard'
);

-- Main alerts table
CREATE TABLE IF NOT EXISTS iot_alerts (
    alert_id UUID PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    alert_type alert_type NOT NULL,
    severity alert_severity NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    sensor_id VARCHAR(255),
    equipment_id VARCHAR(255),
    location VARCHAR(500),
    recommended_action TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    escalation_level alert_escalation_level NOT NULL DEFAULT 'level_1',
    notification_attempts INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_project_id (project_id),
    INDEX idx_created_at (created_at),
    INDEX idx_severity (severity),
    INDEX idx_alert_type (alert_type),
    INDEX idx_is_active (is_active),
    INDEX idx_project_active (project_id, is_active)
);

-- Alert notification history table
CREATE TABLE IF NOT EXISTS alert_notifications (
    notification_id UUID PRIMARY KEY,
    alert_id UUID NOT NULL REFERENCES iot_alerts(alert_id) ON DELETE CASCADE,
    channel notification_channel NOT NULL,
    recipient VARCHAR(500),
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50),
    error_message TEXT,
    INDEX idx_alert_id (alert_id),
    INDEX idx_sent_at (sent_at),
    INDEX idx_channel (channel)
);

-- Alert escalation history table
CREATE TABLE IF NOT EXISTS alert_escalations (
    escalation_id UUID PRIMARY KEY,
    alert_id UUID NOT NULL REFERENCES iot_alerts(alert_id) ON DELETE CASCADE,
    from_level alert_escalation_level NOT NULL,
    to_level alert_escalation_level NOT NULL,
    escalated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    escalation_reason VARCHAR(500),
    escalated_to_recipient VARCHAR(500),
    INDEX idx_alert_id (alert_id),
    INDEX idx_escalated_at (escalated_at)
);

-- Alert acknowledgment history table
CREATE TABLE IF NOT EXISTS alert_acknowledgments (
    acknowledgment_id UUID PRIMARY KEY,
    alert_id UUID NOT NULL REFERENCES iot_alerts(alert_id) ON DELETE CASCADE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    INDEX idx_alert_id (alert_id),
    INDEX idx_acknowledged_by (acknowledged_by)
);

-- Alert resolution history table
CREATE TABLE IF NOT EXISTS alert_resolutions (
    resolution_id UUID PRIMARY KEY,
    alert_id UUID NOT NULL REFERENCES iot_alerts(alert_id) ON DELETE CASCADE,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolution_notes TEXT,
    resolution_action VARCHAR(500),
    INDEX idx_alert_id (alert_id),
    INDEX idx_resolved_by (resolved_by)
);

-- Alert escalation rules configuration table
CREATE TABLE IF NOT EXISTS alert_escalation_rules (
    rule_id UUID PRIMARY KEY,
    severity alert_severity NOT NULL,
    escalation_level alert_escalation_level NOT NULL,
    timeout_minutes INTEGER NOT NULL,
    notification_channels notification_channel[] NOT NULL,
    recipient_role VARCHAR(100),
    recipient_contact VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(severity, escalation_level),
    INDEX idx_severity (severity)
);

-- Alert statistics view for dashboard
CREATE VIEW alert_statistics AS
SELECT
    project_id,
    alert_type,
    severity,
    escalation_level,
    COUNT(*) as total_count,
    SUM(CASE WHEN acknowledged_at IS NOT NULL THEN 1 ELSE 0 END) as acknowledged_count,
    SUM(CASE WHEN resolved_at IS NOT NULL THEN 1 ELSE 0 END) as resolved_count,
    MIN(created_at) as earliest_alert,
    MAX(created_at) as latest_alert
FROM iot_alerts
GROUP BY project_id, alert_type, severity, escalation_level;

-- Recent alerts view for quick access
CREATE VIEW recent_alerts AS
SELECT
    alert_id,
    project_id,
    alert_type,
    severity,
    title,
    created_at,
    escalation_level,
    is_active
FROM iot_alerts
WHERE is_active = TRUE
AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Escalation candidates view for scheduler
CREATE VIEW escalation_candidates AS
SELECT
    a.alert_id,
    a.project_id,
    a.alert_type,
    a.severity,
    a.escalation_level,
    a.created_at,
    a.notification_attempts,
    EXTRACT(EPOCH FROM (NOW() - a.created_at)) as age_seconds
FROM iot_alerts a
JOIN alert_escalation_rules ar ON
    a.severity = ar.severity AND
    a.escalation_level = ar.escalation_level
WHERE a.is_active = TRUE
AND a.resolved_at IS NULL
AND EXTRACT(EPOCH FROM (NOW() - a.created_at)) > ar.timeout_minutes * 60;

-- Daily alert summary view
CREATE VIEW daily_alert_summary AS
SELECT
    DATE(created_at) as alert_date,
    project_id,
    alert_type,
    severity,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM COALESCE(resolved_at, NOW()) - created_at)) as avg_resolution_time_seconds
FROM iot_alerts
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY DATE(created_at), project_id, alert_type, severity;

-- Create indexes for common queries
CREATE INDEX idx_alerts_project_severity ON iot_alerts(project_id, severity);
CREATE INDEX idx_alerts_project_active ON iot_alerts(project_id, is_active, created_at DESC);
CREATE INDEX idx_alerts_unresolved ON iot_alerts(project_id, resolved_at) WHERE resolved_at IS NULL;
CREATE INDEX idx_notifications_alert_channel ON alert_notifications(alert_id, channel);
CREATE INDEX idx_escalations_recent ON alert_escalations(escalated_at DESC);

-- Function to mark alerts as resolved with cleanup
CREATE OR REPLACE FUNCTION resolve_alert(p_alert_id UUID, p_resolved_by VARCHAR, p_notes TEXT)
RETURNS void AS $$
BEGIN
    UPDATE iot_alerts
    SET
        resolved_at = NOW(),
        is_active = FALSE
    WHERE alert_id = p_alert_id;
    
    INSERT INTO alert_resolutions (resolution_id, alert_id, resolved_by, resolution_notes)
    VALUES (
        gen_random_uuid(),
        p_alert_id,
        p_resolved_by,
        p_notes
    );
END;
$$ LANGUAGE plpgsql;

-- Function to escalate an alert
CREATE OR REPLACE FUNCTION escalate_alert(
    p_alert_id UUID,
    p_to_level alert_escalation_level,
    p_reason VARCHAR
)
RETURNS void AS $$
DECLARE
    v_current_level alert_escalation_level;
    v_escalation_to_contact VARCHAR(500);
BEGIN
    SELECT escalation_level INTO v_current_level FROM iot_alerts WHERE alert_id = p_alert_id;
    
    -- Soft increment escalation level
    UPDATE iot_alerts
    SET escalation_level = p_to_level
    WHERE alert_id = p_alert_id;
    
    -- Record escalation in history
    INSERT INTO alert_escalations (
        escalation_id,
        alert_id,
        from_level,
        to_level,
        escalation_reason
    )
    VALUES (
        gen_random_uuid(),
        p_alert_id,
        v_current_level,
        p_to_level,
        p_reason
    );
END;
$$ LANGUAGE plpgsql;

-- Function to record notification
CREATE OR REPLACE FUNCTION record_notification(
    p_alert_id UUID,
    p_channel notification_channel,
    p_recipient VARCHAR,
    p_status VARCHAR,
    p_error_message TEXT
)
RETURNS void AS $$
BEGIN
    INSERT INTO alert_notifications (
        notification_id,
        alert_id,
        channel,
        recipient,
        status,
        error_message
    )
    VALUES (
        gen_random_uuid(),
        p_alert_id,
        p_channel,
        p_recipient,
        p_status,
        p_error_message
    );
    
    -- Increment notification attempts
    UPDATE iot_alerts
    SET notification_attempts = notification_attempts + 1
    WHERE alert_id = p_alert_id;
END;
$$ LANGUAGE plpgsql;

-- Sample data: Insert default escalation rules
INSERT INTO alert_escalation_rules (
    rule_id,
    severity,
    escalation_level,
    timeout_minutes,
    notification_channels,
    recipient_role,
    recipient_contact
)
VALUES
    -- CRITICAL alerts escalate rapidly
    (gen_random_uuid(), 'critical', 'level_1', 1, '{"sms","slack","email"}', 'Site Engineer', 'site-engineer@company.com'),
    (gen_random_uuid(), 'critical', 'level_2', 5, '{"sms","slack","email","push"}', 'Safety Officer', 'safety-officer@company.com'),
    (gen_random_uuid(), 'critical', 'level_3', 10, '{"sms","slack","email","monday_com"}', 'Project Manager', 'pm@company.com'),
    (gen_random_uuid(), 'critical', 'level_4', 15, '{"sms","email"}', 'Operations Chief', 'ops-chief@company.com'),
    
    -- HIGH alerts escalate quickly
    (gen_random_uuid(), 'high', 'level_1', 5, '{"slack","email"}', 'Site Engineer', 'site-engineer@company.com'),
    (gen_random_uuid(), 'high', 'level_2', 15, '{"slack","email","sms"}', 'Safety Officer', 'safety-officer@company.com'),
    (gen_random_uuid(), 'high', 'level_3', 30, '{"slack","email","monday_com"}', 'Project Manager', 'pm@company.com'),
    (gen_random_uuid(), 'high', 'level_4', 60, '{"email"}', 'Operations Chief', 'ops-chief@company.com'),
    
    -- MEDIUM alerts escalate slower
    (gen_random_uuid(), 'medium', 'level_1', 15, '{"slack"}', 'Site Engineer', 'site-engineer@company.com'),
    (gen_random_uuid(), 'medium', 'level_2', 30, '{"slack","email"}', 'Safety Officer', 'safety-officer@company.com'),
    (gen_random_uuid(), 'medium', 'level_3', 60, '{"slack","email"}', 'Project Manager', 'pm@company.com'),
    (gen_random_uuid(), 'medium', 'level_4', 120, '{"email"}', 'Operations Chief', 'ops-chief@company.com'),
    
    -- LOW alerts escalate very slowly
    (gen_random_uuid(), 'low', 'level_1', 30, '{"slack"}', 'Site Engineer', 'site-engineer@company.com'),
    (gen_random_uuid(), 'low', 'level_2', 60, '{"slack","email"}', 'Supervisor', 'supervisor@company.com'),
    (gen_random_uuid(), 'low', 'level_3', 120, '{"email"}', 'Project Manager', 'pm@company.com'),
    (gen_random_uuid(), 'low', 'level_4', 240, '{"email"}', 'Operations Chief', 'ops-chief@company.com')
ON CONFLICT DO NOTHING;

-- Create trigger to update timestamp
CREATE OR REPLACE FUNCTION update_alert_escalation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE alert_escalation_rules
    SET updated_at = CURRENT_TIMESTAMP
    WHERE rule_id = NEW.rule_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER alert_escalation_rules_timestamp
BEFORE UPDATE ON alert_escalation_rules
FOR EACH ROW
EXECUTE FUNCTION update_alert_escalation_timestamp();

-- Create materialized view for performance (if needed)
CREATE MATERIALIZED VIEW alert_performance_metrics AS
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    project_id,
    severity,
    COUNT(*) as alerts_created,
    AVG(EXTRACT(EPOCH FROM COALESCE(resolved_at, NOW()) - created_at)) as avg_resolution_seconds,
    MAX(EXTRACT(EPOCH FROM COALESCE(resolved_at, NOW()) - created_at)) as max_resolution_seconds,
    MIN(EXTRACT(EPOCH FROM COALESCE(resolved_at, NOW()) - created_at)) as min_resolution_seconds
FROM iot_alerts
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('hour', created_at), project_id, severity;

-- Index for materialized view performance
CREATE INDEX idx_alert_performance_hour_project ON alert_performance_metrics(hour, project_id);

-- Grants for application user (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON iot_alerts TO app_user;
-- GRANT SELECT, INSERT ON alert_notifications TO app_user;
-- GRANT SELECT, INSERT ON alert_escalations TO app_user;
-- GRANT SELECT, INSERT ON alert_acknowledgments TO app_user;
-- GRANT SELECT, INSERT ON alert_resolutions TO app_user;
-- GRANT SELECT ON alert_escalation_rules TO app_user;
-- GRANT SELECT ON alert_statistics TO app_user;
-- GRANT SELECT ON recent_alerts TO app_user;
-- GRANT SELECT ON escalation_candidates TO app_user;
-- GRANT SELECT ON daily_alert_summary TO app_user;

-- Migration notes:
-- This schema is designed to work with the Phase 23 Alert Service
-- The in-memory AlertStore can be migrated to use these tables by:
-- 1. Modifying AlertStore to use SQLAlchemy ORM models
-- 2. Replacing dictionary operations with database queries
-- 3. Using connection pooling for better performance
-- 4. Implementing proper transaction handling
--
-- Performance considerations:
-- - Indexes are created on commonly queried columns
-- - Materialized views provide pre-computed aggregations
-- - Partitioning by project_id recommended for very large datasets
-- - Archive old alerts (>90 days) to separate tables for performance
