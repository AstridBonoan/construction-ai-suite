"""
Real-Time Alert Service for Phase 23 IoT
Manages alert storage, escalation, and notifications
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    SENSOR_ANOMALY = "sensor_anomaly"
    SENSOR_OFFLINE = "sensor_offline"
    LOW_BATTERY = "low_battery"
    EQUIPMENT_FAILURE = "equipment_failure"
    SAFETY_HAZARD = "safety_hazard"
    WEATHER_CRITICAL = "weather_critical"
    WORK_STOPPABLE = "work_stoppable"
    AIR_QUALITY = "air_quality"
    RESTRICTION_BREACH = "restriction_breach"
    MAINTENANCE_URGENT = "maintenance_urgent"


class NotificationChannel(Enum):
    """Notification delivery channels"""
    SMS = "sms"
    EMAIL = "email"
    SLACK = "slack"
    PUSH_NOTIFICATION = "push_notification"
    MONDAY_COM = "monday_com"
    DASHBOARD = "dashboard"


class AlertEscalationLevel(Enum):
    """Escalation levels"""
    LEVEL_1 = "level_1"  # Site Engineer
    LEVEL_2 = "level_2"  # Safety Officer
    LEVEL_3 = "level_3"  # Project Manager
    LEVEL_4 = "level_4"  # Emergency Services


class Alert:
    """Alert data structure"""

    def __init__(
        self,
        alert_id: str,
        project_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        sensor_id: Optional[str] = None,
        equipment_id: Optional[str] = None,
        location: Optional[str] = None,
        recommended_action: Optional[str] = None,
    ):
        self.alert_id = alert_id
        self.project_id = project_id
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.description = description
        self.sensor_id = sensor_id
        self.equipment_id = equipment_id
        self.location = location
        self.recommended_action = recommended_action
        self.created_at = datetime.now()
        self.acknowledged_at: Optional[datetime] = None
        self.acknowledged_by: Optional[str] = None
        self.resolved_at: Optional[datetime] = None
        self.escalation_level = AlertEscalationLevel.LEVEL_1
        self.escalation_time = 300  # 5 minutes
        self.last_escalated_at: Optional[datetime] = None
        self.notification_attempts = 0
        self.max_notification_attempts = 3

    def to_dict(self) -> Dict:
        """Convert alert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'project_id': self.project_id,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'sensor_id': self.sensor_id,
            'equipment_id': self.equipment_id,
            'location': self.location,
            'recommended_action': self.recommended_action,
            'created_at': self.created_at.isoformat(),
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'escalation_level': self.escalation_level.value,
            'notification_attempts': self.notification_attempts,
            'is_acknowledged': self.acknowledged_at is not None,
            'is_resolved': self.resolved_at is not None,
        }


class AlertStore:
    """In-memory alert storage (production would use database)"""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.escalation_queue: List[Alert] = []

    def store_alert(self, alert: Alert) -> bool:
        """Store alert"""
        self.alerts[alert.alert_id] = alert
        logger.info(f"Alert stored: {alert.alert_id} ({alert.severity.value})")
        return True

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        return self.alerts.get(alert_id)

    def get_project_alerts(
        self, project_id: str, unacknowledged_only: bool = False
    ) -> List[Alert]:
        """Get all alerts for project"""
        alerts = [a for a in self.alerts.values() if a.project_id == project_id]
        if unacknowledged_only:
            alerts = [a for a in alerts if a.acknowledged_at is None]
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge alert"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.acknowledged_at = datetime.now()
        alert.acknowledged_by = acknowledged_by
        logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
        return True

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark alert as resolved"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.resolved_at = datetime.now()
        logger.info(f"Alert resolved: {alert_id}")
        return True

    def get_escalation_candidates(self) -> List[Alert]:
        """Get alerts pending escalation"""
        candidates = []
        now = datetime.now()

        for alert in self.alerts.values():
            # Skip acknowledged and resolved
            if alert.acknowledged_at or alert.resolved_at:
                continue

            # Check if time exceeded for escalation
            time_since_created = (now - alert.created_at).total_seconds()
            if time_since_created > alert.escalation_time:
                # Check if already escalated
                if alert.last_escalated_at:
                    time_since_escalated = (now - alert.last_escalated_at).total_seconds()
                    if time_since_escalated > alert.escalation_time:
                        candidates.append(alert)
                else:
                    candidates.append(alert)

        return candidates

    def clear_project_alerts(self, project_id: str) -> int:
        """Clear all alerts for project"""
        alerts_to_remove = [a for a in self.alerts.values() if a.project_id == project_id]
        count = len(alerts_to_remove)
        for alert in alerts_to_remove:
            del self.alerts[alert.alert_id]
        return count


