#!/usr/bin/env python3
"""
YAML <-> JSON Converter for FedRAMP Cryptographic Modules

Follows Kubernetes patterns: YAML as canonical source, JSON for tooling.
Supports:
- Single file conversion
- Batch directory conversion
- Schema validation during conversion
"""

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Optional, Union

import yaml

try:
    from jsonschema import Draft202012Validator, ValidationError
except ImportError:
    Draft202012Validator = None
    ValidationError = Exception


class CryptoModuleConverter:
    """Handles bidirectional YAML/JSON conversion with validation."""

    def __init__(self, schema_path: Optional[Path] = None):
        self.schema = None
        self.validator = None

        if schema_path and schema_path.exists() and Draft202012Validator:
            with open(schema_path) as f:
                self.schema = json.load(f)
            self.validator = Draft202012Validator(self.schema)

    def yaml_to_json(
        self,
        yaml_content: str,
        validate: bool = True
    ) -> dict:
        """Convert YAML string to JSON-compatible dict."""
        data = yaml.safe_load(yaml_content)

        if validate and self.validator:
            errors = list(self.validator.iter_errors(data))
            if errors:
                error_msgs = [e.message for e in errors[:5]]  # Limit to first 5
                raise ValidationError(f"Validation failed: {error_msgs}")

        return data

    def json_to_yaml(
        self,
        json_content: Union[str, dict],
        validate: bool = True
    ) -> str:
        """Convert JSON to YAML string."""
        if isinstance(json_content, str):
            data = json.loads(json_content)
        else:
            data = json_content

        if validate and self.validator:
            errors = list(self.validator.iter_errors(data))
            if errors:
                error_msgs = [e.message for e in errors[:5]]
                raise ValidationError(f"Validation failed: {error_msgs}")

        return yaml.dump(
            data,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120
        )

    def convert_file(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        validate: bool = True
    ) -> Path:
        """Convert a single file, auto-detecting format."""
        suffix = input_path.suffix.lower()

        with open(input_path) as f:
            content = f.read()

        if suffix in ['.yaml', '.yml']:
            data = self.yaml_to_json(content, validate=validate)
            result = json.dumps(data, indent=2, ensure_ascii=False)
            out_suffix = '.json'
        elif suffix == '.json':
            result = self.json_to_yaml(content, validate=validate)
            out_suffix = '.yaml'
        else:
            raise ValueError(f"Unknown file type: {suffix}")

        if output_path is None:
            output_path = input_path.with_suffix(out_suffix)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(result)

        return output_path

    def batch_convert(
        self,
        input_dir: Path,
        output_dir: Path,
        to_format: str = 'json',
        validate: bool = True
    ) -> list:
        """Convert all files in a directory."""
        converted = []
        pattern = '*.yaml' if to_format == 'json' else '*.json'
        alt_pattern = '*.yml' if to_format == 'json' else None

        output_dir.mkdir(parents=True, exist_ok=True)

        for input_file in input_dir.glob(f'**/{pattern}'):
            if input_file.name.startswith('_'):
                continue  # Skip internal/generated files

            rel_path = input_file.relative_to(input_dir)
            new_suffix = '.json' if to_format == 'json' else '.yaml'
            output_file = output_dir / rel_path.with_suffix(new_suffix)

            try:
                self.convert_file(input_file, output_file, validate=validate)
                converted.append(output_file)
                print(f"  Converted: {input_file} -> {output_file}")
            except Exception as e:
                print(f"  Error converting {input_file}: {e}", file=sys.stderr)

        # Also process .yml files if converting to JSON
        if alt_pattern:
            for input_file in input_dir.glob(f'**/{alt_pattern}'):
                if input_file.name.startswith('_'):
                    continue

                rel_path = input_file.relative_to(input_dir)
                output_file = output_dir / rel_path.with_suffix('.json')

                try:
                    self.convert_file(input_file, output_file, validate=validate)
                    converted.append(output_file)
                    print(f"  Converted: {input_file} -> {output_file}")
                except Exception as e:
                    print(f"  Error converting {input_file}: {e}", file=sys.stderr)

        return converted

    def merge_to_single_file(
        self,
        input_dir: Path,
        output_file: Path,
        validate: bool = True
    ) -> int:
        """Merge all YAML modules into a single JSON file."""
        modules = []

        for yaml_file in input_dir.glob('**/*.yaml'):
            if yaml_file.name.startswith('_'):
                continue

            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)

                if validate and self.validator:
                    errors = list(self.validator.iter_errors(data))
                    if errors:
                        print(f"  Skipping {yaml_file}: validation errors", file=sys.stderr)
                        continue

                data['_source'] = str(yaml_file)
                modules.append(data)
            except Exception as e:
                print(f"  Error reading {yaml_file}: {e}", file=sys.stderr)

        # Also process .yml files
        for yaml_file in input_dir.glob('**/*.yml'):
            if yaml_file.name.startswith('_'):
                continue

            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)

                if validate and self.validator:
                    errors = list(self.validator.iter_errors(data))
                    if errors:
                        print(f"  Skipping {yaml_file}: validation errors", file=sys.stderr)
                        continue

                data['_source'] = str(yaml_file)
                modules.append(data)
            except Exception as e:
                print(f"  Error reading {yaml_file}: {e}", file=sys.stderr)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({
                'apiVersion': 'fedramp.gov/v1',
                'kind': 'CryptographicModuleList',
                'items': modules
            }, f, indent=2, ensure_ascii=False)

        return len(modules)


