# FedRAMP Compliance

How this system maps to FedRAMP Appendix Q requirements.

## Appendix Q Overview

FedRAMP System Security Plans (SSPs) require **Appendix Q: Cryptographic Modules Table** documenting all FIPS 140 validated cryptographic modules used in the system.

Traditional format: Static table in Word/Excel document.

This system: Git-versioned YAML with automated validation.

## Data Classification Categories

### Data in Transit (DIT)

Encryption protecting data as it moves between systems.

**Examples:**
- TLS/SSL for HTTPS
- VPN encryption
- API gateway encryption
- Database connection encryption
- Message queue encryption

**Schema mapping:**
```yaml
spec:
  usage:
    dataClassification:
      - data-in-transit
```

### Data at Rest (DAR)

Encryption protecting stored data.

**Examples:**
- Volume/disk encryption
- Database encryption (TDE)
- Object storage encryption
- Backup encryption
- Key storage (HSM/KMS)

**Schema mapping:**
```yaml
spec:
  usage:
    dataClassification:
      - data-at-rest
```

### Data in Use (DIU)

Encryption protecting data during processing.

**Examples:**
- Memory encryption
- Secure enclaves (SGX, SEV)
- Confidential computing
- Trusted execution environments

**Schema mapping:**
```yaml
spec:
  usage:
    dataClassification:
      - data-in-use
```

## Appendix Q Field Mapping

| Appendix Q Column | Schema Field |
|-------------------|--------------|
| Module Name | `spec.module.name` |
| Vendor | `spec.module.vendor.name` |
| FIPS Certificate # | `spec.validation.certificateNumber` |
| FIPS Level | `spec.validation.securityLevel` |
| Module Type | `spec.module.type` |
| Software Version | `spec.module.versions.software` |
| Firmware Version | `spec.module.versions.firmware` |
| Data Classification | `spec.usage.dataClassification` |
| Location/Component | `spec.usage.location` |
| Purpose | `spec.usage.purpose` |
| PPS Reference | `spec.portProtocolServiceRef` |

## Port Protocol Service (PPS) Integration

Link cryptographic modules to your SSP's Ports, Protocols, and Services table.

```yaml
spec:
  portProtocolServiceRef:
    - pps-001    # HTTPS 443
    - pps-002    # SSH 22
    - pps-003    # Database 5432
```

These references should match IDs in your SSP's PPS appendix.

## Inheritance

FedRAMP allows inheritance of cryptographic modules from underlying CSPs.

### Full Inheritance

CSP provides and manages the module. Customer has no visibility or control.

```yaml
spec:
  usage:
    inheritance:
      type: full
      provider: "AWS"
      documentation: "AWS FedRAMP High Authorization Package"
```

**Examples:**
- AWS S3 server-side encryption
- Azure Storage Service Encryption
- GCP default encryption

### Partial Inheritance

CSP provides the module; customer configures and manages it.

```yaml
spec:
  usage:
    inheritance:
      type: partial
      provider: "AWS"
      documentation: "AWS KMS Customer Responsibility Matrix"
```

**Examples:**
- AWS KMS customer-managed keys
- Azure Key Vault
- GCP Cloud KMS

### No Inheritance

Customer deploys and manages the module entirely.

```yaml
spec:
  usage:
    inheritance:
      type: none
```

**Examples:**
- Self-hosted HSM
- Application-embedded crypto libraries
- Custom TLS termination

## FedRAMP 20x Alignment

This system implements [FedRAMP 20x](https://www.fedramp.gov/20x/core-concepts/) principles:

### Transparency

- All module definitions visible in Git history
- Changes tracked with full audit trail
- Validation results public in PR comments

### Flexibility

- YAML format easily edited
- Schema extensible for custom fields
- Multiple output formats (YAML, JSON, Markdown)

### Accountability

- Git history shows who changed what and when
- PR reviews required for changes
- Validation blocks non-compliant changes

### Accuracy

- Schema validation catches errors
- CMVP cache ensures certificate numbers are valid
- Automated checks prevent stale data

### Automatic Validation

- GitHub Actions validate on every PR
- Daily scheduled checks for certificate status changes
- Weekly CMVP cache refresh

## Required vs Optional Fields

### Required for FedRAMP

| Field | Reason |
|-------|--------|
| `metadata.name` | Unique identification |
| `spec.module.name` | CMVP module name |
| `spec.module.vendor.name` | CMVP vendor |
| `spec.validation.certificateNumber` | CMVP verification |
| `spec.validation.standard` | FIPS 140-2 or 140-3 |
| `spec.validation.securityLevel` | Security assurance |
| `spec.usage.dataClassification` | Appendix Q categorization |
| `spec.usage.location` | Where module is deployed |
| `spec.usage.purpose` | What data is protected |

### Recommended

| Field | Reason |
|-------|--------|
| `spec.module.versions.software` | Version tracking |
| `spec.validation.validationDate` | Currency verification |
| `spec.portProtocolServiceRef` | PPS cross-reference |
| `spec.usage.inheritance` | CSP responsibility |

### Optional

| Field | Reason |
|-------|--------|
| `spec.validation.algorithms` | Detailed compliance |
| `spec.validation.caveatText` | Special conditions |
| `metadata.annotations` | Internal tracking |

## Generating Appendix Q

Export to traditional Appendix Q format:

```bash
python tools/report_generator.py \
  --input modules/ \
  --output reports/latest/ \
  --format appendix-q
```

Output includes:
- `appendix-q.md` - Markdown table for SSP
- `appendix-q.json` - Structured data for automation
- `appendix-q.csv` - Spreadsheet import

## Assessor Guidance

For 3PAO assessors reviewing systems using this tool:

1. **Verify automation**: Check GitHub Actions logs for validation runs
2. **Review history**: `git log modules/` shows change history
3. **Check cache freshness**: `cmvp-cache/metadata.json` shows last update
4. **Validate live**: Run `python tools/validate.py modules/` during assessment
5. **Cross-reference**: Match certificate numbers against [NIST CMVP](https://csrc.nist.gov/projects/cryptographic-module-validation-program)

## References

- [FedRAMP SSP Template](https://www.fedramp.gov/assets/resources/templates/FedRAMP-SSP-High-Baseline-Template.docx)
- [NIST CMVP](https://csrc.nist.gov/projects/cryptographic-module-validation-program)
- [FedRAMP Cryptographic Module Selection Policy](https://www.fedramp.gov/resources/documents/FedRAMP_Policy_for_Cryptographic_Module_Selection_v1.1.0.pdf)
- [FIPS 140-3](https://csrc.nist.gov/publications/detail/fips/140/3/final)
- [FedRAMP 20x Core Concepts](https://www.fedramp.gov/20x/core-concepts/)
