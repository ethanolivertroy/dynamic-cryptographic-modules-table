#!/usr/bin/env python3
"""
FedRAMP Cryptographic Module Validator

Validates module definitions against:
1. JSON Schema (structural validation)
2. CMVP Cache (certificate status validation)
3. FedRAMP compliance rules (policy validation)
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import yaml

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None


@dataclass
class ValidationResult:
    """Result of validating a single module."""
    module_name: str
    file_path: str
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cmvp_status: Optional[str] = None
    certificate_number: Optional[int] = None


@dataclass
class ValidationSummary:
    """Summary of all validation results."""
    total_modules: int = 0
    valid_modules: int = 0
    invalid_modules: int = 0
    warnings_count: int = 0
    results: List[ValidationResult] = field(default_factory=list)

    def add_result(self, result: ValidationResult):
        self.results.append(result)
        self.total_modules += 1
        if result.is_valid:
            self.valid_modules += 1
        else:
            self.invalid_modules += 1
        self.warnings_count += len(result.warnings)

    def to_dict(self) -> dict:
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'totalModules': self.total_modules,
            'validModules': self.valid_modules,
            'invalidModules': self.invalid_modules,
            'warningsCount': self.warnings_count,
            'errors': [
                {'module': r.module_name, 'file': r.file_path, 'message': e}
                for r in self.results
                for e in r.errors
            ],
            'warnings': [
                {'module': r.module_name, 'file': r.file_path, 'message': w}
                for r in self.results
                for w in r.warnings
            ],
            'results': [
                {
                    'module': r.module_name,
                    'file': r.file_path,
                    'valid': r.is_valid,
                    'certificateNumber': r.certificate_number,
                    'cmvpStatus': r.cmvp_status,
                    'errors': r.errors,
                    'warnings': r.warnings
                }
                for r in self.results
            ]
        }


class CryptoModuleValidator:
    """Validates cryptographic module definitions."""

    # FIPS 140-2 sunset date per FedRAMP policy
    FIPS_140_2_SUNSET = datetime(2026, 9, 21)

    # Warning threshold for expiring modules (90 days)
    EXPIRATION_WARNING_DAYS = 90

    def __init__(
        self,
        schema_path: Optional[Path] = None,
        cmvp_cache_path: Optional[Path] = None
    ):
        self.schema = None
        self.validator = None

        if schema_path and schema_path.exists() and Draft202012Validator:
            with open(schema_path) as f:
                self.schema = json.load(f)
            self.validator = Draft202012Validator(self.schema)

        self.cmvp_cache = {}
        if cmvp_cache_path:
            self._load_cmvp_cache(cmvp_cache_path)

    def _load_cmvp_cache(self, cache_path: Path):
        """Load all cached CMVP certificates."""
        cert_dir = cache_path / 'certificates'
        if not cert_dir.exists():
            cert_dir = cache_path  # Fallback to direct path

        for cache_file in cert_dir.glob('*.json'):
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                    # Handle both dict and list formats
                    if isinstance(data, dict):
                        self.cmvp_cache.update(data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {cache_file}: {e}", file=sys.stderr)

    def validate_module(self, module_path: Path) -> ValidationResult:
        """Validate a single module file."""
        try:
            with open(module_path) as f:
                module_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return ValidationResult(
                module_name='unknown',
                file_path=str(module_path),
                is_valid=False,
                errors=[f"YAML parse error: {e}"]
            )

        if not module_data:
            return ValidationResult(
                module_name='unknown',
                file_path=str(module_path),
                is_valid=False,
                errors=["Empty or invalid YAML file"]
            )

        module_name = module_data.get('metadata', {}).get('name', 'unknown')
        cert_number = module_data.get('spec', {}).get('validation', {}).get('certificateNumber')

        result = ValidationResult(
            module_name=module_name,
            file_path=str(module_path),
            is_valid=True,
            certificate_number=cert_number
        )

        # 1. Schema validation
        if self.validator:
            schema_errors = list(self.validator.iter_errors(module_data))
            for error in schema_errors[:10]:  # Limit to first 10 errors
                result.errors.append(f"Schema: {error.message}")
                result.is_valid = False

        if not result.is_valid:
            return result

        # 2. CMVP validation
        if cert_number:
            self._validate_cmvp(cert_number, module_data, result)

        # 3. FedRAMP policy validation
        self._validate_fedramp_policy(module_data, result)

        return result

    def _validate_cmvp(
        self,
        cert_number: int,
        module_data: dict,
        result: ValidationResult
    ):
        """Validate against CMVP cache."""
        cert_str = str(cert_number)

        if cert_str not in self.cmvp_cache:
            result.warnings.append(
                f"Certificate #{cert_number} not found in CMVP cache. "
                "Run cache update or verify certificate number."
            )
            return

        cached = self.cmvp_cache[cert_str]
        result.cmvp_status = cached.get('status')

        # Check certificate status
        if cached.get('status') == 'Revoked':
            result.errors.append(
                f"Certificate #{cert_number} has been REVOKED. "
                "This module must be replaced immediately."
            )
            result.is_valid = False
        elif cached.get('status') == 'Historical':
            result.warnings.append(
                f"Certificate #{cert_number} is HISTORICAL. "
                "Document in POA&M and plan for replacement per FedRAMP policy."
            )

        # Verify module name matches (if we have both)
        declared_name = module_data.get('spec', {}).get('module', {}).get('name')
        cached_name = cached.get('moduleName')
        if declared_name and cached_name:
            # Fuzzy match - check if key words match
            declared_words = set(declared_name.lower().split())
            cached_words = set(cached_name.lower().split())
            common_words = declared_words & cached_words
            if len(common_words) < 2 and declared_name.lower() != cached_name.lower():
                result.warnings.append(
                    f"Module name may not match CMVP record: "
                    f"declared='{declared_name}', CMVP='{cached_name}'"
                )

        # Check sunset date
        sunset_str = cached.get('sunsetDate')
        if sunset_str:
            try:
                sunset_date = datetime.strptime(sunset_str, '%Y-%m-%d')
                days_until_sunset = (sunset_date - datetime.now()).days

                if days_until_sunset < 0:
                    result.errors.append(
                        f"Certificate #{cert_number} sunset date ({sunset_str}) "
                        "has passed. Module validation has expired."
                    )
                    result.is_valid = False
                elif days_until_sunset < self.EXPIRATION_WARNING_DAYS:
                    result.warnings.append(
                        f"Certificate #{cert_number} expires in {days_until_sunset} days "
                        f"(sunset: {sunset_str}). Plan for renewal or replacement."
                    )
            except ValueError:
                pass  # Skip if date parsing fails

    def _validate_fedramp_policy(self, module_data: dict, result: ValidationResult):
        """Validate against FedRAMP-specific policies."""
        validation = module_data.get('spec', {}).get('validation', {})
        usage = module_data.get('spec', {}).get('usage', {})

        # Check FIPS 140-2 vs 140-3
        standard = validation.get('standard')
        if standard == 'FIPS 140-2':
            days_until_sunset = (self.FIPS_140_2_SUNSET - datetime.now()).days
            if days_until_sunset < 0:
                result.errors.append(
                    "FIPS 140-2 modules are no longer acceptable after September 21, 2026. "
                    "Migrate to a FIPS 140-3 validated module."
                )
                result.is_valid = False
            elif days_until_sunset < 180:
                result.warnings.append(
                    f"FIPS 140-2 acceptance ends in {days_until_sunset} days "
                    "(September 21, 2026). Plan migration to FIPS 140-3."
                )
            elif days_until_sunset < 365:
                result.warnings.append(
                    "FIPS 140-2 modules will not be acceptable after September 21, 2026. "
                    "Consider planning migration to FIPS 140-3."
                )

        # Verify required fields for inherited modules
        if usage.get('inherited') and not usage.get('inheritedFrom'):
            result.errors.append(
                "Inherited modules must specify 'inheritedFrom' with "
                "the FedRAMP package ID of the providing service."
            )
            result.is_valid = False

        # Check data classification completeness
        classifications = usage.get('dataClassification', [])
        if not classifications:
            result.warnings.append(
                "No data classification specified. "
                "Should indicate data-in-transit, data-at-rest, or data-in-use."
            )

        # Check for missing location
        if not usage.get('location'):
            result.warnings.append(
                "Module location not specified. "
                "Should indicate where the module is deployed in the system."
            )

        # Check for PPS references for DIT modules
        if 'data-in-transit' in classifications:
            pps_refs = module_data.get('spec', {}).get('portProtocolServiceRef', [])
            if not pps_refs:
                result.warnings.append(
                    "Data-in-Transit module should reference Ports/Protocols/Services "
                    "table entries via 'portProtocolServiceRef'."
                )

    def validate_all(self, modules_dir: Path) -> ValidationSummary:
        """Validate all modules in a directory."""
        summary = ValidationSummary()

        # Process .yaml files
        for module_file in modules_dir.glob('**/*.yaml'):
            if module_file.name.startswith('_'):
                continue  # Skip generated/internal files

            result = self.validate_module(module_file)
            summary.add_result(result)

        # Process .yml files
        for module_file in modules_dir.glob('**/*.yml'):
            if module_file.name.startswith('_'):
                continue

            result = self.validate_module(module_file)
            summary.add_result(result)

        return summary


def main():
    parser = argparse.ArgumentParser(
        description='Validate FedRAMP cryptographic module definitions'
    )
    parser.add_argument(
        '--schema',
        type=Path,
        default=Path('schemas/v1/crypto-module.schema.json'),
        help='Path to JSON Schema'
    )
    parser.add_argument(
        '--modules',
        type=Path,
        required=True,
        help='Path to modules directory'
    )
    parser.add_argument(
        '--cmvp-cache',
        type=Path,
        help='Path to CMVP cache directory'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=Path,
        help='Output file for JSON results'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'text', 'github-actions'],
        default='text',
        help='Output format'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )

    args = parser.parse_args()

    # Find schema relative to script location if not found at specified path
    schema_path = args.schema
    if not schema_path.exists():
        script_dir = Path(__file__).parent.parent
        schema_path = script_dir / args.schema
        if not schema_path.exists():
            print(f"Warning: Schema not found at {args.schema}", file=sys.stderr)
            schema_path = None

    # Find CMVP cache
    cmvp_cache_path = args.cmvp_cache
    if cmvp_cache_path and not cmvp_cache_path.exists():
        script_dir = Path(__file__).parent.parent
        cmvp_cache_path = script_dir / args.cmvp_cache
        if not cmvp_cache_path.exists():
            print(f"Warning: CMVP cache not found at {args.cmvp_cache}", file=sys.stderr)
            cmvp_cache_path = None

    validator = CryptoModuleValidator(
        schema_path=schema_path,
        cmvp_cache_path=cmvp_cache_path
    )

    summary = validator.validate_all(args.modules)

    # Apply strict mode
    if args.strict and summary.warnings_count > 0:
        for result in summary.results:
            if result.warnings:
                result.is_valid = False
                result.errors.extend([f"[Strict] {w}" for w in result.warnings])
        summary.invalid_modules = sum(1 for r in summary.results if not r.is_valid)
        summary.valid_modules = summary.total_modules - summary.invalid_modules

    # Output results
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(summary.to_dict(), f, indent=2)

    if args.format == 'text':
        print(f"\nValidation Summary")
        print(f"==================")
        print(f"Total Modules: {summary.total_modules}")
        print(f"Valid: {summary.valid_modules}")
        print(f"Invalid: {summary.invalid_modules}")
        print(f"Warnings: {summary.warnings_count}")

        if summary.invalid_modules > 0:
            print(f"\nErrors:")
            for result in summary.results:
                for error in result.errors:
                    print(f"  [{result.module_name}] {error}")

        if summary.warnings_count > 0:
            print(f"\nWarnings:")
            for result in summary.results:
                for warning in result.warnings:
                    print(f"  [{result.module_name}] {warning}")

    elif args.format == 'github-actions':
        # Output GitHub Actions annotations
        for result in summary.results:
            for error in result.errors:
                print(f"::error file={result.file_path}::{error}")
            for warning in result.warnings:
                print(f"::warning file={result.file_path}::{warning}")

        # Summary for GitHub Actions
        if summary.invalid_modules > 0:
            print(f"::error::Validation failed: {summary.invalid_modules} invalid module(s)")
        elif summary.warnings_count > 0:
            print(f"::warning::Validation passed with {summary.warnings_count} warning(s)")
        else:
            print(f"::notice::All {summary.total_modules} module(s) validated successfully")

    elif args.format == 'json':
        print(json.dumps(summary.to_dict(), indent=2))

    # Exit with error code if validation failed
    sys.exit(0 if summary.invalid_modules == 0 else 1)


if __name__ == '__main__':
    main()
