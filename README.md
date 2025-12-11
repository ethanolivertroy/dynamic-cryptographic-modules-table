# FedRAMP Cryptographic Modules Table

Git-versioned, automatically validated tracking for FedRAMP Appendix Q cryptographic modules.

## Overview

This repository replaces static DOCX-based Appendix Q tables with a dynamic, version-controlled system that:

- **Validates** module definitions against JSON Schema
- **Checks** CMVP certificate status against NIST data
- **Enforces** FedRAMP cryptographic module policies
- **Generates** compliance reports automatically

Aligned with [FedRAMP 20x](https://www.fedramp.gov/20x/core-concepts/) principles: Transparency, Flexibility, Accountability, Accuracy, and Automatic Validation.

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd fedramp-crypto-modules

# Install dependencies
pip install -r tools/requirements.txt
```

### Define a Cryptographic Module

Create a YAML file in the appropriate `modules/` subdirectory:

```yaml
# modules/data-in-transit/api-tls.yaml
apiVersion: fedramp20x-poc/v1
kind: CryptographicModule
metadata:
  name: api-tls-encryption
  uuid: <generate-uuid>
  labels:
    data-classification:
      - DIT
spec:
  module:
    name: "OpenSSL FIPS Provider"
    vendor:
      name: "OpenSSL Software Foundation"
    type: software
    versions:
      software: "3.0.8"
  validation:
    standard: "FIPS 140-3"
    certificateNumber: 4282
    securityLevel: 1
  usage:
    dataClassification:
      - data-in-transit
    location: "API Gateway"
    purpose: "TLS 1.3 encryption for API endpoints"
```

### Validate Modules

```bash
# Validate all modules
python tools/validate.py modules/

# Validate a specific file
python tools/validate.py modules/data-in-transit/api-tls.yaml

# JSON output for CI
python tools/validate.py modules/ --output json
```

### Convert Between YAML and JSON

```bash
# YAML to JSON
python tools/convert.py modules/data-in-transit/api-tls.yaml --to json

# Batch convert directory
python tools/convert.py modules/ --to json --output-dir modules/_generated/
```

### Generate Reports

```bash
# Generate compliance report
python tools/report_generator.py --input modules/ --output reports/latest/
```

## Directory Structure

```
.
├── .github/workflows/     # CI/CD pipelines
│   ├── validate-modules.yml    # Validation on push/PR
│   ├── update-cmvp-cache.yml   # Weekly CMVP data refresh
│   └── generate-reports.yml    # Report generation
├── schemas/v1/            # JSON Schema definitions
│   ├── crypto-module.schema.json
│   └── cmvp-cache.schema.json
├── modules/               # Your module definitions (YAML)
│   ├── data-in-transit/   # DIT modules
│   ├── data-at-rest/      # DAR modules
│   ├── data-in-use/       # DIU modules
│   └── _generated/        # Auto-generated JSON
├── cmvp-cache/            # Cached NIST CMVP data
├── tools/                 # Python utilities
├── examples/              # Example module definitions
├── reports/               # Generated compliance reports
└── docs/                  # Documentation
```

## GitHub Actions

### Validation Workflow

Runs on every push and pull request:
- YAML linting
- JSON Schema validation
- CMVP certificate status checks
- FedRAMP policy compliance

Failed validations block PR merges.

### Cache Update Workflow

Runs weekly to refresh CMVP certificate data from NIST. Can be triggered manually.

### Report Generation

Generates markdown and JSON compliance reports after validation.

## Documentation

- [Getting Started](docs/getting-started.md)
- [Schema Reference](docs/schema-reference.md)
- [Validation Rules](docs/validation-rules.md)
- [FedRAMP Compliance](docs/fedramp-compliance.md)

## Validation Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | Schema validation errors |
| 2 | CMVP certificate issues (revoked/expired) |
| 3 | FedRAMP policy violations |

## License

MIT
