# TCG Storage Security Subsystem Class (SSC): Opal
## Extracted Tables — Version 2.30 | 1/30/2025

---

## Table 18 - Admin SP - SPInfo Table Preconfiguration

| UID | SPID | Name | Size | SizeInUse | SPSessionTimeout | Enabled |
|-----|------|------|------|-----------|-----------------|---------|
| 00 00 00 02 00 00 00 01 | 00 00 02 05 00 00 00 01 | "Admin" | | | | T |

> **Note:** As specified in [2], a TPer SHALL ignore the value of SPSessionTimeout column if:
> - (a) no value exists in SPSessionTimeout column; or
> - (b) SPSessionTimeout column is zero.

---

## Table 19 - Admin SP - SPTemplates Table Preconfiguration

| UID | TemplateID | Name | Version |
|-----|------------|------|---------|
| 00 00 00 03 00 00 00 01 | 00 00 02 04 00 00 00 01 | "Base" | 00 00 00 02 *ST1 |
| 00 00 00 03 00 00 00 02 | 00 00 02 04 00 00 00 02 | "Admin" | 00 00 00 02 *ST1 |

> **\*ST1:** This version number or any version number that complies with this SSC.

---

## Table 20 - Admin SP - Table Table Preconfiguration

| UID | Name | CommonName | TemplateID | Kind | ColumnNum | Columns | Rows | RowsFree | RowBytes | LastID | MinSize | MaxSize | MandatoryWriteGranularity | RecommendedAccessGranularity |
|-----|------|------------|------------|------|-----------|---------|------|----------|----------|--------|---------|---------|--------------------------|------------------------------|
| 00 00 00 01 00 00 00 01 | "Table" | | | Object | | | 0 | 0 | | | | | | |
| 00 00 00 01 00 00 00 02 | "SPInfo" | | | Object | | | 0 | 0 | | | | | | |
| 00 00 00 01 00 00 00 03 | "SPTemplates" | | | Object | | | 0 | 0 | | | | | | |
| 00 00 00 01 00 00 00 06 | "MethodID" | | | Object | | | 0 | 0 | | | | | | |
| 00 00 00 01 00 00 00 07 | "AccessControl" | | | Object | | | 0 | 0 | | | | | | |

> **Note:**
> - Refer to section 5.3 for description and requirements of the `MandatoryWriteGranularity` and `RecommendedAccessGranularity` columns.
> - If the Data Removal Mechanism feature descriptor is not supported, the `DataRemovalMechanism` row SHALL NOT exist.

---

## Additional Properties Reference (Section 4.1.1.1)

| Property | Requirement | Host Property |
|----------|-------------|---------------|
| MaxMethods (M) | Min: 1, Max: VU, Initial: 1 | Yes |
| MaxSessions (M) | Min: 1, Max: VU, Initial: 1 | Yes |
| MaxAuthentications (M) | 2 minimum | N/A – not a host property |
| MaxTransactionLimit (M) | 1 minimum | N/A – not a host property |
| DefSessionTimeout (M) | VU | N/A – not a host property |

---

## StartSession Supported Parameters (Section 4.1.1.2)

| Parameter | Support |
|-----------|---------|
| HostSessionID | Mandatory |
| SPID | Mandatory |
| Write | Mandatory |
| HostChallenge | Mandatory |
| HostSigningAuthority | Mandatory |
| SessionTimeout | Optional |

| Write Value | Support |
|-------------|---------|
| True | SHALL be supported |
| False (read-only session) | May or may not be supported |

---

## SyncSession Supported Parameters (Section 4.1.1.3)

| Parameter | Support |
|-----------|---------|
| HostSessionID | Mandatory |
| SPSessionID | Mandatory |

---

## CloseSession (Section 4.1.1.4)

| Method | Support |
|--------|---------|
| CloseSession | Optional (MAY be supported) |
