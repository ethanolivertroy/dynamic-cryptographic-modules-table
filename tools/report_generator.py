#!/usr/bin/env python3
"""
FedRAMP Cryptographic Module Report Generator

Generates markdown and JSON reports from validation results.
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml


def load_modules(modules_dir: Path) -> dict:
    """Load all module definitions from directory."""
    modules = {}

    for yaml_file in modules_dir.glob('**/*.yaml'):
        if yaml_file.name.startswith('_'):
            continue
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
                if data and 'metadata' in data:
                    name = data['metadata'].get('name', yaml_file.stem)
                    modules[name] = {
                        'data': data,
                        'file': str(yaml_file)
                    }
        except (yaml.YAMLError, IOError):
            pass

    for yaml_file in modules_dir.glob('**/*.yml'):
        if yaml_file.name.startswith('_'):
            continue
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
                if data and 'metadata' in data:
                    name = data['metadata'].get('name', yaml_file.stem)
                    modules[name] = {
                        'data': data,
                        'file': str(yaml_file)
                    }
        except (yaml.YAMLError, IOError):
            pass

    return modules


def generate_markdown_report(
    validation_results: dict,
    modules: dict,
    output_path: Path
):
    """Generate a markdown report."""
    timestamp = validation_results.get('timestamp', datetime.utcnow().isoformat() + 'Z')

    lines = [
        "# Cryptographic Module Validation Report",
        "",
        f"**Generated:** {timestamp}  ",
        f"**Total Modules:** {validation_results.get('totalModules', 0)}",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total Modules | {validation_results.get('totalModules', 0)} |",
        f"| Compliant | {validation_results.get('validModules', 0)} |",
        f"| Non-Compliant | {validation_results.get('invalidModules', 0)} |",
        f"| Warnings | {validation_results.get('warningsCount', 0)} |",
        "",
    ]

    # Categorize results
    compliant = []
    action_required = []
    non_compliant = []

    for result in validation_results.get('results', []):
        if not result.get('valid'):
            non_compliant.append(result)
        elif result.get('warnings'):
            action_required.append(result)
        else:
            compliant.append(result)

    # Compliant modules section
    if compliant:
        lines.extend([
            "## Compliant Modules",
            "",
            "| Module | Certificate | Status | Standard |",
            "|--------|-------------|--------|----------|",
        ])
        for result in compliant:
            name = result.get('module', 'unknown')
            cert = result.get('certificateNumber', 'N/A')
            status = result.get('cmvpStatus', 'Unknown')

            # Get standard from module data
            standard = 'N/A'
            if name in modules:
                mod_data = modules[name].get('data', {})
                standard = mod_data.get('spec', {}).get('validation', {}).get('standard', 'N/A')

            lines.append(f"| {name} | #{cert} | {status} | {standard} |")
        lines.append("")

    # Action required section
    if action_required:
        lines.extend([
            "## Action Required (POA&M)",
            "",
            "| Module | Certificate | Status | Issue |",
            "|--------|-------------|--------|-------|",
        ])
        for result in action_required:
            name = result.get('module', 'unknown')
            cert = result.get('certificateNumber', 'N/A')
            status = result.get('cmvpStatus', 'Unknown')
            # Get first warning as the issue
            issue = result.get('warnings', ['No details'])[0][:80]
            lines.append(f"| {name} | #{cert} | {status} | {issue} |")
        lines.append("")

    # Non-compliant section
    if non_compliant:
        lines.extend([
            "## Non-Compliant (Immediate Action Required)",
            "",
            "| Module | Certificate | Issue |",
            "|--------|-------------|-------|",
        ])
        for result in non_compliant:
            name = result.get('module', 'unknown')
            cert = result.get('certificateNumber', 'N/A')
            # Get first error as the issue
            issue = result.get('errors', ['No details'])[0][:80]
            lines.append(f"| {name} | #{cert} | {issue} |")
        lines.append("")

    # Module inventory by data classification
    lines.extend([
        "---",
        "",
        "## Module Inventory by Data Classification",
        "",
    ])

    # Group modules by classification
    by_classification = defaultdict(list)
    for name, mod in modules.items():
        data = mod.get('data', {})
        classifications = data.get('spec', {}).get('usage', {}).get('dataClassification', [])
        for classification in classifications:
            by_classification[classification].append({
                'name': name,
                'cert': data.get('spec', {}).get('validation', {}).get('certificateNumber', 'N/A'),
                'purpose': data.get('spec', {}).get('usage', {}).get('purpose', 'N/A')
            })

    classification_labels = {
        'data-in-transit': 'Data in Transit (DIT)',
        'data-at-rest': 'Data at Rest (DAR)',
        'data-in-use': 'Data in Use (DIU)'
    }

    for classification, label in classification_labels.items():
        mods = by_classification.get(classification, [])
        lines.append(f"### {label}")
        lines.append("")
        if mods:
            for mod in mods:
                lines.append(f"- **{mod['name']}** (#{mod['cert']}) - {mod['purpose']}")
        else:
            lines.append("*No modules registered for this classification*")
        lines.append("")

    # Validation details
    lines.extend([
        "---",
        "",
        "## Validation Details",
        "",
        "<details>",
        "<summary>Full Validation Log (JSON)</summary>",
        "",
        "```json",
        json.dumps(validation_results, indent=2),
        "```",
        "",
        "</details>",
        "",
        "---",
        "",
        "## References",
        "",
        "- [NIST CMVP](https://csrc.nist.gov/projects/cryptographic-module-validation-program)",
        "- [FedRAMP Policy for Cryptographic Module Selection](https://www.fedramp.gov/resources/documents/)",
        "- [FIPS 140-3 Standard](https://csrc.nist.gov/publications/detail/fips/140/3/final)",
        "",
    ])

    # Write the report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"Report generated: {output_path}")


def generate_json_summary(
    validation_results: dict,
    modules: dict,
    output_path: Path
):
    """Generate a JSON summary report."""
    # Group modules by status
    by_status = {
        'compliant': [],
        'action_required': [],
        'non_compliant': []
    }

    for result in validation_results.get('results', []):
        name = result.get('module', 'unknown')
        module_data = modules.get(name, {}).get('data', {})

        entry = {
            'name': name,
            'certificateNumber': result.get('certificateNumber'),
            'cmvpStatus': result.get('cmvpStatus'),
            'standard': module_data.get('spec', {}).get('validation', {}).get('standard'),
            'dataClassification': module_data.get('spec', {}).get('usage', {}).get('dataClassification', []),
            'location': module_data.get('spec', {}).get('usage', {}).get('location'),
            'errors': result.get('errors', []),
            'warnings': result.get('warnings', [])
        }

        if not result.get('valid'):
            by_status['non_compliant'].append(entry)
        elif result.get('warnings'):
            by_status['action_required'].append(entry)
        else:
            by_status['compliant'].append(entry)

    summary = {
        'timestamp': validation_results.get('timestamp'),
        'summary': {
            'total': validation_results.get('totalModules', 0),
            'compliant': len(by_status['compliant']),
            'actionRequired': len(by_status['action_required']),
            'nonCompliant': len(by_status['non_compliant']),
            'warnings': validation_results.get('warningsCount', 0)
        },
        'modules': by_status
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"JSON summary generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate compliance reports from validation results'
    )
    parser.add_argument(
        '--validation-results',
        type=Path,
        required=True,
        help='Path to validation results JSON file'
    )
    parser.add_argument(
        '--modules',
        type=Path,
        required=True,
        help='Path to modules directory'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=Path,
        default=Path('reports/latest/validation-summary.md'),
        help='Output path for markdown report'
    )
    parser.add_argument(
        '--json-output',
        type=Path,
        help='Output path for JSON summary (optional)'
    )

    args = parser.parse_args()

    # Load validation results
    with open(args.validation_results) as f:
        validation_results = json.load(f)

    # Load modules
    modules = load_modules(args.modules)

    # Generate markdown report
    generate_markdown_report(validation_results, modules, args.output)

    # Generate JSON summary if requested
    if args.json_output:
        generate_json_summary(validation_results, modules, args.json_output)
    else:
        # Default JSON output next to markdown
        json_output = args.output.with_suffix('.json')
        generate_json_summary(validation_results, modules, json_output)


if __name__ == '__main__':
    main()
