## Bit

> **Section ID**:  | **Page**: 19-19


---
### 📊 Tables (3)

#### Table 1: Table 2 - Level 0 Discovery Header
![Table 2 - Level 0 Discovery Header](../section_images/table_019_0.png)

| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Byte** | | | | | | | | |
| 0 | (MSB) | | | | | | | |
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | (LSB) |
| 4 | (MSB) | | | | | | | |
| 5 | | | | | | | | |
| 6 | | | | | | | | |
| 7 | | | | | | | | (LSB) |
| 8 - 15 | | | | | | | | |
| 16 | (MSB) | | | | | | | |
| ... | | | | | | | | |
| 47 | | | | | | | | (LSB) |


#### Table 2: Table 3 - Level 0 Discovery - TPer Feature Descriptor
![Table 3 - Level 0 Discovery - TPer Feature Descriptor](../section_images/table_020_0.png)

| Byte | Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | | | | | |
| 0 | (MSB) | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |


#### Table 3: Table 4 - Level 0 Discovery - Locking Feature Descriptor
![Table 4 - Level 0 Discovery - Locking Feature Descriptor](../section_images/table_020_1.png)

| Bit Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| | (MSB) | | | | | | | |
| 0 | | | | | | | | |
| | | | | | | | | Feature Code (0x0002) |
| | | | | | | | | |
| 1 | | | | | | | | |
| | | | | | | | | (LSB) |
| 2 | | | | | | | | |
| | | | | | | | | Version |
| | | | | | | | | Reserved |
| 3 | | | | | | | | |
| | | | | | | | | Length |
| 4 | HW Reset for LOR/DOR Supported | MBR Shadowing Not Supported | MBR Done | MBR Enabled | Media Encryption | Locked | Locking Enabled | Locking Supported |
| 5 - 15 | | | | | | | | |
| | | | | | | | | Reserved |