class NotificationService:
    """Service for sending notifications"""

    def __init__(self):
        self.notification_log: List[Dict] = []

    def send_notification(
        self,
        alert: Alert,
        channels: List[NotificationChannel],
        recipient: Optional[str] = None,
    ) -> bool:
        """Send notification through specified channels"""
        success = True

        for channel in channels:
            try:
                if channel == NotificationChannel.SMS:
                    self._send_sms(alert, recipient)
                elif channel == NotificationChannel.EMAIL:
                    self._send_email(alert, recipient)
                elif channel == NotificationChannel.SLACK:
                    self._send_slack(alert)
                elif channel == NotificationChannel.PUSH_NOTIFICATION:
                    self._send_push(alert, recipient)
                elif channel == NotificationChannel.MONDAY_COM:
                    self._send_monday_com(alert)
                elif channel == NotificationChannel.DASHBOARD:
                    self._send_dashboard(alert)

                alert.notification_attempts += 1
                self._log_notification(alert, channel, "success")
            except Exception as e:
                logger.error(f"Failed to send {channel.value} for alert {alert.alert_id}: {str(e)}")
                self._log_notification(alert, channel, "failed")
                success = False

        return success

    def _send_sms(self, alert: Alert, recipient: Optional[str]) -> None:
        """Send SMS notification (Twilio integration)"""
        if not recipient:
            logger.warning("SMS recipient not provided")
            return

        message = f"[{alert.severity.value.upper()}] {alert.title}\n{alert.description}"
        logger.info(f"SMS notification queued to {recipient}: {message}")
        # In production: twilio_client.messages.create(to=recipient, from_=FROM_NUMBER, body=message)

    def _send_email(self, alert: Alert, recipient: Optional[str]) -> None:
        """Send email notification (SendGrid integration)"""
        if not recipient:
            logger.warning("Email recipient not provided")
            return

        subject = f"[{alert.severity.value.upper()}] {alert.title}"
        body = f"""
Alert: {alert.title}
Description: {alert.description}
Severity: {alert.severity.value}
Location: {alert.location or 'Unknown'}
Recommended Action: {alert.recommended_action or 'None'}
Time: {alert.created_at.isoformat()}
        """
        logger.info(f"Email notification queued to {recipient}")
        # In production: sendgrid.send(Email(recipient), subject, body)

    def _send_slack(self, alert: Alert) -> None:
        """Send Slack notification"""
        color_map = {
            AlertSeverity.LOW: "#36a64f",  # Green
            AlertSeverity.MEDIUM: "#ffd700",  # Yellow
            AlertSeverity.HIGH: "#ff8c00",  # Orange
            AlertSeverity.CRITICAL: "#ff0000",  # Red
        }

        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#cccccc"),
                    "title": alert.title,
                    "text": alert.description,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Type", "value": alert.alert_type.value, "short": True},
                        {"title": "Project", "value": alert.project_id, "short": True},
                        {"title": "Location", "value": alert.location or "Unknown", "short": True},
                        {
                            "title": "Recommended Action",
                            "value": alert.recommended_action or "Contact site supervisor",
                        },
                    ],
                    "ts": int(alert.created_at.timestamp()),
                }
            ]
        }
        logger.info(f"Slack notification queued: {json.dumps(payload)}")
        # In production: requests.post(SLACK_WEBHOOK_URL, json=payload)

    def _send_push(self, alert: Alert, recipient: Optional[str]) -> None:
        """Send push notification to mobile app"""
        logger.info(f"Push notification queued for recipient: {recipient or 'all'}")
        # In production: firebase.send_multicast(message, tokens)

    def _send_monday_com(self, alert: Alert) -> None:
        """Update monday.com board with alert"""
        logger.info(f"Monday.com update queued for alert {alert.alert_id}")
        # In production: monday_client.update_board_item(project_id, alert_data)

    def _send_dashboard(self, alert: Alert) -> None:
        """Display on real-time dashboard"""
        logger.info(f"Dashboard notification for alert {alert.alert_id}")
        # In production: websocket_broadcast(alert.to_dict())

    def _log_notification(self, alert: Alert, channel: NotificationChannel, status: str) -> None:
        """Log notification attempt"""
        self.notification_log.append(
            {
                "alert_id": alert.alert_id,
                "channel": channel.value,
                "status": status,
                "timestamp": datetime.now().isoformat(),
            }
        )


