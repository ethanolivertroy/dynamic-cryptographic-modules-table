# FedRAMP Field Mapping

This document maps schema fields to FedRAMP Appendix Q requirements, NIST SP 800-53 controls, and assessment evidence needs.

---

## Appendix Q Column Mapping

The FedRAMP SSP Appendix Q table requires specific information about each cryptographic module. Here's how our schema fields map to those columns:

| Appendix Q Column | Schema Field | Notes |
|-------------------|--------------|-------|
| Module Name | `spec.module.name` | Must match CMVP certificate exactly |
| Vendor | `spec.module.vendor.name` | As registered with NIST CMVP |
| FIPS Certificate # | `spec.validation.certificateNumber` | Validated against CMVP database |
| FIPS 140 Level | `spec.validation.securityLevel` | 1, 2, 3, or 4 |
| Module Type | `spec.module.type` | hardware, software, firmware, hybrid |
| Software Version | `spec.module.versions.software` | If applicable |
| Firmware Version | `spec.module.versions.firmware` | If applicable |
| Hardware Version | `spec.module.versions.hardware` | If applicable |
| Data Classification | `spec.usage.dataClassification` | DIT, DAR, DIU |
| System Component | `spec.usage.location` | Where module is deployed |
| Use/Purpose | `spec.usage.purpose` | What data is protected |
| Inherited? | `spec.usage.inherited` | From CSP or customer-deployed |
| Inherited From | `spec.usage.inheritedFrom` | CSP package ID if inherited |

---

## NIST SP 800-53 Control Mapping

### SC-12: Cryptographic Key Establishment and Management

> *"The organization establishes and manages cryptographic keys when cryptography is employed within the system."*

| Schema Field | Evidence Provided |
|--------------|-------------------|
| `spec.module.name` | Identifies key management module |
| `spec.validation.certificateNumber` | Proves FIPS validation for key operations |
| `spec.validation.algorithms` | Documents approved key establishment algorithms |
| `spec.usage.location` | Shows where keys are managed |
| `spec.usage.inherited` | Clarifies key management responsibility |

**Assessment Questions Answered:**
- What FIPS-validated modules manage cryptographic keys?
- Are key management modules properly validated?
- Who is responsible for key management (CSP vs customer)?

### SC-13: Cryptographic Protection

> *"The system implements cryptographic mechanisms that comply with applicable laws, Executive Orders, directives, regulations, policies, standards, and guidelines."*

| Schema Field | Evidence Provided |
|--------------|-------------------|
| `spec.validation.standard` | FIPS 140-2 or FIPS 140-3 compliance |
| `spec.validation.certificateNumber` | CMVP validation proof |
| `spec.validation.securityLevel` | Appropriate strength for data sensitivity |
| `spec.validation.algorithms` | Approved cryptographic algorithms |
| `spec.usage.dataClassification` | What data is protected |
| `spec.usage.purpose` | How protection is applied |

**Assessment Questions Answered:**
- Are all cryptographic modules FIPS 140 validated?
- What algorithms are used for encryption?
- Is the security level appropriate for the data?

### SC-28: Protection of Information at Rest

> *"The system protects the confidentiality and integrity of information at rest."*

| Schema Field | Evidence Provided |
|--------------|-------------------|
| `spec.usage.dataClassification` | Must include `data-at-rest` (DAR) |
| `spec.usage.location` | Where DAR protection is applied |
| `spec.usage.purpose` | What stored data is protected |
| `spec.validation.certificateNumber` | FIPS validation for DAR module |

**Assessment Questions Answered:**
- What modules protect data at rest?
- Where is DAR encryption applied (volumes, databases, backups)?
- Are DAR modules FIPS 140 validated?

---

## Data Classification Mapping

### Data in Transit (DIT)

**FedRAMP Definition:** Data moving between system components or across network boundaries.

| Schema Value | Appendix Q Section | Typical Use Cases |
|--------------|-------------------|-------------------|
| `data-in-transit` | Data in Transit | TLS termination, VPN encryption, API encryption, database connections |

**Related Controls:** SC-8 (Transmission Confidentiality), SC-13

**Schema Example:**
```yaml
spec:
  usage:
    dataClassification:
      - data-in-transit
    location: "Load Balancer"
    purpose: "TLS 1.3 termination for HTTPS traffic"
```

### Data at Rest (DAR)

**FedRAMP Definition:** Data stored on persistent media (disks, databases, backups).

| Schema Value | Appendix Q Section | Typical Use Cases |
|--------------|-------------------|-------------------|
| `data-at-rest` | Data at Rest | Volume encryption, database TDE, object storage, backup encryption |

**Related Controls:** SC-28 (Protection of Information at Rest), SC-13

**Schema Example:**
```yaml
spec:
  usage:
    dataClassification:
      - data-at-rest
    location: "Database Server"
    purpose: "Transparent Data Encryption for PostgreSQL"
```

### Data in Use (DIU)

**FedRAMP Definition:** Data being actively processed in memory or compute.

| Schema Value | Appendix Q Section | Typical Use Cases |
|--------------|-------------------|-------------------|
| `data-in-use` | Data in Use | Memory encryption, secure enclaves, confidential computing |

**Related Controls:** SC-13, SA-8 (Security and Privacy Engineering Principles)