def generate_uuid() -> str:
    """Generate a new UUID for a module."""
    return str(uuid.uuid4())


def main():
    parser = argparse.ArgumentParser(
        description='Convert FedRAMP crypto module files between YAML and JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  python convert.py module.yaml -o module.json

  # Batch convert directory to JSON
  python convert.py modules/ -o modules/_generated -f json

  # Merge all modules into single JSON file
  python convert.py modules/ --merge -o modules/_generated/all-modules.json

  # Generate new UUID
  python convert.py --generate-uuid
"""
    )
    parser.add_argument('input', type=Path, nargs='?', help='Input file or directory')
    parser.add_argument('-o', '--output', type=Path, help='Output file/directory')
    parser.add_argument(
        '-f', '--format',
        choices=['yaml', 'json'],
        help='Target format (for batch conversion)'
    )
    parser.add_argument(
        '-s', '--schema',
        type=Path,
        default=Path('schemas/v1/crypto-module.schema.json'),
        help='JSON Schema for validation'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip schema validation'
    )
    parser.add_argument(
        '--merge',
        action='store_true',
        help='Merge all modules into a single JSON file'
    )
    parser.add_argument(
        '--generate-uuid',
        action='store_true',
        help='Generate a new UUID and exit'
    )

    args = parser.parse_args()

    if args.generate_uuid:
        print(generate_uuid())
        return

    if not args.input:
        parser.error("input is required unless using --generate-uuid")

    # Find schema relative to script location if not found at specified path
    schema_path = args.schema
    if not schema_path.exists():
        script_dir = Path(__file__).parent.parent
        schema_path = script_dir / args.schema

    converter = CryptoModuleConverter(
        schema_path=schema_path if not args.no_validate else None
    )

    if args.merge:
        if not args.output:
            args.output = args.input / '_generated' / 'all-modules.json'
        count = converter.merge_to_single_file(
            args.input,
            args.output,
            validate=not args.no_validate
        )
        print(f"Merged {count} modules into {args.output}")
    elif args.input.is_dir():
        if not args.format:
            print("Error: --format required for directory conversion", file=sys.stderr)
            sys.exit(1)
        converted = converter.batch_convert(
            args.input,
            args.output or args.input / '_generated',
            args.format,
            validate=not args.no_validate
        )
        print(f"Converted {len(converted)} files")
    else:
        output = converter.convert_file(
            args.input,
            args.output,
            validate=not args.no_validate
        )
        print(f"Converted: {args.input} -> {output}")


if __name__ == '__main__':
    main()
