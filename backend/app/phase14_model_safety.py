"""
Phase 14: Model Safety & Version Control

Ensures model versions are explicitly named and controlled.
Locks inference to specific model versions.
Prevents accidental overwriting.
Adds metadata logging for model usage.
Requires explicit flag for retraining.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a trained model"""
    
    model_name: str              # e.g., "phase9_risk_scorer"
    version: str                 # e.g., "1.0.0" (semver)
    training_date: str           # ISO 8601 timestamp
    training_duration_seconds: float
    training_dataset: str        # Name/description of dataset
    training_records: int        # Number of records used
    model_type: str              # e.g., "decision_tree", "neural_network"
    metrics: Dict[str, float]    # Validation metrics {metric_name: value}
    hyperparameters: Dict[str, Any]  # Training hyperparameters
    description: str             # Human-readable description
    locked: bool = True          # Cannot be overwritten if true
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'model_name': self.model_name,
            'version': self.version,
            'training_date': self.training_date,
            'training_duration_seconds': self.training_duration_seconds,
            'training_dataset': self.training_dataset,
            'training_records': self.training_records,
            'model_type': self.model_type,
            'metrics': self.metrics,
            'hyperparameters': self.hyperparameters,
            'description': self.description,
            'locked': self.locked,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelMetadata':
        """Create from JSON dict"""
        return cls(
            model_name=data['model_name'],
            version=data['version'],
            training_date=data['training_date'],
            training_duration_seconds=data['training_duration_seconds'],
            training_dataset=data['training_dataset'],
            training_records=data['training_records'],
            model_type=data['model_type'],
            metrics=data['metrics'],
            hyperparameters=data['hyperparameters'],
            description=data['description'],
            locked=data.get('locked', True),
        )


class ModelRegistry:
    """Central registry for all trained models"""
    
    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize model registry.
        
        Args:
            registry_path: Path to registry JSON file
                          Defaults to models/registry.json
        """
        self.registry_path = registry_path or (
            Path(__file__).parent.parent.parent / 'models' / 'registry.json'
        )
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing registry
        self.models: Dict[str, ModelMetadata] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from file"""
        if not self.registry_path.exists():
            return
        
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
                self.models = {
                    name: ModelMetadata.from_dict(meta)
                    for name, meta in data.items()
                }
            logger.info(f"Loaded {len(self.models)} models from registry")
        except Exception as e:
            logger.error(f"Failed to load model registry: {e}")
    
    def _save_registry(self):
        """Save registry to file"""
        try:
            data = {
                name: meta.to_dict()
                for name, meta in self.models.items()
            }
            
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Model registry saved")
        except Exception as e:
            logger.error(f"Failed to save model registry: {e}")
    
    def register_model(
        self,
        metadata: ModelMetadata,
        allow_overwrite: bool = False
    ) -> bool:
        """
        Register a trained model.
        
        Args:
            metadata: Model metadata
            allow_overwrite: Allow overwriting locked models
        
        Returns:
            True if registered, False otherwise
        """
        model_id = f"{metadata.model_name}:{metadata.version}"
        
        # Check if model already exists
        if model_id in self.models:
            existing = self.models[model_id]
            if existing.locked and not allow_overwrite:
                logger.error(
                    f"Cannot register model: {model_id} is locked",
                    extra={'details': {'existing_date': existing.training_date}}
                )
                return False
        
        # Register
        self.models[model_id] = metadata
        self._save_registry()
        
        logger.info(
            f"Model registered: {model_id}",
            extra={'details': metadata.to_dict()}
        )
        
        return True
    
    def get_model(self, model_name: str, version: str) -> Optional[ModelMetadata]:
        """Retrieve model metadata"""
        model_id = f"{model_name}:{version}"
        return self.models.get(model_id)
    
    def get_latest_model(self, model_name: str) -> Optional[ModelMetadata]:
        """Get latest version of a model"""
        matching = [
            meta for name, meta in self.models.items()
            if name.startswith(f"{model_name}:")
        ]
        
        if not matching:
            return None
        
        # Sort by version (assume semver)
        matching.sort(key=lambda m: m.version, reverse=True)
        return matching[0]
    
    def lock_model(self, model_name: str, version: str) -> bool:
        """Lock a model to prevent overwrites"""
        model_id = f"{model_name}:{version}"
        
        if model_id not in self.models:
            logger.error(f"Model not found: {model_id}")
            return False
        
        self.models[model_id].locked = True
        self._save_registry()
        
        logger.info(f"Model locked: {model_id}")
        return True
    
    def unlock_model(self, model_name: str, version: str, force_flag: bool = False) -> bool:
        """Unlock a model (requires explicit force flag)"""
        if not force_flag:
            logger.error("Cannot unlock model without force_flag=True")
            return False
        
        model_id = f"{model_name}:{version}"
        
        if model_id not in self.models:
            logger.error(f"Model not found: {model_id}")
            return False
        
        self.models[model_id].locked = False
        self._save_registry()
        
        logger.warning(f"Model unlocked: {model_id} (CAREFUL!)")
        return True
    
    def list_models(self, model_name: Optional[str] = None) -> Dict[str, ModelMetadata]:
        """List all registered models"""
        if model_name is None:
            return self.models.copy()
        
        return {
            name: meta for name, meta in self.models.items()
            if name.startswith(f"{model_name}:")
        }


