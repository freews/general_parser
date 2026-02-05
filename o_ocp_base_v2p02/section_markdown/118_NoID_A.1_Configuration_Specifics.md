### A.1 Configuration Specifics

> **Section ID**:  | **Page**: 114-115


---
### 📊 Tables (1)

#### Table 1: Table__A_1_Configuration_Specifics
![Table__A_1_Configuration_Specifics](../section_images/Table__A_1_Configuration_Specifics.png)

| Requirement ID | Description |
| :--- | :--- |
| FB-CONF-1 | Obsolete. |
| FB-CONF-2 | IEEE 1667 shall not be supported. Devices shall not support Enable IEEE1667 Silo (Feature Identifier C4h) Set Feature or Enable IEEE1667 Silo (Feature Identifier C4h) Get Feature. |
| FB-CONF-3 | For all form factors, SMBus byte 91 bit 6, Firmware Update Enabled bit shall be set to 1b by default from the factory. |
| Requirement ID | Description |
| FB-CONF-4 | Devices shall not support Error Injection (Feature Identifier C0h) Set Feature. |
| FB-CONF-5 | Devices shall not support Error Injection (Feature Identifier C0h) Get Feature. |
| FB-CONF-6 | Devices shall not support Error Recovery (Log Identifier C1h). |
| FB-CONF-7 | All Telemetry and debugging logs can be either in binary or ASCII. |
| FB-CONF-8 | The default power state shall conform to the following table: |
| | <table><tbody><tr><td><b>Form Factor</b></td><td><b>Capacity</b></td><td><b>Default Power State Upon Factory Exit</b></td></tr><tr><td>E1.S</td><td><= 2TB</td><td>6 (12W)</td></tr><tr><td></td><td>= 4TB</td><td>5 (14W)</td></tr></tbody></table> |
| FB-CONF-9 | Devices shall be configured to Configuration Setting A as shown in Section 12 - Device Profiles. |

