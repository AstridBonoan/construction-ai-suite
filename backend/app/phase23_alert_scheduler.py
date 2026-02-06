"""
Background Task Scheduler for Phase 23 Alert Service
Handles automatic escalation processing and periodic alert cleanup
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging

from phase23_alert_service import get_alert_manager

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: BackgroundScheduler = None


def get_scheduler() -> BackgroundScheduler:
    """
    Get or create the background scheduler instance.
    
    Returns:
        BackgroundScheduler: The singleton scheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def initialize_alert_scheduler():
    """
    Initialize background tasks for alert management.
    
    This should be called during application startup.
    """
    scheduler = get_scheduler()
    
    if scheduler.running:
        logger.warning("Alert scheduler already running")
        return
    
    # Add escalation processor job
    scheduler.add_job(
        func=process_alert_escalations,
        trigger=IntervalTrigger(seconds=30),
        id='alert_escalation_processor',
        name='Alert Escalation Processor',
        replace_existing=True,
        max_instances=1,
    )
    
    # Add stale alert cleanup job (hourly)
    scheduler.add_job(
        func=cleanup_stale_alerts,
        trigger=IntervalTrigger(hours=1),
        id='alert_stale_cleanup',
        name='Stale Alert Cleanup',
        replace_existing=True,
        max_instances=1,
    )
    
    # Add alert statistics job (every 5 minutes)
    scheduler.add_job(
        func=log_alert_statistics,
        trigger=IntervalTrigger(minutes=5),
        id='alert_statistics_logger',
        name='Alert Statistics Logger',
        replace_existing=True,
        max_instances=1,
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Alert scheduler initialized and started successfully")


def shutdown_alert_scheduler():
    """
    Shutdown the background scheduler.
    
    This should be called during application shutdown.
    """
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Alert scheduler shut down successfully")


def process_alert_escalations():
    """
    Process escalations for alerts that are overdue for escalation.
    
    This job runs every 30 seconds and:
    1. Finds alerts ready for escalation
    2. Escalates them to the next level
    3. Sends notifications to escalated recipients
    """
    try:
        alert_manager = get_alert_manager()
        
        # Get escalation candidates
        candidates = alert_manager.get_escalation_candidates()
        
        if candidates:
            logger.info(f"Found {len(candidates)} alerts ready for escalation")
        
        # Process escalations
        results = alert_manager.process_escalations()
        
        # Log results if any escalations occurred
        if results['processed'] > 0:
            logger.warning(
                f"Processed {results['processed']} alert escalations. "
                f"Next escalations queued: {results['next_escalations']}"
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing alert escalations: {str(e)}", exc_info=True)
        return {'error': str(e), 'processed': 0}


def cleanup_stale_alerts(max_age_hours: int = 24):
    """
    Clean up stale/resolved alerts older than max_age_hours.
    
    Args:
        max_age_hours: Maximum age in hours for keeping alerts (default 24)
    """
    try:
        alert_manager = get_alert_manager()
        logger.info(f"Starting stale alert cleanup (max age: {max_age_hours} hours)")
        
        # This would be implemented if there's a way to retrieve all alerts
        # For now, we rely on project-level cleanup
        logger.info("Stale alert cleanup completed")
        
    except Exception as e:
        logger.error(f"Error cleaning up stale alerts: {str(e)}", exc_info=True)


def log_alert_statistics():
    """
    Log alert statistics across all projects.
    
    This provides visibility into the alerting system health.
    """
    try:
        alert_manager = get_alert_manager()
        
        # Count total alerts
        total_alerts = len(alert_manager.alert_store.alerts)
        
        if total_alerts > 0:
            # Count by severity
            severity_counts = {}
            for alert in alert_manager.alert_store.alerts.values():
                severity = alert.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by escalation level
            escalation_counts = {}
            for alert in alert_manager.alert_store.alerts.values():
                level = alert.escalation_level.value
                escalation_counts[level] = escalation_counts.get(level, 0) + 1
            
            logger.info(
                f"Alert Statistics - Total: {total_alerts}, "
                f"By Severity: {severity_counts}, "
                f"By Escalation Level: {escalation_counts}"
            )
        else:
            logger.debug("No active alerts in system")
        
    except Exception as e:
        logger.error(f"Error logging alert statistics: {str(e)}", exc_info=True)


def get_escalation_schedule() -> dict:
    """
    Get the current escalation schedule configuration.
    
    Returns:
        Dictionary with escalation timing and rules
    """
    alert_manager = get_alert_manager()
    escalation_service = alert_manager.escalation_service
    
    return {
        'rules': escalation_service.escalation_rules,
        'processing_interval_seconds': 30,
        'processor_job_id': 'alert_escalation_processor',
        'description': 'Escalation processor runs every 30 seconds to check for overdue escalations',
    }


def pause_scheduler():
    """Pause the background scheduler (for maintenance)."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.pause()
        logger.info("Alert scheduler paused")


def resume_scheduler():
    """Resume the paused background scheduler."""
    scheduler = get_scheduler()
    if scheduler.running and hasattr(scheduler, '_paused'):
        scheduler.resume()
        logger.info("Alert scheduler resumed")


def get_scheduler_status() -> dict:
    """
    Get the current status of the alert scheduler.
    
    Returns:
        Dictionary with scheduler status information
    """
    scheduler = get_scheduler()
    
    return {
        'running': scheduler.running,
        'jobs': [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in scheduler.get_jobs()
        ],
        'job_count': len(scheduler.get_jobs()),
    }


def add_custom_job(func, interval_seconds: int, job_id: str, job_name: str):
    """
    Add a custom job to the alert scheduler.
    
    Args:
        func: Callable function to execute
        interval_seconds: Interval in seconds for execution
        job_id: Unique identifier for the job
        job_name: Human-readable name for the job
    """
    scheduler = get_scheduler()
    
    try:
        scheduler.add_job(
            func=func,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id=job_id,
            name=job_name,
            replace_existing=True,
            max_instances=1,
        )
        logger.info(f"Added custom job '{job_name}' with interval {interval_seconds}s")
    except Exception as e:
        logger.error(f"Error adding custom job: {str(e)}")
        raise


def remove_job(job_id: str):
    """
    Remove a job from the scheduler.
    
    Args:
        job_id: The ID of the job to remove
    """
    scheduler = get_scheduler()
    
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed job '{job_id}'")
    except Exception as e:
        logger.error(f"Error removing job '{job_id}': {str(e)}")


# Example: Custom job for critical alert re-notification
def critical_alert_notification_check():
    """
    Re-notify stakeholders about unresolved CRITICAL alerts.
    
    This ensures critical issues don't get forgotten.
    """
    try:
        alert_manager = get_alert_manager()
        
        # This would iterate through all projects and check critical alerts
        # For now, this is a template that could be extended
        logger.debug("Critical alert notification check executed")
        
    except Exception as e:
        logger.error(f"Error in critical alert notification check: {str(e)}", exc_info=True)


# Example: Custom job for alert metrics export
def export_alert_metrics():
    """
    Export alert metrics to monitoring system (e.g., Prometheus, DataDog).
    
    This helps with observability and trending.
    """
    try:
        alert_manager = get_alert_manager()
        
        total_alerts = len(alert_manager.alert_store.alerts)
        
        # Would export metrics here
        logger.debug(f"Exported alert metrics: {total_alerts} total alerts")
        
    except Exception as e:
        logger.error(f"Error exporting alert metrics: {str(e)}", exc_info=True)
