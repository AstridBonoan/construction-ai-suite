from flask import Flask, request
from flask_cors import CORS
from app.routes.project_delay import project_delay_bp
from app.api import api_bp
try:
    # Initialize DB (if available) and register models
    from app.models.tenant_models import db as models_db  # noqa: E402
except Exception:
    models_db = None
try:
    from app.phase16_api import schedule_bp
    PHASE16_AVAILABLE = True
except ImportError:
    PHASE16_AVAILABLE = False
try:
    from app.phase23_alert_scheduler import initialize_alert_scheduler, shutdown_alert_scheduler
    PHASE23_ALERT_SCHEDULER_AVAILABLE = True
except ImportError:
    PHASE23_ALERT_SCHEDULER_AVAILABLE = False
import json
import os
import sys
import logging
from pathlib import Path

# Phase 15: Setup logging and environment validation
try:
    from app.phase14_logging import setup_logging, get_logger
    PHASE14_AVAILABLE = True
except ImportError:
    PHASE14_AVAILABLE = False
    # Fallback logging setup if Phase 14 not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure SQLAlchemy from DATABASE_URL when present
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if models_db:
        try:
            models_db.init_app(app)
            # Expose db on app for convenience in scripts/tests
            app.db = models_db
        except Exception:
            logger = logging.getLogger(__name__)
            logger.exception('Failed to initialize SQLAlchemy')

# Setup logging
if PHASE14_AVAILABLE:
    setup_logging()
    logger = get_logger(__name__)
else:
    logger = logging.getLogger(__name__)

# Phase 15: Startup validation and configuration
def validate_environment():
    """Validate required environment variables and directories."""
    issues = []
    
    # Check Flask environment
    flask_env = os.environ.get('FLASK_ENV', 'development')
    if flask_env not in ['development', 'staging', 'production']:
        issues.append(f"Invalid FLASK_ENV: {flask_env}. Must be development, staging, or production.")
    
    # In production, check for required variables
    if flask_env == 'production':
        if not os.environ.get('FLASK_SECRET_KEY'):
            issues.append("FLASK_SECRET_KEY is required in production")
        if os.environ.get('FLASK_DEBUG', 'false').lower() == 'true':
            issues.append("FLASK_DEBUG must be false in production")
    
    # Check required directories
    required_dirs = ['logs', 'models', 'data']
    for dir_name in required_dirs:
        dir_path = Path(__file__).resolve().parents[2] / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    return issues

# Validate on startup
startup_issues = validate_environment()
if startup_issues:
    for issue in startup_issues:
        logger.warning(f"Startup validation: {issue}")

# Get configuration from environment
DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
DEMO_MODE = os.environ.get('DEMO_MODE', 'false').lower() == 'true'
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Register blueprints
app.register_blueprint(project_delay_bp)
app.register_blueprint(api_bp)
# Register Feature 13 blueprints if available
try:
    from app.feature13_monday_oauth import bp as feature13_oauth_bp
    from app.feature13_admin import bp as feature13_admin_bp
    app.register_blueprint(feature13_oauth_bp)
    app.register_blueprint(feature13_admin_bp)
except Exception:
    logger.warning('Feature 13 blueprints not available or failed to register')
if PHASE16_AVAILABLE:
    app.register_blueprint(schedule_bp)
    logger.info("Phase 16 (Schedule Dependencies) enabled")
else:
    logger.warning("Phase 16 (Schedule Dependencies) not available")

# Initialize Phase 23 Alert Scheduler
if PHASE23_ALERT_SCHEDULER_AVAILABLE:
    try:
        initialize_alert_scheduler()
        logger.info("Phase 23 Alert Scheduler initialized successfully")
        
        # Register shutdown handler
        def shutdown_alerts():
            shutdown_alert_scheduler()
        
        app.teardown_appcontext(lambda e: shutdown_alerts())
    except Exception as e:
        logger.error(f"Failed to initialize Phase 23 Alert Scheduler: {str(e)}")
else:
    logger.warning("Phase 23 Alert Scheduler not available")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint. Returns OK if system is running."""
    return (json.dumps({
        "status": "ok",
        "version": "1.0.0",
        "demo_mode": DEMO_MODE
    }), 200, {'Content-Type': 'application/json'})


@app.route('/phase9/outputs', methods=['GET'])
def get_phase9_outputs():
    """Serve Phase 9 outputs for local development.

    Prefers `reports/phase9_outputs.json` if present, otherwise falls back
    to `frontend_phase10/src/mock/phase9_sample.json`.
    """
    # Get project root: __file__ is /backend/app/main.py, so parents[2] = /project_root
    project_root = Path(__file__).resolve().parents[2]
    
    # Try reports path first
    reports_path = project_root / 'reports' / 'phase9_outputs.json'
    if reports_path.exists():
        try:
            with open(reports_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading reports file: {e}")
            return (json.dumps({"error": str(e)}), 500, {'Content-Type': 'application/json'})
    else:
        # Fall back to mock data
        mock_path = project_root / 'frontend_phase10' / 'src' / 'mock' / 'phase9_sample.json'
        if not mock_path.exists():
            logger.error(f"Neither reports nor mock file found. Tried: {reports_path} and {mock_path}")
            return (json.dumps({"error": "phase9 data not found"}), 500, {'Content-Type': 'application/json'})
        try:
            with open(mock_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading mock file: {e}")
            return (json.dumps({"error": str(e)}), 500, {'Content-Type': 'application/json'})

    variant = request.args.get('variant')

    if variant == 'live':
        for obj in data:
            obj['project_name'] = f"{obj.get('project_name','')} (LIVE)"
            if isinstance(obj.get('risk_score'), (int, float)):
                obj['risk_score'] = min(1.0, round(obj['risk_score'] + 0.13, 2))
            if isinstance(obj.get('delay_probability'), (int, float)):
                obj['delay_probability'] = min(1.0, round(obj['delay_probability'] + 0.1, 2))
            if isinstance(obj.get('predicted_delay_days'), (int, float)):
                obj['predicted_delay_days'] = int(obj.get('predicted_delay_days', 0)) + 8

    return (json.dumps(data), 200, {'Content-Type': 'application/json'})


if __name__ == "__main__":
    # Startup banner
    print("\n" + "=" * 70)
    print("  Construction AI Suite - Initialization")
    print("=" * 70)
    print(f"  Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"  Debug Mode: {DEBUG}")
    print(f"  Demo Mode: {DEMO_MODE}")
    print(f"  Log Level: {LOG_LEVEL}")
    if PHASE14_AVAILABLE:
        print("  Phase 14: ✓ Production Hardening Available")
    else:
        print("  Phase 14: ⚠ Production Hardening Not Available (OK for demo)")
    if PHASE23_ALERT_SCHEDULER_AVAILABLE:
        print("  Phase 23: ✓ Real-Time Alert Service Available")
    else:
        print("  Phase 23: ⚠ Real-Time Alert Service Not Available")
    print()
    print("  Endpoints:")
    print("    • Health Check: http://localhost:5000/health")
    print("    • Phase 9 Outputs: http://localhost:5000/phase9/outputs")
    print()
    print(f"  Logs: {Path('logs').resolve()}")
    print("=" * 70 + "\n")
    
    logger.info(f"Starting Construction AI Suite (environment={os.environ.get('FLASK_ENV', 'development')}, demo={DEMO_MODE})")
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=DEBUG
    )
