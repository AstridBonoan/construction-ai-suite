"""
Phase 14: Security & Access Controls

Audits credentials, environment variables, file permissions.
Prevents sensitive data leakage.
Validates access to internal endpoints.
"""

import logging
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class CredentialDetector:
    """Detects and prevents credential leakage"""
    
    # Patterns for detecting common credential types
    PATTERNS = {
        'api_key': r'[Aa][Pp][Ii][_-]?[Kk][Ee][Yy][\s:=]+[a-zA-Z0-9_\-\.]{20,}',
        'aws_key': r'(AKIA|AIDA|AIPA|ASIB)[0-9A-Z]{16}',
        'password': r'[Pp]assword[\s:=]+[\'"]?[^\s\'"]+[\'"]?',
        'token': r'[Tt]oken[\s:=]+[a-zA-Z0-9_\-\.]{20,}',
        'private_key': r'BEGIN RSA PRIVATE KEY|BEGIN PRIVATE KEY',
        'connection_string': r'(mongodb|postgresql|mysql):\/\/[^@]*:[^@]*@',
        'oauth_token': r'oauth[_\-]?token[\s:=]+[a-zA-Z0-9_\-\.]{20,}',
        'jwt': r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
    }
    
    @staticmethod
    def detect_in_text(text: str) -> Dict[str, List[str]]:
        """Detect credential patterns in text"""
        findings = {}
        
        for credential_type, pattern in CredentialDetector.PATTERNS.items():
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                findings[credential_type] = matches
        
        return findings
    
    @staticmethod
    def detect_in_dict(data: dict) -> Dict[str, Any]:
        """Detect credentials in dictionary values"""
        findings = {}
        
        def check_value(key, value):
            if isinstance(value, str):
                credentials = CredentialDetector.detect_in_text(value)
                if credentials:
                    findings[key] = credentials
            elif isinstance(value, dict):
                check_dict(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        credentials = CredentialDetector.detect_in_text(item)
                        if credentials:
                            findings[key] = credentials
        
        def check_dict(d):
            for k, v in d.items():
                check_value(k, v)
        
        check_dict(data)
        return findings
    
    @staticmethod
    def sanitize_log_message(message: str) -> str:
        """Remove credentials from log messages"""
        sanitized = message
        
        # Replace common credential patterns with [REDACTED]
        for pattern in [
            r'(password|token|key|secret|auth)["\']?\s*[=:]\s*[^\s,\}\]]+',
            r'(authorization|bearer)\s+[^\s,\}\]]+',
            r'(mongodb|postgresql|mysql):\/\/[^\/]+:[^@]+@',
        ]:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def audit_file(file_path: Path) -> Dict[str, Any]:
        """Audit a file for credentials"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            credentials = CredentialDetector.detect_in_text(content)
            
            return {
                'file': str(file_path),
                'has_credentials': bool(credentials),
                'credentials_found': credentials,
            }
        except Exception as e:
            logger.error(f"Failed to audit {file_path}: {e}")
            return {
                'file': str(file_path),
                'error': str(e),
            }


class EnvironmentAuditor:
    """Audits environment variables for security"""
    
    # Environment variables that should exist
    REQUIRED_ENV_VARS = {
        'LOG_LEVEL': 'INFO',
        'FLASK_ENV': 'production',
    }
    
    # Environment variables that should NOT use defaults
    SENSITIVE_ENV_VARS = {
        'DATABASE_URL': None,
        'JWT_SECRET': None,
        'API_KEY': None,
        'OPENAI_API_KEY': None,
        'AWS_ACCESS_KEY_ID': None,
        'AWS_SECRET_ACCESS_KEY': None,
    }
    
    @staticmethod
    def audit_environment() -> Dict[str, Any]:
        """Audit environment variables"""
        findings = {
            'required_missing': [],
            'sensitive_using_defaults': [],
            'unset_sensitive': [],
            'suspicious_values': [],
        }
        
        # Check required variables
        for var_name, expected_value in EnvironmentAuditor.REQUIRED_ENV_VARS.items():
            if var_name not in os.environ:
                findings['required_missing'].append(var_name)
        
        # Check sensitive variables
        for var_name in EnvironmentAuditor.SENSITIVE_ENV_VARS:
            value = os.environ.get(var_name)
            
            if value is None:
                findings['unset_sensitive'].append(var_name)
            elif value in ['default', '', 'test', 'none', 'null']:
                findings['sensitive_using_defaults'].append({
                    'variable': var_name,
                    'value': value,
                })
            elif re.match(r'^(test|demo|example|mock|fake|dummy)', value, re.IGNORECASE):
                findings['suspicious_values'].append({
                    'variable': var_name,
                    'reason': 'Looks like test/demo value',
                })
        
        return findings
    
    @staticmethod
    def validate_flask_env() -> Tuple[bool, Optional[str]]:
        """Validate Flask environment is production"""
        env = os.environ.get('FLASK_ENV', 'development').lower()
        
        if env != 'production':
            return False, f"FLASK_ENV should be 'production', got '{env}'"
        
        return True, None
    
    @staticmethod
    def validate_debug_mode() -> Tuple[bool, Optional[str]]:
        """Validate Flask debug mode is off"""
        debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        
        if debug:
            return False, "FLASK_DEBUG should be 'false' in production"
        
        return True, None


class FilePermissionAuditor:
    """Audits file permissions for security"""
    
    # Directories that should have restricted permissions
    SENSITIVE_DIRS = {
        'models': 0o755,         # Only owner can write
        'logs': 0o755,
        'config': 0o700,         # Only owner can access
        'data': 0o755,
    }
    
    @staticmethod
    def audit_directory_permissions(base_path: Path) -> Dict[str, Any]:
        """Audit permissions for sensitive directories"""
        findings = {
            'too_permissive': [],
            'missing_dirs': [],
        }
        
        for dir_name, expected_perms in FilePermissionAuditor.SENSITIVE_DIRS.items():
            dir_path = base_path / dir_name
            
            if not dir_path.exists():
                findings['missing_dirs'].append(dir_name)
                continue
            
            # Get current permissions
            stat_info = dir_path.stat()
            current_perms = stat_info.st_mode & 0o777
            
            if current_perms != expected_perms:
                findings['too_permissive'].append({
                    'directory': dir_name,
                    'current': oct(current_perms),
                    'expected': oct(expected_perms),
                })
        
        return findings
    
    @staticmethod
    def fix_directory_permissions(base_path: Path):
        """Fix permissions for sensitive directories"""
        for dir_name, perms in FilePermissionAuditor.SENSITIVE_DIRS.items():
            dir_path = base_path / dir_name
            
            if dir_path.exists():
                try:
                    dir_path.chmod(perms)
                    logger.info(f"Fixed permissions for {dir_name}: {oct(perms)}")
                except Exception as e:
                    logger.error(f"Failed to fix permissions for {dir_name}: {e}")


class AccessControlValidator:
    """Validates access controls for internal endpoints"""
    
    # Endpoints that should be protected
    INTERNAL_ENDPOINTS = {
        '/admin/*': 'internal',
        '/debug/*': 'internal',
        '/metrics/*': 'internal',
        '/logs/*': 'internal',
    }
    
    @staticmethod
    def validate_request_origin(request: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate request came from allowed origin.
        
        Note: This is a simplified check. Use proper CORS and authentication.
        """
        # This would be implemented in the Flask app
        # For now, just documentation
        return True, None
    
    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate API key format and presence"""
        if not api_key:
            return False, "API key is required"
        
        # Validate format (should be long, random string)
        if len(api_key) < 32:
            return False, "API key too short"
        
        # Check it's not a common default
        if api_key.lower() in ['test', 'demo', 'default']:
            return False, "API key should not be a default value"
        
        return True, None
    
    @staticmethod
    def validate_jwt_token(token: str) -> Tuple[bool, Optional[str]]:
        """Validate JWT token format"""
        parts = token.split('.')
        
        if len(parts) != 3:
            return False, "Invalid JWT format"
        
        # Check each part is valid base64
        import base64
        for part in parts:
            try:
                # Add padding if needed
                padded = part + '=' * (4 - len(part) % 4)
                base64.urlsafe_b64decode(padded)
            except Exception:
                return False, "Invalid JWT encoding"
        
        return True, None


class SecurityAuditReport:
    """Generates security audit report"""
    
    @staticmethod
    def generate(base_path: Path) -> Dict[str, Any]:
        """Generate full security audit report"""
        report = {
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'environment': EnvironmentAuditor.audit_environment(),
            'file_permissions': FilePermissionAuditor.audit_directory_permissions(base_path),
            'credentials': {
                'config_files': {},
                'env_files': {},
            },
        }
        
        # Audit config files
        config_dir = base_path / 'config'
        if config_dir.exists():
            for config_file in config_dir.glob('*.json'):
                if 'test' not in config_file.name:
                    try:
                        with open(config_file) as f:
                            config = json.load(f)
                        credentials = CredentialDetector.detect_in_dict(config)
                        if credentials:
                            report['credentials']['config_files'][config_file.name] = credentials
                    except Exception as e:
                        logger.error(f"Failed to audit {config_file}: {e}")
        
        # Check for .env files
        env_files = list(base_path.glob('.env*'))
        for env_file in env_files:
            try:
                with open(env_file) as f:
                    content = f.read()
                credentials = CredentialDetector.detect_in_text(content)
                if credentials:
                    report['credentials']['env_files'][env_file.name] = credentials
            except Exception as e:
                logger.error(f"Failed to audit {env_file}: {e}")
        
        return report
    
    @staticmethod
    def check_critical_issues(report: Dict[str, Any]) -> List[str]:
        """Identify critical security issues"""
        issues = []
        
        env_audit = report.get('environment', {})
        if env_audit.get('required_missing'):
            issues.append(f"Missing required environment variables: {env_audit['required_missing']}")
        
        if env_audit.get('sensitive_using_defaults'):
            issues.append(f"Sensitive vars using defaults: {[x['variable'] for x in env_audit['sensitive_using_defaults']]}")
        
        credentials = report.get('credentials', {})
        if credentials.get('config_files') or credentials.get('env_files'):
            issues.append("Credentials detected in config/env files - must be removed!")
        
        file_perms = report.get('file_permissions', {})
        if file_perms.get('too_permissive'):
            issues.append(f"Directories with too permissive permissions: {[x['directory'] for x in file_perms['too_permissive']]}")
        
        return issues
