## 12 Device Profiles

> **Section ID**: 12 | **Page**: 102-103

The following are device profiles.  This section is intended to be firmware-based configuration settings
configured by device suppliers when manufacturing a device.  A device may be configured with a mix
of A and/or B settings.  Each customer shall provide their A/B preference for each configuration setting.
The following conventions are used for the Device Profile Table:


---
### 📊 Tables (1)

#### Table 1: Table_12_Device_Profiles
![Table_12_Device_Profiles](../section_images/Table_12_Device_Profiles.png)

| Convention | Definition |
| :--- | :--- |
| R | Required. This shall be supported. |
| O | Optional. This may be supported. |
| P | Prohibited. This shall not be supported. |
| **Requirement ID** | **Description** | **Configuration Setting** | |
| | | **A** | **B** |
| DP-CFG-1 | Factory Default Sector Size. | 4096-byte | 512-byte |
| DP-CFG-2 | Number of Namespaces Supported. | NSM-4 (16 Namespaces) | NSM-5 (16 Namespaces per TB) |
| DP-CFG-3 | Retention Time based on RETC-1 (data retention time). | 1 Month | 3 Months |
| DP-CFG-4 | NVMe Basic Management Command Supported. | R | P |
| DP-CFG-5 | Max M.2 top side height. | 2.0mm | 3.2mm |
| DP-CFG-6 | EOL/PLP Failure Mode (Feature Identifier C2h). | Enabled | Disabled |
| DP-CFG-7 | Write Uncorrectable command support. | O | R |
| DP-CFG-8 | Time-to-Identify-Ready based on TTR-1. | <= 1 second | <= 10 seconds |
| DP-CFG-9 | Time-to-I/O-Ready based on TTR-2. | <= 20 seconds | <= 10 seconds |
| DP-CFG-10 | In addition to the requirements in TTR-4, the device shall keep CSTS.RDY = 0 until the device is able to service I/O commands successfully. | P | R |