class EscalationService:
    """Service for managing alert escalation"""

    def __init__(self, alert_store: AlertStore, notification_service: NotificationService):
        self.alert_store = alert_store
        self.notification_service = notification_service
        self.escalation_rules = self._define_escalation_rules()

    def _define_escalation_rules(self) -> Dict:
        """Define escalation rules based on severity and type"""
        return {
            AlertSeverity.LOW: {"escalate_after": 900, "levels": [AlertEscalationLevel.LEVEL_1]},  # 15 min
            AlertSeverity.MEDIUM: {"escalate_after": 600, "levels": [AlertEscalationLevel.LEVEL_1, AlertEscalationLevel.LEVEL_2]},  # 10 min
            AlertSeverity.HIGH: {"escalate_after": 300, "levels": [AlertEscalationLevel.LEVEL_2, AlertEscalationLevel.LEVEL_3]},  # 5 min
            AlertSeverity.CRITICAL: {"escalate_after": 60, "levels": [AlertEscalationLevel.LEVEL_1, AlertEscalationLevel.LEVEL_2, AlertEscalationLevel.LEVEL_3, AlertEscalationLevel.LEVEL_4]},  # 1 min
        }

    def process_escalations(self) -> Tuple[int, int]:
        """Process pending escalations"""
        escalation_candidates = self.alert_store.get_escalation_candidates()
        processed = 0
        escalated = 0

        for alert in escalation_candidates:
            if self.escalate_alert(alert):
                escalated += 1
            processed += 1

        return processed, escalated

    def escalate_alert(self, alert: Alert) -> bool:
        """Escalate single alert to next level"""
        rule = self.escalation_rules.get(alert.severity)
        if not rule:
            return False

        # Determine next escalation level
        current_level_index = len(rule["levels"]) - 1
        if alert.escalation_level in rule["levels"]:
            current_level_index = rule["levels"].index(alert.escalation_level)

        if current_level_index < len(rule["levels"]) - 1:
            next_level = rule["levels"][current_level_index + 1]
            alert.escalation_level = next_level
            alert.last_escalated_at = datetime.now()

            # Determine notification channels for escalation
            channels = self._get_channels_for_level(next_level)
            recipient = self._get_recipient_for_level(next_level, alert.project_id)

            logger.warning(
                f"Escalating alert {alert.alert_id} from {alert.escalation_level.value} "
                f"to {next_level.value}"
            )

            self.notification_service.send_notification(alert, channels, recipient)
            return True

        return False

    def _get_channels_for_level(self, level: AlertEscalationLevel) -> List[NotificationChannel]:
        """Get notification channels for escalation level"""
        channel_map = {
            AlertEscalationLevel.LEVEL_1: [NotificationChannel.DASHBOARD, NotificationChannel.EMAIL],
            AlertEscalationLevel.LEVEL_2: [
                NotificationChannel.SMS,
                NotificationChannel.SLACK,
                NotificationChannel.EMAIL,
            ],
            AlertEscalationLevel.LEVEL_3: [NotificationChannel.SMS, NotificationChannel.SLACK],
            AlertEscalationLevel.LEVEL_4: [NotificationChannel.SMS, NotificationChannel.PUSH_NOTIFICATION],
        }
        return channel_map.get(level, [NotificationChannel.DASHBOARD])

    def _get_recipient_for_level(self, level: AlertEscalationLevel, project_id: str) -> Optional[str]:
        """Get recipient contact for escalation level"""
        # In production: look up from database or project config
        recipient_map = {
            AlertEscalationLevel.LEVEL_1: "site_engineer@company.com",
            AlertEscalationLevel.LEVEL_2: "safety_officer@company.com",
            AlertEscalationLevel.LEVEL_3: "project_manager@company.com",
            AlertEscalationLevel.LEVEL_4: "emergency_services@company.com",
        }
        return recipient_map.get(level)


class AlertServiceManager:
    """Central alert service manager"""

    def __init__(self):
        self.store = AlertStore()
        self.notifications = NotificationService()
        self.escalation = EscalationService(self.store, self.notifications)

    def create_and_send_alert(
        self,
        project_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        recommended_action: Optional[str] = None,
        sensor_id: Optional[str] = None,
        equipment_id: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Alert:
        """Create alert and send notifications"""
        alert_id = f"alert_{project_id}_{datetime.now().isoformat()}"

        alert = Alert(
            alert_id=alert_id,
            project_id=project_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            sensor_id=sensor_id,
            equipment_id=equipment_id,
            location=location,
            recommended_action=recommended_action,
        )

        # Store alert
        self.store.store_alert(alert)

        # Send initial notifications
        initial_channels = self.escalation._get_channels_for_level(alert.escalation_level)
        recipient = self.escalation._get_recipient_for_level(alert.escalation_level, project_id)

        self.notifications.send_notification(alert, initial_channels, recipient)

        logger.info(f"Alert created and sent: {alert_id}")
        return alert

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge alert"""
        return self.store.acknowledge_alert(alert_id, user_id)

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve alert"""
        return self.store.resolve_alert(alert_id)

    def get_alerts(self, project_id: str, unacknowledged_only: bool = False) -> List[Dict]:
        """Get project alerts"""
        alerts = self.store.get_project_alerts(project_id, unacknowledged_only)
        return [a.to_dict() for a in alerts]

    def process_escalations(self) -> Tuple[int, int]:
        """Process pending escalations"""
        return self.escalation.process_escalations()

    def cleanup_project(self, project_id: str) -> int:
        """Clean up alerts for project"""
        return self.store.clear_project_alerts(project_id)


# Global alert manager instance
_alert_manager: Optional[AlertServiceManager] = None


def get_alert_manager() -> AlertServiceManager:
    """Get or create alert manager singleton"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertServiceManager()
    return _alert_manager