**Schema Example:**
```yaml
spec:
  usage:
    dataClassification:
      - data-in-use
    location: "Confidential VM"
    purpose: "AMD SEV memory encryption for sensitive workloads"
```

---

## FIPS 140 Field Mapping

### Validation Standard

| Schema Value | Meaning | FedRAMP Status |
|--------------|---------|----------------|
| `FIPS 140-3` | Current standard | **Preferred** |
| `FIPS 140-2` | Previous standard | **Acceptable until Sept 21, 2026** |

**Policy Reference:** [FedRAMP Policy for Cryptographic Module Selection](https://www.fedramp.gov/resources/documents/)

### Security Level

| Level | Physical Security | Use Case | FedRAMP Guidance |
|-------|------------------|----------|------------------|
| 1 | None required | Software modules | Acceptable for Moderate |
| 2 | Tamper evidence | Firmware/software | Recommended for High |
| 3 | Tamper resistance | Hardware/HSM | Required for key storage at High |
| 4 | Tamper active response | High-security HSM | Specialized use cases |

### Certificate Number

| Validation | Meaning | Action |
|------------|---------|--------|
| Number exists, status Active | Valid and current | None required |
| Number exists, status Historical | Validation expired | Document in POA&M |
| Number exists, status Revoked | Security issue found | **Immediate replacement** |
| Number not found | Invalid or typo | Verify against CMVP |

**CMVP Lookup:** https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/[NUMBER]

---

## FedRAMP Authorization Requirements

### Required Fields (Minimum for Authorization)

| Field | Requirement | Why |
|-------|-------------|-----|
| `metadata.name` | Unique identifier | Tracking and reference |
| `spec.module.name` | CMVP module name | Verification against NIST |
| `spec.module.vendor.name` | Vendor name | Verification against NIST |
| `spec.validation.certificateNumber` | CMVP cert # | Proof of validation |
| `spec.validation.standard` | FIPS 140-2/3 | Compliance verification |
| `spec.validation.securityLevel` | 1-4 | Strength assessment |
| `spec.usage.dataClassification` | DIT/DAR/DIU | Appendix Q categorization |
| `spec.usage.location` | Deployment location | System understanding |

### Recommended Fields (Assessment Evidence)

| Field | Benefit |
|-------|---------|
| `spec.module.versions.software` | Version tracking for patching |
| `spec.validation.algorithms` | Algorithm inventory for SC-13 |
| `spec.usage.purpose` | Clear documentation of use |
| `spec.portProtocolServiceRef` | Cross-reference to PPS table |
| `spec.usage.inherited` | Responsibility clarification |

### Inheritance Documentation

When modules are inherited from CSPs:

| Inheritance Type | Required Documentation |
|-----------------|----------------------|
| `full` | CSP FedRAMP package ID, Customer Responsibility Matrix reference |
| `partial` | CSP package ID, specific customer configuration documented |
| `none` | Full module documentation required |

**Schema Example (Inherited):**
```yaml
spec:
  usage:
    inherited: true
    inheritedFrom: "AWS FedRAMP High Package (FR1234567890)"
```

---

## Assessment Evidence Matrix

| Assessment Activity | Schema Fields Used | Evidence Generated |
|--------------------|-------------------|-------------------|
| Appendix Q Review | All `spec.*` fields | Complete module inventory |
| SC-12 Testing | `certificateNumber`, `algorithms` | Key management validation |
| SC-13 Testing | `certificateNumber`, `standard`, `algorithms` | Crypto compliance |
| SC-28 Testing | `dataClassification`, `location` | DAR coverage |
| Continuous Monitoring | `status.cmvpStatus` | Certificate status tracking |
| POA&M Management | `status.complianceStatus` | Non-compliant module tracking |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEDRAMP CRYPTO MODULE                         │
├─────────────────────────────────────────────────────────────────┤
│  APPENDIX Q FIELDS                                              │
│  ├── Module Name ──────── spec.module.name                      │
│  ├── Vendor ───────────── spec.module.vendor.name               │
│  ├── Certificate # ────── spec.validation.certificateNumber     │
│  ├── FIPS Level ───────── spec.validation.securityLevel         │
│  ├── Classification ───── spec.usage.dataClassification         │
│  └── Location ─────────── spec.usage.location                   │
├─────────────────────────────────────────────────────────────────┤
│  NIST CONTROLS                                                  │
│  ├── SC-12 ────────────── certificateNumber + key mgmt modules  │
│  ├── SC-13 ────────────── certificateNumber + algorithms        │
│  └── SC-28 ────────────── dataClassification: data-at-rest      │
├─────────────────────────────────────────────────────────────────┤
│  STATUS CHECKS                                                  │
│  ├── Active ───────────── OK                                    │
│  ├── Historical ───────── POA&M required                        │
│  └── Revoked ──────────── IMMEDIATE ACTION                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## References

- [FedRAMP SSP Template - Appendix Q](https://www.fedramp.gov/assets/resources/templates/)
- [NIST SP 800-53 Rev 5 - SC Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [NIST CMVP](https://csrc.nist.gov/projects/cryptographic-module-validation-program)
- [FedRAMP Cryptographic Module Selection Policy](https://www.fedramp.gov/resources/documents/)
- [FIPS 140-3 Standard](https://csrc.nist.gov/publications/detail/fips/140/3/final)
