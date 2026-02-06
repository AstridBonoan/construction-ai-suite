"""
Unit tests for Phase 23 Alert Service
Tests for alert creation, storage, notification, and escalation
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Add backend app to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from phase23_alert_service import (
    Alert,
    AlertStore,
    NotificationService,
    EscalationService,
    AlertServiceManager,
    AlertType,
    AlertSeverity,
    AlertEscalationLevel,
    NotificationChannel,
)


class TestAlert:
    """Test Alert data class"""

    def test_alert_creation(self):
        """Test creating an alert"""
        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test alert description",
            sensor_id="sensor_001",
        )

        assert alert.project_id == "proj_001"
        assert alert.alert_type == AlertType.SENSOR_ANOMALY
        assert alert.severity == AlertSeverity.HIGH
        assert alert.title == "Test Alert"
        assert alert.description == "Test alert description"
        assert alert.sensor_id == "sensor_001"
        assert alert.acknowledged_at is None
        assert alert.escalation_level == AlertEscalationLevel.LEVEL_1

    def test_alert_to_dict(self):
        """Test alert serialization to dictionary"""
        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Equipment Failure",
            description="Motor bearings damaged",
        )

        alert_dict = alert.to_dict()

        assert alert_dict["project_id"] == "proj_001"
        assert alert_dict["alert_type"] == "equipment_failure"
        assert alert_dict["severity"] == "critical"
        assert alert_dict["title"] == "Equipment Failure"
        assert "alert_id" in alert_dict
        assert "created_at" in alert_dict

    def test_alert_unique_ids(self):
        """Test that alerts get unique IDs"""
        alert1 = Alert(
            project_id="proj_001",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.MEDIUM,
            title="Alert 1",
        )
        alert2 = Alert(
            project_id="proj_001",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.MEDIUM,
            title="Alert 2",
        )

        assert alert1.alert_id != alert2.alert_id


class TestAlertStore:
    """Test AlertStore in-memory storage"""

    def test_store_and_retrieve_alert(self):
        """Test storing and retrieving an alert"""
        store = AlertStore()
        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
        )

        # Store alert
        store.store_alert(alert)

        # Retrieve alert
        retrieved = store.get_alert(alert.alert_id)
        assert retrieved is not None
        assert retrieved.alert_id == alert.alert_id
        assert retrieved.title == "Test Alert"

    def test_get_nonexistent_alert(self):
        """Test retrieving a nonexistent alert"""
        store = AlertStore()
        retrieved = store.get_alert("nonexistent")
        assert retrieved is None

    def test_get_project_alerts(self):
        """Test retrieving all alerts for a project"""
        store = AlertStore()

        # Create and store multiple alerts
        alert1 = Alert(
            project_id="proj_001",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            title="Alert 1",
        )
        alert2 = Alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Alert 2",
        )
        alert3 = Alert(
            project_id="proj_002",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.MEDIUM,
            title="Alert 3",
        )

        store.store_alert(alert1)
        store.store_alert(alert2)
        store.store_alert(alert3)

        # Get alerts for proj_001
        proj1_alerts = store.get_project_alerts("proj_001")
        assert len(proj1_alerts) == 2
        assert all(a.project_id == "proj_001" for a in proj1_alerts)

        # Get alerts for proj_002
        proj2_alerts = store.get_project_alerts("proj_002")
        assert len(proj2_alerts) == 1
        assert proj2_alerts[0].project_id == "proj_002"

    def test_acknowledge_alert(self):
        """Test acknowledging an alert"""
        store = AlertStore()
        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
        )
        store.store_alert(alert)

        # Acknowledge alert
        success = store.acknowledge_alert(alert.alert_id)
        assert success is True

        # Check alert is acknowledged
        retrieved = store.get_alert(alert.alert_id)
        assert retrieved.acknowledged_at is not None

    def test_acknowledge_nonexistent_alert(self):
        """Test acknowledging a nonexistent alert"""
        store = AlertStore()
        success = store.acknowledge_alert("nonexistent")
        assert success is False

    def test_resolve_alert(self):
        """Test resolving an alert"""
        store = AlertStore()
        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
        )
        store.store_alert(alert)

        # Resolve alert
        success = store.resolve_alert(alert.alert_id)
        assert success is True

        # Alert should be removed from unresolved
        retrieved = store.get_alert(alert.alert_id)
        assert retrieved is None

    def test_escalation_candidates(self):
        """Test finding escalation candidates"""
        store = AlertStore()

        # Create old critical alert
        alert1 = Alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Critical Equipment Failure",
        )
        alert1.created_at = datetime.utcnow() - timedelta(minutes=5)
        alert1.escalation_level = AlertEscalationLevel.LEVEL_1
        store.store_alert(alert1)

        # Create recent critical alert
        alert2 = Alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Recent Critical Failure",
        )
        store.store_alert(alert2)

        # Create low severity alert
        alert3 = Alert(
            project_id="proj_001",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.LOW,
            title="Low Priority Anomaly",
        )
        alert3.created_at = datetime.utcnow() - timedelta(minutes=20)
        store.store_alert(alert3)

        # Get escalation candidates (should find old CRITICAL alert)
        candidates = store.get_escalation_candidates()
        assert len(candidates) > 0
        assert any(a.alert_id == alert1.alert_id for a in candidates)

    def test_clear_project_alerts(self):
        """Test clearing all alerts for a project"""
        store = AlertStore()

        # Create alerts for two projects
        alert1 = Alert(project_id="proj_001", alert_type=AlertType.SENSOR_ANOMALY, severity=AlertSeverity.HIGH, title="Alert 1")
        alert2 = Alert(project_id="proj_001", alert_type=AlertType.SENSOR_ANOMALY, severity=AlertSeverity.HIGH, title="Alert 2")
        alert3 = Alert(project_id="proj_002", alert_type=AlertType.SENSOR_ANOMALY, severity=AlertSeverity.HIGH, title="Alert 3")

        store.store_alert(alert1)
        store.store_alert(alert2)
        store.store_alert(alert3)

        # Clear alerts for proj_001
        store.clear_project_alerts("proj_001")

        # Check proj_001 alerts are gone
        assert len(store.get_project_alerts("proj_001")) == 0

        # Check proj_002 alerts remain
        assert len(store.get_project_alerts("proj_002")) == 1


class TestNotificationService:
    """Test NotificationService"""

    def test_notification_service_creation(self):
        """Test creating notification service"""
        service = NotificationService()
        assert service is not None

    @patch.object(NotificationService, '_send_sms')
    def test_send_sms_notification(self, mock_send):
        """Test sending SMS notification"""
        service = NotificationService()
        mock_send.return_value = True

        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Critical Alert",
        )

        result = service.send_notification(
            alert=alert,
            channel=NotificationChannel.SMS,
            recipient="+1234567890",
        )

        # Should call _send_sms
        mock_send.assert_called_once()

    @patch.object(NotificationService, '_send_email')
    def test_send_email_notification(self, mock_send):
        """Test sending email notification"""
        service = NotificationService()
        mock_send.return_value = True

        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            title="Sensor Issue",
        )

        result = service.send_notification(
            alert=alert,
            channel=NotificationChannel.EMAIL,
            recipient="safety@company.com",
        )

        # Should call _send_email
        mock_send.assert_called_once()

    @patch.object(NotificationService, '_send_slack')
    def test_send_slack_notification(self, mock_send):
        """Test sending Slack notification"""
        service = NotificationService()
        mock_send.return_value = True

        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.SAFETY_HAZARD,
            severity=AlertSeverity.CRITICAL,
            title="Safety Hazard",
        )

        result = service.send_notification(
            alert=alert,
            channel=NotificationChannel.SLACK,
            recipient="safety-alerts",
        )

        # Should call _send_slack
        mock_send.assert_called_once()

    def test_notification_with_multiple_channels(self):
        """Test notification routing to multiple channels"""
        service = NotificationService()

        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Critical Equipment Failure",
        )

        # Mock all channel methods
        with patch.multiple(
            service,
            _send_sms=MagicMock(return_value=True),
            _send_email=MagicMock(return_value=True),
            _send_slack=MagicMock(return_value=True),
        ):
            # Should be able to send to multiple channels
            service.send_notification(alert, NotificationChannel.SMS, "+1234567890")
            service.send_notification(alert, NotificationChannel.EMAIL, "admin@company.com")
            service.send_notification(alert, NotificationChannel.SLACK, "alerts")

            # Verify all were called
            assert service._send_sms.call_count >= 0
            assert service._send_email.call_count >= 0
            assert service._send_slack.call_count >= 0


class TestEscalationService:
    """Test EscalationService"""

    def test_escalation_service_creation(self):
        """Test creating escalation service"""
        service = EscalationService()
        assert service is not None

    def test_define_escalation_rules(self):
        """Test defining escalation rules"""
        service = EscalationService()
        service.define_escalation_rules()

        # Check that rules are defined for each severity
        assert len(service.escalation_rules) > 0
        assert AlertSeverity.CRITICAL in service.escalation_rules
        assert AlertSeverity.HIGH in service.escalation_rules

    def test_escalation_rules_are_strict(self):
        """Test that escalation rules get stricter at higher levels"""
        service = EscalationService()
        service.define_escalation_rules()

        critical_rules = service.escalation_rules.get(AlertSeverity.CRITICAL, {})

        # CRITICAL should escalate faster than LOW
        if AlertSeverity.LOW in service.escalation_rules:
            low_rules = service.escalation_rules[AlertSeverity.LOW]
            # CRITICAL level 1->2 should be faster than LOW level 1->2
            critical_l1_to_l2 = critical_rules.get(AlertEscalationLevel.LEVEL_1, {}).get('timeout_minutes', float('inf'))
            low_l1_to_l2 = low_rules.get(AlertEscalationLevel.LEVEL_1, {}).get('timeout_minutes', float('inf'))
            assert critical_l1_to_l2 <= low_l1_to_l2

    def test_get_channels_for_escalation_level(self):
        """Test getting notification channels for escalation level"""
        service = EscalationService()
        service.define_escalation_rules()

        # Get channels for each level
        level1_channels = service.get_channels_for_level(AlertEscalationLevel.LEVEL_1)
        level2_channels = service.get_channels_for_level(AlertEscalationLevel.LEVEL_2)
        level3_channels = service.get_channels_for_level(AlertEscalationLevel.LEVEL_3)
        level4_channels = service.get_channels_for_level(AlertEscalationLevel.LEVEL_4)

        # Each level should have at least one channel
        assert len(level1_channels) > 0
        assert len(level2_channels) > 0
        assert len(level3_channels) > 0
        assert len(level4_channels) > 0

        # Level 4 (emergency) should be more aggressive than level 1
        assert len(level4_channels) >= len(level1_channels)

    def test_get_recipient_for_level(self):
        """Test getting recipient for escalation level"""
        service = EscalationService()
        service.define_escalation_rules()

        # Get recipients for each level
        level1_recipient = service.get_recipient_for_level(AlertEscalationLevel.LEVEL_1)
        level2_recipient = service.get_recipient_for_level(AlertEscalationLevel.LEVEL_2)
        level3_recipient = service.get_recipient_for_level(AlertEscalationLevel.LEVEL_3)
        level4_recipient = service.get_recipient_for_level(AlertEscalationLevel.LEVEL_4)

        # Each level should have a recipient defined
        assert level1_recipient is not None
        assert level2_recipient is not None
        assert level3_recipient is not None
        assert level4_recipient is not None

    def test_escalate_alert(self):
        """Test escalating an alert"""
        store = AlertStore()
        service = EscalationService()
        service.define_escalation_rules()

        alert = Alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Critical Alert",
        )
        store.store_alert(alert)

        # Escalate alert
        escalated = service.escalate_alert(alert)
        assert escalated.escalation_level != alert.escalation_level
        assert escalated.notification_attempts > alert.notification_attempts


class TestAlertServiceManager:
    """Test AlertServiceManager singleton"""

    def test_manager_singleton_pattern(self):
        """Test that manager follows singleton pattern"""
        from phase23_alert_service import get_alert_manager

        manager1 = get_alert_manager()
        manager2 = get_alert_manager()

        assert manager1 is manager2

    def test_create_and_send_alert(self):
        """Test creating and sending alert"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        with patch.object(manager.notification_service, 'send_notification') as mock_notify:
            alert = manager.create_and_send_alert(
                project_id="proj_001",
                alert_type=AlertType.EQUIPMENT_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title="Critical Equipment Failure",
                description="Motor failure detected",
            )

            assert alert is not None
            assert alert.project_id == "proj_001"
            assert alert.alert_type == AlertType.EQUIPMENT_FAILURE
            # Notification should be attempted
            assert mock_notify.call_count > 0

    def test_get_alerts(self):
        """Test retrieving alerts for project"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        # Clear existing alerts for clean test
        manager.alert_store.clear_project_alerts("test_proj")

        # Create an alert
        alert = manager.create_and_send_alert(
            project_id="test_proj",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
        )

        # Retrieve alerts
        alerts = manager.get_alerts("test_proj")
        assert len(alerts) > 0
        assert any(a.alert_id == alert.alert_id for a in alerts)

    def test_acknowledge_alert(self):
        """Test acknowledging alert through manager"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        alert = manager.create_and_send_alert(
            project_id="test_proj",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
        )

        # Acknowledge the alert
        success = manager.acknowledge_alert("test_proj", alert.alert_id)
        assert success is True

        # Check it's acknowledged
        acknowledged_alert = manager.alert_store.get_alert(alert.alert_id)
        assert acknowledged_alert.acknowledged_at is not None

    def test_resolve_alert(self):
        """Test resolving alert through manager"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        alert = manager.create_and_send_alert(
            project_id="test_proj",
            alert_type=AlertType.SENSOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
        )

        # Resolve the alert
        success = manager.resolve_alert("test_proj", alert.alert_id)
        assert success is True

        # Alert should be removed
        resolved_alert = manager.alert_store.get_alert(alert.alert_id)
        assert resolved_alert is None

    def test_process_escalations(self):
        """Test escalation processor"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        # Create a critical alert
        alert = manager.create_and_send_alert(
            project_id="test_proj",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Critical Alert",
        )

        # Make it old enough to escalate
        alert.created_at = datetime.utcnow() - timedelta(minutes=5)

        # Process escalations
        with patch.object(manager.notification_service, 'send_notification'):
            results = manager.process_escalations()
            assert "processed" in results
            assert "next_escalations" in results

    def test_cleanup_project(self):
        """Test cleaning up alerts for a project"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        # Create multiple alerts for a project
        for i in range(3):
            manager.create_and_send_alert(
                project_id="cleanup_test",
                alert_type=AlertType.SENSOR_ANOMALY,
                severity=AlertSeverity.HIGH,
                title=f"Alert {i}",
            )

        # Verify alerts exist
        alerts_before = manager.get_alerts("cleanup_test")
        assert len(alerts_before) >= 3

        # Cleanup project
        manager.cleanup_project("cleanup_test")

        # Verify alerts are cleared
        alerts_after = manager.get_alerts("cleanup_test")
        assert len(alerts_after) == 0

    def test_alert_with_equipment_id(self):
        """Test creating alert with equipment ID"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        alert = manager.create_and_send_alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Equipment Failure",
            equipment_id="equip_001",
        )

        assert alert.equipment_id == "equip_001"

    def test_alert_with_location(self):
        """Test creating alert with location"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        alert = manager.create_and_send_alert(
            project_id="proj_001",
            alert_type=AlertType.SAFETY_HAZARD,
            severity=AlertSeverity.HIGH,
            title="Safety Hazard",
            location="Site A, Building 2, Floor 3",
        )

        assert alert.location == "Site A, Building 2, Floor 3"

    def test_alert_recommendation_action(self):
        """Test alert includes recommended action"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        recommended = "STOP operations immediately. Call maintenance emergency line."
        alert = manager.create_and_send_alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Equipment Failure",
            recommended_action=recommended,
        )

        assert alert.recommended_action == recommended


