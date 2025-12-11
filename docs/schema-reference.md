# Schema Reference

Complete reference for the CryptographicModule schema (v1).

## Top-Level Structure

```yaml
apiVersion: fedramp20x-poc/v1  # Required
kind: CryptographicModule       # Required
metadata: {}                    # Required
spec: {}                        # Required
status: {}                      # Optional (auto-populated)
```

## metadata

Module identification and labels.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier (lowercase, alphanumeric, hyphens) |
| `uuid` | string | Yes | UUID v4 for tracking |
| `labels` | object | No | Key-value pairs for categorization |
| `annotations` | object | No | Non-identifying metadata |

### metadata.labels

Common labels:

| Label | Values | Description |
|-------|--------|-------------|
| `data-classification` | `DIT`, `DAR`, `DIU` | Data protection category |
| `environment` | `production`, `staging`, `development` | Deployment environment |
| `component` | string | System component name |
| `team` | string | Owning team |

### Example

```yaml
metadata:
  name: api-gateway-tls
  uuid: 95beec7e-6f82-4aaa-8211-969cd7c1f1ab
  labels:
    data-classification:
      - DIT
    environment: production
    component: api-gateway
  annotations:
    jira-ticket: CRYPTO-123
```

## spec.module

Cryptographic module identification.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | CMVP-registered module name |
| `vendor` | object | Yes | Vendor information |
| `type` | enum | Yes | `hardware`, `software`, `hybrid`, `firmware` |
| `versions` | object | No | Version information |
| `operatingEnvironment` | string | No | Tested operating environment |

### spec.module.vendor

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Vendor name as registered with CMVP |
| `contact` | string | No | Vendor contact information |
| `website` | string | No | Vendor website URL |

### spec.module.versions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `software` | string | No | Software version |
| `firmware` | string | No | Firmware version |
| `hardware` | string | No | Hardware revision |

### Example

```yaml
spec:
  module:
    name: "OpenSSL FIPS Provider"
    vendor:
      name: "OpenSSL Software Foundation"
      website: "https://www.openssl.org"
    type: software
    versions:
      software: "3.0.8"
    operatingEnvironment: "Red Hat Enterprise Linux 9"
```

## spec.validation

FIPS 140 validation details.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `standard` | enum | Yes | `FIPS 140-2` or `FIPS 140-3` |
| `certificateNumber` | integer | Yes | CMVP certificate number |
| `securityLevel` | enum | Yes | `1`, `2`, `3`, or `4` |
| `validationDate` | date | No | Date of CMVP validation |
| `sunsetDate` | date | No | Certificate expiration date |
| `algorithms` | array | No | Validated algorithms |
| `caveatText` | string | No | Certificate caveats |
| `itar` | boolean | No | ITAR restricted (default: false) |

### spec.validation.algorithms

Array of validated cryptographic algorithms:

```yaml
algorithms:
  - AES
  - RSA
  - ECDSA
  - SHA-2
  - SHA-3
  - HMAC
  - DRBG
```

### Example

```yaml
spec:
  validation:
    standard: "FIPS 140-3"
    certificateNumber: 4282
    securityLevel: 1
    validationDate: "2023-10-03"
    sunsetDate: "2028-10-03"
    algorithms:
      - AES
      - RSA
      - ECDSA
      - SHA-2
      - SHA-3
```

## spec.usage

How and where the module is used.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dataClassification` | array | Yes | `data-in-transit`, `data-at-rest`, `data-in-use` |
| `location` | string | Yes | Where the module is deployed |
| `purpose` | string | Yes | What the module encrypts/protects |
| `inheritance` | object | No | FedRAMP inheritance info |

### spec.usage.dataClassification

Must include at least one:

| Value | Abbreviation | Description |
|-------|--------------|-------------|
| `data-in-transit` | DIT | Data moving between systems |
| `data-at-rest` | DAR | Data stored on disk/database |
| `data-in-use` | DIU | Data being processed in memory |

### spec.usage.inheritance

For inherited modules (IaaS/PaaS):

| Field | Type | Description |
|-------|------|-------------|
| `type` | enum | `none`, `partial`, `full` |
| `provider` | string | CSP name |
| `documentation` | string | Reference to inheritance documentation |

### Example

```yaml
spec:
  usage:
    dataClassification:
      - data-in-transit
    location: "API Gateway - TLS Termination"
    purpose: "TLS 1.3 encryption for all API traffic"
    inheritance:
      type: partial
      provider: "AWS"
      documentation: "AWS FedRAMP Inheritance Matrix v3.2"
```

## spec.portProtocolServiceRef

References to Port/Protocol/Service (PPS) entries from your SSP.

```yaml
portProtocolServiceRef:
  - pps-001    # HTTPS 443
  - pps-002    # SSH 22
```

## status

Auto-populated by the validation system. Do not set manually.

| Field | Type | Description |
|-------|------|-------------|
| `cmvpStatus` | enum | `Active`, `Historical`, `Revoked` |
| `lastValidated` | datetime | Last validation timestamp |
| `complianceStatus` | enum | `compliant`, `warning`, `non-compliant` |
| `validationErrors` | array | List of validation errors |
| `validationWarnings` | array | List of validation warnings |

### Example (auto-generated)

```yaml
status:
  cmvpStatus: Active
  lastValidated: "2025-12-07T10:30:00Z"
  complianceStatus: compliant
  validationErrors: []
  validationWarnings: []
```

## Complete Example

```yaml
apiVersion: fedramp20x-poc/v1
kind: CryptographicModule
metadata:
  name: openssl-fips-provider
  uuid: 95beec7e-6f82-4aaa-8211-969cd7c1f1ab
  labels:
    data-classification:
      - DIT
      - DAR
    environment: production
    component: application-server
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
    validationDate: "2023-10-03"
    algorithms:
      - AES
      - RSA
      - ECDSA
      - SHA-2
      - SHA-3
  usage:
    dataClassification:
      - data-in-transit
    location: "Application Server - TLS Termination"
    purpose: "TLS 1.3 encryption for API endpoints"
  portProtocolServiceRef:
    - pps-001
    - pps-002
status:
  cmvpStatus: Active
  lastValidated: "2025-12-07T10:30:00Z"
  complianceStatus: compliant
```
