"""
Phase 14: Data Validation & Guardrails

Strict validation for all incoming data before model usage.
Prevents training/predictions on corrupt data.
Provides sensible defaults for optional fields.
"""

from typing import Optional, List, Dict, Any, Tuple
import math


class DataValidator:
    """Validates construction project data"""
    
    # Schema constraints
    REQUIRED_FIELDS = {
        'project_id': str,
        'project_name': str,
        'budget': float,
        'scheduled_duration_days': int,
    }
    
    OPTIONAL_FIELDS_WITH_DEFAULTS = {
        'phase': 'design',
        'status': 'active',
        'location': 'unknown',
        'description': '',
    }
    
    NUMERIC_CONSTRAINTS = {
        'budget': {'min': 0, 'max': 1_000_000_000},
        'scheduled_duration_days': {'min': 1, 'max': 10_000},
        'actual_spend': {'min': 0, 'max': 1_000_000_000},
        'delay_days': {'min': -10_000, 'max': 10_000},
    }
    
    ENUM_FIELDS = {
        'phase': ['design', 'planning', 'construction', 'closeout'],
        'status': ['active', 'completed', 'on_hold', 'cancelled'],
    }
    
    @staticmethod
    def validate_row(row: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single data row.
        
        Returns:
            (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Check required fields
        for field, field_type in DataValidator.REQUIRED_FIELDS.items():
            if field not in row:
                errors.append(f"Missing required field: {field}")
            elif row[field] is None:
                errors.append(f"Field '{field}' is None")
            elif not isinstance(row[field], field_type):
                errors.append(f"Field '{field}' has wrong type: {type(row[field])}")
            elif isinstance(row[field], str) and not row[field].strip():
                errors.append(f"Field '{field}' is empty string")
        
        # Check numeric constraints
        for field, constraints in DataValidator.NUMERIC_CONSTRAINTS.items():
            if field in row and row[field] is not None:
                try:
                    value = float(row[field])
                    
                    # Check for NaN or infinity
                    if math.isnan(value) or math.isinf(value):
                        errors.append(f"Field '{field}' is NaN or infinity: {value}")
                    
                    # Check bounds
                    if value < constraints['min']:
                        errors.append(
                            f"Field '{field}' is below minimum: {value} < {constraints['min']}"
                        )
                    if value > constraints['max']:
                        errors.append(
                            f"Field '{field}' exceeds maximum: {value} > {constraints['max']}"
                        )
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' is not numeric: {row[field]}")
        
        # Check enum fields
        for field, valid_values in DataValidator.ENUM_FIELDS.items():
            if field in row and row[field] is not None:
                if row[field] not in valid_values:
                    errors.append(
                        f"Field '{field}' has invalid value '{row[field]}'. "
                        f"Must be one of: {', '.join(valid_values)}"
                    )
        
        return len(errors) == 0, errors
    
    @staticmethod
    def apply_defaults(row: Dict[str, Any]) -> Dict[str, Any]:
        """Apply defaults for optional fields"""
        cleaned_row = row.copy()
        
        for field, default_value in DataValidator.OPTIONAL_FIELDS_WITH_DEFAULTS.items():
            if field not in cleaned_row or cleaned_row[field] is None:
                cleaned_row[field] = default_value
        
        return cleaned_row
    
    @staticmethod
    def validate_dataset(
        rows: List[Dict[str, Any]],
        allow_partial: bool = False
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate a dataset.
        
        Args:
            rows: List of data rows
            allow_partial: If True, return valid rows + errors list
                          If False, fail on first error
        
        Returns:
            (valid_rows, invalid_rows)
        """
        valid_rows = []
        invalid_rows = []
        
        for idx, row in enumerate(rows):
            is_valid, errors = DataValidator.validate_row(row)
            
            if is_valid:
                cleaned = DataValidator.apply_defaults(row)
                valid_rows.append(cleaned)
            else:
                invalid_rows.append({
                    'row_index': idx,
                    'row_data': row,
                    'errors': errors
                })
                
                if not allow_partial:
                    return [], invalid_rows
        
        return valid_rows, invalid_rows


class InputGuardRails:
    """Guardrails for API inputs"""
    
    @staticmethod
    def validate_project_id(project_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate project ID format"""
        if not project_id:
            return False, "project_id is required"
        
        if not isinstance(project_id, str):
            return False, "project_id must be string"
        
        if len(project_id) < 3:
            return False, "project_id too short (min 3 chars)"
        
        if len(project_id) > 256:
            return False, "project_id too long (max 256 chars)"
        
        # Allow alphanumeric, hyphens, underscores
        if not all(c.isalnum() or c in '-_' for c in project_id):
            return False, "project_id contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_request_size(data: Dict[str, Any], max_records: int = 10000) -> Tuple[bool, Optional[str]]:
        """Validate request payload size"""
        if not isinstance(data, dict):
            return False, "Request body must be JSON object"
        
        # Rough estimate: count of records
        records = data.get('records', [])
        if isinstance(records, list):
            if len(records) > max_records:
                return False, f"Request too large: {len(records)} records > {max_records} max"
        
        return True, None
    
    @staticmethod
    def validate_timestamp(timestamp_str: str) -> Tuple[bool, Optional[str]]:
        """Validate ISO 8601 timestamp"""
        from datetime import datetime
        
        if not timestamp_str:
            return False, "Timestamp is required"
        
        try:
            # Try parsing as ISO 8601
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            datetime.fromisoformat(timestamp_str)
            return True, None
        except (ValueError, TypeError):
            return False, f"Invalid ISO 8601 timestamp: {timestamp_str}"


class SanitizationRules:
    """Sanitize data to prevent injection or misuse"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return str(value)
        
        # Trim whitespace
        value = value.strip()
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        # Remove control characters
        value = ''.join(c for c in value if ord(c) >= 32 or c in '\t\n\r')
        
        return value
    
    @staticmethod
    def sanitize_numeric(value: Any) -> Optional[float]:
        """Sanitize numeric input"""
        try:
            num = float(value)
            
            # Check for NaN/infinity
            if math.isnan(num) or math.isinf(num):
                return None
            
            return num
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """Sanitize dictionary input (prevent deep nesting attacks)"""
        if max_depth <= 0:
            return {}
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key (must be string)
            key = SanitizationRules.sanitize_string(str(key), max_length=256)
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[key] = SanitizationRules.sanitize_string(value)
            elif isinstance(value, (int, float)):
                num = SanitizationRules.sanitize_numeric(value)
                if num is not None:
                    sanitized[key] = num
            elif isinstance(value, dict):
                sanitized[key] = SanitizationRules.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[key] = [
                    v if isinstance(v, (str, int, float)) else str(v)
                    for v in value[:100]  # Limit list length
                ]
            elif value is None:
                sanitized[key] = None
            elif isinstance(value, bool):
                sanitized[key] = value
        
        return sanitized
