# Getting Started

This guide walks through setting up and using the FedRAMP Cryptographic Modules tracking system.

## Prerequisites

- Python 3.10 or higher
- pip package manager
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fedramp-crypto-modules
```

### 2. Install Python Dependencies

```bash
pip install -r tools/requirements.txt
```

This installs:
- `PyYAML`, `ruamel.yaml` - YAML processing
- `jsonschema` - Schema validation
- `aiohttp` - Async HTTP for CMVP scraping
- `beautifulsoup4` - HTML parsing
- `rich` - Terminal output formatting

### 3. Verify Installation

```bash
python tools/validate.py --help
```

## Creating Your First Module

### 1. Choose the Data Classification

Modules are organized by data classification:
- `modules/data-in-transit/` - Encryption for data moving between systems
- `modules/data-at-rest/` - Encryption for stored data
- `modules/data-in-use/` - Encryption for data being processed

### 2. Create a YAML File

Create a new file, e.g., `modules/data-in-transit/my-tls-module.yaml`:

```yaml
apiVersion: fedramp20x-poc/v1
kind: CryptographicModule
metadata:
  name: my-tls-module
  uuid: 12345678-1234-1234-1234-123456789abc
  labels:
    data-classification:
      - DIT
    environment: production
spec:
  module:
    name: "BoringSSL"
    vendor:
      name: "Google LLC"
    type: software
    versions:
      software: "latest"
  validation:
    standard: "FIPS 140-3"
    certificateNumber: 4407
    securityLevel: 1
    validationDate: "2024-03-15"
  usage:
    dataClassification:
      - data-in-transit
    location: "Load Balancer"
    purpose: "TLS termination for incoming HTTPS traffic"
  portProtocolServiceRef:
    - pps-001
```

### 3. Generate a UUID

Use any UUID generator:

```bash
python -c "import uuid; print(uuid.uuid4())"
# or
uuidgen
```

### 4. Find Your Certificate Number

Look up your cryptographic module on the [NIST CMVP](https://csrc.nist.gov/projects/cryptographic-module-validation-program/validated-modules/search) website to find the certificate number.

## Running Validation

### Validate All Modules

```bash
python tools/validate.py modules/
```

### Validate a Single File

```bash
python tools/validate.py modules/data-in-transit/my-tls-module.yaml
```

### Output Formats

```bash
# Human-readable (default)
python tools/validate.py modules/

# JSON for CI/CD
python tools/validate.py modules/ --output json

# Verbose mode
python tools/validate.py modules/ -v
```

## Understanding Validation Results

### Success

```
Validation Results
==================
Total modules: 3
Passed: 3
Failed: 0
Warnings: 1

Warnings:
- my-tls-module.yaml: Certificate #4407 uses FIPS 140-2 (sunset: 2026-09-21)
```

### Failure

```
Validation Results
==================
Total modules: 3
Passed: 2
Failed: 1

Errors:
- broken-module.yaml: Missing required field 'spec.validation.certificateNumber'
- broken-module.yaml: Certificate #1234 status is 'Revoked'
```

## Setting Up GitHub Actions

### 1. Enable Workflows

The repository includes pre-configured workflows in `.github/workflows/`. They are disabled by default in template repositories.

To enable:
1. Go to your repository's Actions tab
2. Enable workflows

### 2. Configure Permissions

For the cache update workflow to commit changes:
1. Go to Settings > Actions > General
2. Under "Workflow permissions", select "Read and write permissions"

### 3. Trigger Manual Runs

- **Update CMVP Cache**: Actions > Update CMVP Cache > Run workflow
- **Generate Reports**: Actions > Generate Compliance Reports > Run workflow

## Converting Files

### YAML to JSON

```bash
# Single file
python tools/convert.py modules/data-in-transit/my-module.yaml --to json

# Directory (outputs to modules/_generated/)
python tools/convert.py modules/ --to json --output-dir modules/_generated/
```

### JSON to YAML

```bash
python tools/convert.py modules/_generated/my-module.json --to yaml
```

## Generating Reports

```bash
python tools/report_generator.py \
  --input modules/ \
  --output reports/latest/ \
  --format markdown
```

Output files:
- `reports/latest/compliance-report.md` - Human-readable report
- `reports/latest/compliance-report.json` - Machine-readable data

## Next Steps

- [Schema Reference](schema-reference.md) - All available fields
- [Validation Rules](validation-rules.md) - What gets checked
- [FedRAMP Compliance](fedramp-compliance.md) - Appendix Q mapping
