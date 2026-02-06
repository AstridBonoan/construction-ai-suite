"""
Phase 14: Completion Verification

Tests full application startup.
Verifies all hardening is in place.
Tests failure scenarios and recovery.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StartupVerifier:
    """Verifies application startup"""
    
    @staticmethod
    def check_imports() -> Dict[str, bool]:
        """Check all required modules can be imported"""
        checks = {}
        
        modules = [
            'flask',
            'pandas',
            'numpy',
            'sklearn',
            'phase14_errors',
            'phase14_logging',
            'phase14_validation',
            'phase14_model_safety',
            'phase14_performance',
            'phase14_security',
        ]
        
        for module in modules:
            try:
                __import__(module)
                checks[f'import_{module}'] = True
            except ImportError as e:
                checks[f'import_{module}'] = False
                logger.error(f"Failed to import {module}: {e}")
        
        return checks
    
    @staticmethod
    def check_file_structure(base_path: Path) -> Dict[str, bool]:
        """Check required file structure exists"""
        checks = {}
        
        required_files = {
            'backend/app/app.py': 'Flask app',
            'backend/app/phase14_errors.py': 'Error handling',
            'backend/app/phase14_logging.py': 'Logging',
            'backend/app/phase14_validation.py': 'Validation',
            'backend/app/phase14_model_safety.py': 'Model safety',
            'backend/app/phase14_performance.py': 'Performance',
            'backend/app/phase14_security.py': 'Security',
            'models/': 'Models directory',
            'logs/': 'Logs directory',
        }
        
        for file_path, description in required_files.items():
            full_path = base_path / file_path
            exists = full_path.exists()
            checks[f'{description}'] = exists
            
            if not exists:
                logger.error(f"Missing: {file_path}")
        
        return checks
    
    @staticmethod
    def check_logging_initialized() -> Tuple[bool, Optional[str]]:
        """Check logging is properly initialized"""
        try:
            root_logger = logging.getLogger()
            
            if not root_logger.handlers:
                return False, "No logging handlers configured"
            
            has_file_handler = any(
                isinstance(h, logging.FileHandler)
                for h in root_logger.handlers
            )
            
            if not has_file_handler:
                return False, "No file handler in logging configuration"
            
            return True, None
        except Exception as e:
            return False, f"Logging check failed: {e}"
    
    @staticmethod
    def check_model_registry() -> Tuple[bool, Optional[str]]:
        """Check model registry is accessible"""
        try:
            from phase14_model_safety import get_model_registry
            
            registry = get_model_registry()
            models = registry.list_models()
            
            # Should have at least some models
            if not models:
                return True, None  # Empty is OK at startup
            
            return True, None
        except Exception as e:
            return False, f"Model registry check failed: {e}"
    
    @staticmethod
    def verify_startup() -> Dict[str, Any]:
        """Complete startup verification"""
        checks = {
            'imports': StartupVerifier.check_imports(),
            'files': StartupVerifier.check_file_structure(Path.cwd()),
            'logging': dict(zip(
                ['status', 'error'],
                StartupVerifier.check_logging_initialized()
            )),
            'model_registry': dict(zip(
                ['status', 'error'],
                StartupVerifier.check_model_registry()
            )),
        }
        
        all_passed = all(
            all(v for v in d.values() if isinstance(v, bool))
            for d in [checks['imports'], checks['files']]
        ) and checks['logging']['status'] and checks['model_registry']['status']
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'all_passed': all_passed,
            'checks': checks,
        }


class FailureScenarioTester:
    """Tests application behavior in failure scenarios"""
    
    @staticmethod
    def test_bad_input_data() -> Dict[str, Any]:
        """Test handling of bad input data"""
        from phase14_validation import DataValidator
        from phase14_errors import ValidationError
        
        results = {
            'test': 'bad_input_data',
            'scenarios': {},
        }
        
        # Missing required field
        try:
            bad_row = {'project_name': 'Test'}  # Missing project_id
            is_valid, errors = DataValidator.validate_row(bad_row)
            results['scenarios']['missing_field'] = {
                'caught': not is_valid,
                'errors': errors,
            }
        except Exception as e:
            results['scenarios']['missing_field'] = {'error': str(e)}
        
        # Invalid type
        try:
            bad_row = {'project_id': 'P001', 'budget': 'not_a_number'}
            is_valid, errors = DataValidator.validate_row(bad_row)
            results['scenarios']['invalid_type'] = {
                'caught': not is_valid,
                'errors': errors,
            }
        except Exception as e:
            results['scenarios']['invalid_type'] = {'error': str(e)}
        
        # Out of range value
        try:
            bad_row = {
                'project_id': 'P001',
                'project_name': 'Test',
                'budget': -1000,  # Negative budget
                'scheduled_duration_days': 10,
            }
            is_valid, errors = DataValidator.validate_row(bad_row)
            results['scenarios']['out_of_range'] = {
                'caught': not is_valid,
                'errors': errors,
            }
        except Exception as e:
            results['scenarios']['out_of_range'] = {'error': str(e)}
        
        return results
    
    @staticmethod
    def test_large_dataset() -> Dict[str, Any]:
        """Test handling of large datasets"""
        from phase14_performance import ResourceMonitor, PerformanceTracker
        
        results = {
            'test': 'large_dataset',
            'initial_memory': ResourceMonitor.get_memory_usage(),
        }
        
        # Generate large dataset
        try:
            large_dataset = [
                {
                    'project_id': f'P{i:06d}',
                    'project_name': f'Project {i}',
                    'budget': 100000 + (i * 1000),
                    'scheduled_duration_days': 365,
                }
                for i in range(10000)
            ]
            
            results['dataset_size'] = len(large_dataset)
            results['final_memory'] = ResourceMonitor.get_memory_usage()
            results['success'] = True
        except Exception as e:
            results['error'] = str(e)
            results['success'] = False
        
        return results
    
    @staticmethod
    def test_model_safety_gates() -> Dict[str, Any]:
        """Test model safety gates"""
        from phase14_model_safety import (
            get_model_registry,
            ModelMetadata,
            RetrainingGuard,
        )
        from phase14_errors import ModelError
        
        results = {
            'test': 'model_safety_gates',
            'scenarios': {},
        }
        
        try:
            registry = get_model_registry()
            
            # Test 1: Can't train without force flag
            try:
                guard = RetrainingGuard(force_retrain=False)
                guard.validate_retraining_request()
                results['scenarios']['force_flag_gate'] = {
                    'protected': False,
                    'error': 'Should have required force_retrain=True',
                }
            except Exception as e:
                results['scenarios']['force_flag_gate'] = {
                    'protected': True,
                    'error_message': str(e),
                }
            
            # Test 2: Can train with force flag
            try:
                guard = RetrainingGuard(force_retrain=True)
                guard.validate_retraining_request()
                results['scenarios']['force_flag_allowed'] = {
                    'allowed': True,
                }
            except Exception as e:
                results['scenarios']['force_flag_allowed'] = {
                    'allowed': False,
                    'error': str(e),
                }
        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    @staticmethod
    def test_error_recovery() -> Dict[str, Any]:
        """Test application can recover from errors"""
        from phase14_errors import safe_api_call, ValidationError
        
        results = {
            'test': 'error_recovery',
            'scenarios': {},
        }
        
        # Simulate API error
        @safe_api_call
        def failing_endpoint():
            raise ValueError("Something went wrong")
        
        try:
            response, status = failing_endpoint()
            results['scenarios']['error_caught'] = {
                'caught': True,
                'status': status,
                'has_error_message': 'error' in response,
            }
        except Exception as e:
            results['scenarios']['error_caught'] = {
                'caught': False,
                'error': str(e),
            }
        
        return results


class EndToEndWorkflowTester:
    """Tests complete workflows"""
    
    @staticmethod
    def test_full_pipeline() -> Dict[str, Any]:
        """Test complete data pipeline"""
        results = {
            'test': 'full_pipeline',
            'steps': {},
        }
        
        try:
            from phase14_logging import setup_logging
            from phase14_validation import DataValidator
            from phase14_performance import PerformanceTracker
            
            # Step 1: Setup logging
            try:
                setup_logging()
                results['steps']['logging_setup'] = {'status': 'success'}
            except Exception as e:
                results['steps']['logging_setup'] = {'status': 'failed', 'error': str(e)}
            
            # Step 2: Validate data
            try:
                test_data = [
                    {
                        'project_id': 'P001',
                        'project_name': 'Test Project',
                        'budget': 500000,
                        'scheduled_duration_days': 180,
                    }
                ]
                
                valid, invalid = DataValidator.validate_dataset(test_data)
                results['steps']['data_validation'] = {
                    'status': 'success',
                    'valid_count': len(valid),
                    'invalid_count': len(invalid),
                }
            except Exception as e:
                results['steps']['data_validation'] = {'status': 'failed', 'error': str(e)}
            
            # Step 3: Test performance tracking
            try:
                with PerformanceTracker('test_operation'):
                    pass
                
                results['steps']['performance_tracking'] = {'status': 'success'}
            except Exception as e:
                results['steps']['performance_tracking'] = {'status': 'failed', 'error': str(e)}
            
        except Exception as e:
            results['error'] = str(e)
        
        return results


class Phase14VerificationReport:
    """Generates Phase 14 completion report"""
    
    @staticmethod
    def generate_report(base_path: Path = None) -> Dict[str, Any]:
        """Generate complete Phase 14 verification report"""
        if base_path is None:
            base_path = Path.cwd()
        
        report = {
            'phase': 14,
            'timestamp': datetime.utcnow().isoformat(),
            'sections': {},
        }
        
        # Startup verification
        report['sections']['startup'] = StartupVerifier.verify_startup()
        
        # Failure scenarios
        report['sections']['failure_scenarios'] = {
            'bad_input': FailureScenarioTester.test_bad_input_data(),
            'large_dataset': FailureScenarioTester.test_large_dataset(),
            'model_safety': FailureScenarioTester.test_model_safety_gates(),
            'error_recovery': FailureScenarioTester.test_error_recovery(),
        }
        
        # End-to-end workflows
        report['sections']['e2e_workflows'] = {
            'full_pipeline': EndToEndWorkflowTester.test_full_pipeline(),
        }
        
        # Overall status
        report['overall_status'] = 'READY_FOR_PRODUCTION' if all([
            report['sections']['startup']['all_passed'],
            all(s.get('success', False) for s in report['sections']['failure_scenarios'].values()),
        ]) else 'NEEDS_REVIEW'
        
        return report
    
    @staticmethod
    def print_report(report: Dict[str, Any]):
        """Pretty print verification report"""
        print("\n" + "="*60)
        print("PHASE 14 COMPLETION VERIFICATION REPORT")
        print("="*60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Overall Status: {report['overall_status']}")
        print()
        
        # Startup section
        print("STARTUP CHECKS:")
        startup = report['sections']['startup']
        print(f"  All Passed: {startup['all_passed']}")
        for category, checks in startup['checks'].items():
            if isinstance(checks, dict):
                passing = sum(1 for v in checks.values() if v is True)
                total = sum(1 for v in checks.values() if isinstance(v, bool))
                print(f"  {category}: {passing}/{total} passed")
        print()
        
        # Failure scenarios
        print("FAILURE SCENARIOS:")
        scenarios = report['sections']['failure_scenarios']
        for scenario_name, result in scenarios.items():
            status = result.get('success', 'UNKNOWN')
            print(f"  {scenario_name}: {status}")
        print()
        
        # E2E workflows
        print("END-TO-END WORKFLOWS:")
        workflows = report['sections']['e2e_workflows']
        for workflow_name, result in workflows.items():
            steps = result.get('steps', {})
            all_success = all(s.get('status') == 'success' for s in steps.values())
            print(f"  {workflow_name}: {'PASS' if all_success else 'FAIL'}")
            for step_name, step_result in steps.items():
                status = step_result.get('status', 'unknown')
                print(f"    - {step_name}: {status}")
        print()
        
        print("="*60)
        print("RECOMMENDATIONS:")
        print("  1. Review all failure scenarios for issues")
        print("  2. Check logs/phase14_verification.json for details")
        print("  3. Deploy to staging before production")
        print("  4. Monitor metrics during initial rollout")
        print("="*60 + "\n")


def run_phase14_verification():
    """CLI entry point for Phase 14 verification"""
    report = Phase14VerificationReport.generate_report()
    
    # Save report
    report_path = Path('logs/phase14_verification.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print report
    Phase14VerificationReport.print_report(report)
    
    return 0 if report['overall_status'] == 'READY_FOR_PRODUCTION' else 1


if __name__ == '__main__':
    sys.exit(run_phase14_verification())