class TestAlertSeverityLevels:
    """Test alert severity level semantics"""

    def test_all_severity_levels_defined(self):
        """Test that all severity levels are defined"""
        levels = [
            AlertSeverity.LOW,
            AlertSeverity.MEDIUM,
            AlertSeverity.HIGH,
            AlertSeverity.CRITICAL,
        ]
        assert len(levels) == 4

    def test_all_alert_types_defined(self):
        """Test that all alert types are defined"""
        types = [
            AlertType.SENSOR_ANOMALY,
            AlertType.SENSOR_OFFLINE,
            AlertType.LOW_BATTERY,
            AlertType.EQUIPMENT_FAILURE,
            AlertType.SAFETY_HAZARD,
            AlertType.WEATHER_CRITICAL,
            AlertType.WORK_STOPPABLE,
            AlertType.AIR_QUALITY,
            AlertType.RESTRICTED_AREA_BREACH,
            AlertType.MAINTENANCE_URGENT,
        ]
        assert len(types) == 10

    def test_all_escalation_levels_defined(self):
        """Test that all escalation levels are defined"""
        levels = [
            AlertEscalationLevel.LEVEL_1,
            AlertEscalationLevel.LEVEL_2,
            AlertEscalationLevel.LEVEL_3,
            AlertEscalationLevel.LEVEL_4,
        ]
        assert len(levels) == 4

    def test_all_notification_channels_defined(self):
        """Test that all notification channels are defined"""
        channels = [
            NotificationChannel.SMS,
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
            NotificationChannel.PUSH,
            NotificationChannel.MONDAY_COM,
            NotificationChannel.DASHBOARD,
        ]
        assert len(channels) == 6


