# Validation Rules

The validation system checks modules against three categories of rules.

## Validation Categories

### 1. Schema Validation

Structural validation against the JSON Schema.

**Checked:**
- Required fields present
- Field types correct
- Enum values valid
- UUID format valid
- Date formats valid

**Exit Code:** 1

### 2. CMVP Validation

Certificate status from NIST CMVP cache.

**Checked:**
- Certificate number exists in CMVP database
- Certificate status (Active, Historical, Revoked)
- Module name matches CMVP record
- Vendor name matches CMVP record

**Exit Code:** 2

### 3. FedRAMP Policy Validation

Compliance with FedRAMP cryptographic policies.

**Checked:**
- FIPS 140-2 sunset date compliance
- Security level requirements
- Inherited module documentation
- Data classification consistency

**Exit Code:** 3

## CMVP Status Rules

| Status | Result | Action Required |
|--------|--------|-----------------|
| Active | PASS | None |
| Historical | WARNING | Document in POA&M, plan migration |
| Revoked | ERROR | Immediate replacement required |
| Not Found | ERROR | Verify certificate number |

### Active

Module is currently validated and in good standing.

```
Certificate #4282: Active
```

### Historical

Module validation has expired but was not revoked. Still usable but migration should be planned.

```
WARNING: Certificate #3245 status is 'Historical'
  - Original validation: 2020-06-15
  - Consider migrating to an Active certificate
```

### Revoked

Module has been revoked due to security issues. **Must be replaced immediately.**

```
ERROR: Certificate #1234 status is 'Revoked'
  - Revocation date: 2024-01-15
  - Immediate action required
```

## FedRAMP Policy Rules

### FIPS 140-2 Sunset

Per [FedRAMP Policy](https://www.fedramp.gov/resources/documents/FedRAMP_Policy_for_Cryptographic_Module_Selection_v1.1.0.pdf), FIPS 140-2 modules sunset on **September 21, 2026**.

| Condition | Result | Message |
|-----------|--------|---------|
| FIPS 140-3 | PASS | - |
| FIPS 140-2, > 90 days until sunset | WARNING | Plan migration |
| FIPS 140-2, < 90 days until sunset | ERROR | Urgent migration needed |
| FIPS 140-2, after sunset | ERROR | Non-compliant |

```
WARNING: Certificate #2847 uses FIPS 140-2
  - Sunset date: 2026-09-21
  - Days remaining: 654
  - Action: Plan migration to FIPS 140-3 module
```

### Inherited Module Requirements

Modules inherited from CSPs require documentation.

```yaml
spec:
  usage:
    inheritance:
      type: full
      provider: "AWS"
      documentation: "AWS FedRAMP Package - Customer Responsibility Matrix"
```

| Inheritance Type | Validation |
|-----------------|------------|
| `none` | Full validation required |
| `partial` | Documentation reference required |
| `full` | Documentation reference required |

### Security Level Requirements

| Data Sensitivity | Minimum Level |
|-----------------|---------------|
| Low | 1 |
| Moderate | 1 |
| High | 2+ recommended |

## CI/CD Integration

### Exit Codes

| Code | Meaning | PR Action |
|------|---------|-----------|
| 0 | All passed | Allow merge |
| 1 | Schema errors | Block merge |
| 2 | CMVP issues | Block merge |
| 3 | Policy violations | Block merge |

### GitHub Actions Example

```yaml
- name: Validate Modules
  run: |
    python tools/validate.py modules/ --output json > validation.json
  continue-on-error: true

- name: Check Results
  run: |
    if [ $? -ne 0 ]; then
      echo "Validation failed"
      exit 1
    fi
```

### PR Comments

The validation workflow posts results as PR comments:

```markdown
## Cryptographic Module Validation

| Status | Count |
|--------|-------|
| Passed | 12 |
| Warnings | 2 |
| Errors | 1 |

### Errors
- `legacy-vpn.yaml`: Certificate #1234 status is 'Revoked'

### Warnings
- `app-tls.yaml`: FIPS 140-2 sunset approaching (654 days)
```

## Validation Output

### Human-Readable (default)

```
Validating modules in: modules/

[PASS] openssl-fips-provider.yaml
[WARN] legacy-tls.yaml
  - FIPS 140-2 sunset: 2026-09-21 (654 days remaining)
[FAIL] broken-module.yaml
  - Missing required field: spec.validation.certificateNumber

=====================================
Results: 2 passed, 1 warning, 1 failed
```

### JSON Output

```json
{
  "summary": {
    "total": 3,
    "passed": 2,
    "warnings": 1,
    "errors": 1
  },
  "results": [
    {
      "file": "openssl-fips-provider.yaml",
      "status": "pass",
      "errors": [],
      "warnings": []
    },
    {
      "file": "legacy-tls.yaml",
      "status": "warning",
      "errors": [],
      "warnings": [
        {
          "code": "FIPS_140_2_SUNSET",
          "message": "FIPS 140-2 sunset: 2026-09-21",
          "field": "spec.validation.standard"
        }
      ]
    }
  ]
}
```

## Suppressing Warnings

For documented exceptions, use annotations:

```yaml
metadata:
  annotations:
    suppress-warnings: "FIPS_140_2_SUNSET"
    suppression-justification: "Migration planned for Q2 2026, tracked in POAM-123"
```

**Note:** Errors cannot be suppressed. Revoked certificates and missing required fields always fail validation.