class ModelInferenceGuard:
    """Guards inference calls to ensure safety"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
    
    def validate_inference_request(
        self,
        model_name: str,
        model_version: str,
        input_data: Dict[str, Any],
        allow_untrained: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Validate an inference request before executing.
        
        Returns:
            (is_valid, error_message)
        """
        
        # Check model exists
        model = self.registry.get_model(model_name, model_version)
        if model is None:
            return False, f"Model not found: {model_name}:{model_version}"
        
        # Check model is not locked (locked means no inference yet)
        if model.locked:
            return False, f"Model is locked and cannot be used for inference: {model_name}:{model_version}"
        
        # Check input data is not empty
        if not input_data:
            return False, "Input data is empty"
        
        # Check input has required fields for model
        # (would be extended based on actual model requirements)
        
        return True, None
    
    def log_inference_call(
        self,
        model_name: str,
        model_version: str,
        input_size: int,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Log model inference call"""
        logger.info(
            f"Model inference: {model_name}:{model_version}",
            extra={
                'event_type': 'MODEL_INFERENCE',
                'model_name': model_name,
                'model_version': model_version,
                'input_size': input_size,
                'duration_ms': duration_ms,
                'success': success,
                'error': error,
            }
        )


class RetrainingGuard:
    """Guards retraining operations to prevent accidental changes"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
    
    def validate_retraining_request(
        self,
        model_name: str,
        training_dataset: str,
        force_retrain: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a retraining request.
        
        Requires explicit force_retrain flag to proceed.
        
        Returns:
            (is_allowed, error_message)
        """
        
        if not force_retrain:
            return False, (
                "Retraining requires explicit force_retrain=True flag. "
                "This is intentional - retraining is not automatic."
            )
        
        # Check dataset exists and is valid
        if not training_dataset or len(training_dataset) < 3:
            return False, "Invalid training dataset name"
        
        # Check we're not retraining the only version of a model
        existing = self.registry.list_models(model_name)
        if len(existing) == 1:
            logger.warning(
                f"About to retrain the only version of {model_name}",
                extra={'details': {'existing_models': list(existing.keys())}}
            )
        
        return True, None
    
    def log_retraining_start(
        self,
        model_name: str,
        training_dataset: str,
        records_count: int
    ):
        """Log start of retraining"""
        logger.info(
            f"Retraining started: {model_name}",
            extra={
                'event_type': 'RETRAIN_START',
                'model_name': model_name,
                'training_dataset': training_dataset,
                'records_count': records_count,
            }
        )
    
    def log_retraining_complete(
        self,
        model_name: str,
        version: str,
        duration_seconds: float,
        metrics: Dict[str, float]
    ):
        """Log completion of retraining"""
        logger.info(
            f"Retraining completed: {model_name}:{version}",
            extra={
                'event_type': 'RETRAIN_COMPLETE',
                'model_name': model_name,
                'model_version': version,
                'duration_seconds': duration_seconds,
                'metrics': metrics,
            }
        )


# Global registry instance
_registry: Optional[ModelRegistry] = None


def get_model_registry(registry_path: Optional[Path] = None) -> ModelRegistry:
    """Get or create global model registry"""
    global _registry
    if _registry is None:
        _registry = ModelRegistry(registry_path)
    return _registry
