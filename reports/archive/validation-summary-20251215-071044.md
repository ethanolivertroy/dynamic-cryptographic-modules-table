# Cryptographic Module Validation Report

**Generated:** 2025-12-15T07:10:44.549781Z  
**Total Modules:** 3

---

## Summary

| Metric | Count |
|--------|-------|
| Total Modules | 3 |
| Compliant | 3 |
| Non-Compliant | 0 |
| Warnings | 2 |

## Compliant Modules

| Module | Certificate | Status | Standard |
|--------|-------------|--------|----------|
| aws-kms-hsm | #4523 | Active | FIPS 140-3 |
| openssl-fips-provider | #4282 | Active | FIPS 140-3 |

## Action Required (POA&M)

| Module | Certificate | Status | Issue |
|--------|-------------|--------|-------|
| legacy-tls-library | #2345 | Historical | Certificate #2345 is HISTORICAL. Document in POA&M and plan for replacement per  |

---

## Module Inventory by Data Classification

### Data in Transit (DIT)

- **legacy-tls-library** (#2345) - TLS encryption for legacy application - migration planned
- **openssl-fips-provider** (#4282) - TLS 1.3 encryption for API endpoints

### Data at Rest (DAR)

- **aws-kms-hsm** (#4523) - Envelope encryption key management for data at rest

### Data in Use (DIU)

*No modules registered for this classification*

---

## Validation Details

<details>
<summary>Full Validation Log (JSON)</summary>

```json
{
  "timestamp": "2025-12-15T07:10:44.549781Z",
  "totalModules": 3,
  "validModules": 3,
  "invalidModules": 0,
  "warningsCount": 2,
  "errors": [],
  "warnings": [
    {
      "module": "legacy-tls-library",
      "file": "modules/data-in-transit/legacy-tls-library.yaml",
      "message": "Certificate #2345 is HISTORICAL. Document in POA&M and plan for replacement per FedRAMP policy."
    },
    {
      "module": "legacy-tls-library",
      "file": "modules/data-in-transit/legacy-tls-library.yaml",
      "message": "FIPS 140-2 modules will not be acceptable after September 21, 2026. Consider planning migration to FIPS 140-3."
    }
  ],
  "results": [
    {
      "module": "aws-kms-hsm",
      "file": "modules/data-at-rest/aws-kms.yaml",
      "valid": true,
      "certificateNumber": 4523,
      "cmvpStatus": "Active",
      "errors": [],
      "warnings": []
    },
    {
      "module": "legacy-tls-library",
      "file": "modules/data-in-transit/legacy-tls-library.yaml",
      "valid": true,
      "certificateNumber": 2345,
      "cmvpStatus": "Historical",
      "errors": [],
      "warnings": [
        "Certificate #2345 is HISTORICAL. Document in POA&M and plan for replacement per FedRAMP policy.",
        "FIPS 140-2 modules will not be acceptable after September 21, 2026. Consider planning migration to FIPS 140-3."
      ]
    },
    {
      "module": "openssl-fips-provider",
      "file": "modules/data-in-transit/openssl-fips-provider.yaml",
      "valid": true,
      "certificateNumber": 4282,
      "cmvpStatus": "Active",
      "errors": [],
      "warnings": []
    }
  ]
}
```

</details>

---

## References

- [NIST CMVP](https://csrc.nist.gov/projects/cryptographic-module-validation-program)
- [FedRAMP Policy for Cryptographic Module Selection](https://www.fedramp.gov/resources/documents/)
- [FIPS 140-3 Standard](https://csrc.nist.gov/publications/detail/fips/140/3/final)