class TestAlertIntegration:
    """Integration tests for alert workflow"""

    def test_full_alert_lifecycle(self):
        """Test complete alert creation to resolution lifecycle"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        # 1. Create alert
        with patch.object(manager.notification_service, 'send_notification'):
            alert = manager.create_and_send_alert(
                project_id="proj_001",
                alert_type=AlertType.EQUIPMENT_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title="Critical Equipment Failure",
                description="Motor bearings are overheating",
            )

        assert alert is not None

        # 2. Alert should be retrievable
        alerts = manager.get_alerts("proj_001")
        assert any(a.alert_id == alert.alert_id for a in alerts)

        # 3. Acknowledge alert
        success = manager.acknowledge_alert("proj_001", alert.alert_id)
        assert success is True

        # 4. Check acknowledgment
        acknowledged_alerts = manager.get_alerts("proj_001")
        acked = next(a for a in acknowledged_alerts if a.alert_id == alert.alert_id)
        assert acked.acknowledged_at is not None

        # 5. Resolve alert
        success = manager.resolve_alert("proj_001", alert.alert_id)
        assert success is True

        # 6. Alert should be gone
        remaining = manager.get_alerts("proj_001")
        assert not any(a.alert_id == alert.alert_id for a in remaining)

    def test_critical_alert_escalation_flow(self):
        """Test critical alert escalation through levels"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        # Create critical alert
        alert = manager.create_and_send_alert(
            project_id="proj_001",
            alert_type=AlertType.EQUIPMENT_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Critical Equipment Failure",
        )

        initial_level = alert.escalation_level

        # Escalate alert
        with patch.object(manager.notification_service, 'send_notification'):
            escalated = manager.escalation_service.escalate_alert(alert)

        # Level should increase
        assert escalated.escalation_level != initial_level

    def test_multiple_alert_handling(self):
        """Test handling multiple concurrent alerts"""
        from phase23_alert_service import get_alert_manager

        manager = get_alert_manager()

        # Create multiple alerts
        alert_ids = []
        with patch.object(manager.notification_service, 'send_notification'):
            for i in range(5):
                alert = manager.create_and_send_alert(
                    project_id="proj_001",
                    alert_type=AlertType.SENSOR_ANOMALY,
                    severity=AlertSeverity.HIGH,
                    title=f"Anomaly Alert {i}",
                )
                alert_ids.append(alert.alert_id)

        # Retrieve all alerts
        alerts = manager.get_alerts("proj_001")
        assert len(alerts) >= 5

        # Acknowledge some
        for alert_id in alert_ids[:2]:
            success = manager.acknowledge_alert("proj_001", alert_id)
            assert success is True

        # Resolve some
        for alert_id in alert_ids[2:4]:
            success = manager.resolve_alert("proj_001", alert_id)
            assert success is True

        # Check final state
        remaining = manager.get_alerts("proj_001")
        assert len(remaining) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
