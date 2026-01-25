## 5 Admin Command Set

> **Section ID**: 5 | **Page**: 195-196

The Admin Command Set defines the commands that may be submitted to the Admin Submission Queue.
Section 5.1.2 describes Admin commands that are common to all transport models. Section 5.3 describes
Admin commands that are specific to the Memory-based transport model. Section 5.4 describes Admin
commands that are specific to the Message-based transport model.
The submission queue entry (SQE) structure and the fields that are common to all Admin commands are
defined in section 4.1. The completion queue entry (CQE) structure and the fields that are common to all
Admin commands are defined in section 4.2. The command specific fields in the SQE and CQE structures
(i.e., SQE Command Dwords 10 to 15, CQE Dword 0, and CQE Dword 1) for the Admin Command Set are
defined in this section.
Admin commands should not be impacted by the state of I/O queues (e.g., a full I/O Completion Queue
should not delay or stall the Delete I/O Submission Queue command).
Figure 142 defines all Admin commands. Refer to Figure 28 for mandatory, optional, and prohibited
commands for the various controller types.


---
### 📊 Tables (1)

#### Table 1: Table_5_Admin_Command_Set
![Table_5_Admin_Command_Set](../section_images/Table_5_Admin_Command_Set.png)

| Opcode by Field |  |  |  |  |  |
| :--- | :--- | :--- | :--- | :--- | :--- |
| (07:02) | (01:00) | | | | |
| Function | Data Transfer³ | Combined Opcode¹ | Namespace Identifier Used ² | Command | Reference ⁸ |
| 0000 00b | 00b | 00h | No | Delete I/O Submission Queue | 5.3.4 |
| 0000 00b | 01b | 01h | No | Create I/O Submission Queue | 5.3.2 |
| 0000 00b | 10b | 02h | Yes¹¹ | Get Log Page | 5.2.12 |
| 0000 01b | 00b | 04h | No | Delete I/O Completion Queue | 5.3.3 |
| 0000 01b | 01b | 05h | No | Create I/O Completion Queue | 5.3.1 |
| 0000 01b | 10b | 06h | NOTE 6 | Identify | 5.2.13 |
| 0000 10b | 00b | 08h | No | Abort | 5.2.1 |
| 0000 10b | 01b | 09h | Yes | Set Features | 5.2.26 |
| 0000 10b | 10b | 0Ah | Yes | Get Features | 5.2.11 |
| 0000 11b | 00b | 0Ch | No | Asynchronous Event Request | 5.2.2 |
| 0000 11b | 01b | 0Dh | Yes | Namespace Management | 5.2.21 |
| 0001 00b | 00b | 10h | No | Firmware Commit | 5.2.8 |
| 0001 00b | 01b | 11h | No | Firmware Image Download | 5.2.9 |
| 0001 01b | 00b | 14h | Yes | Device Self-test | 5.2.5 |
| 0001 01b | 01b | 15h | Yes⁴ | Namespace Attachment | 5.2.20 |
| 0001 10b | 00b | 18h | No | Keep Alive | 5.2.7 |
| 0001 10b | 01b | 19h | Yes⁵ | Directive Send | 5.2.6 |
| 0001 10b | 10b | 1Ah | Yes⁵ | Directive Receive | 5.2.6 |
| 0001 11b | 00b | 1Ch | No | Virtualization Management | 5.3.6 |
| 0001 11b | 01b | 1Dh | No | NVMe-MI Send | 5.2.19 |
| 0001 11b | 10b | 1Eh | No | NVMe-MI Receive | 5.2.18 |
| 0010 00b | 00b | 20h | No | Capacity Management | 5.2.3 |
| 0010 00b | 01b | 21h | No | Discovery Information Management | 5.4.4 |
| 0010 00b | 10b | 22h | No | Fabric Zoning Receive | 5.4.6 |
| 0010 01b | 00b | 24h | No | Lockdown | 5.2.15 |
| 0010 01b | 01b | 25h | No | Fabric Zoning Lookup | 5.4.5 |
| 0010 10b | 00b | 28h | No | Clear Exported NVM Resource Configuration¹⁰ | 5.4.1 |
| 0010 10b | 01b | 29h | No | Fabric Zoning Send | 5.4.7 |
| 0010 10b | 10b | 2Ah | No | Create Exported NVM Subsystem¹⁰ | 5.4.2 |
| 0010 11b | 00b | 2Dh | No | Manage Exported NVM Subsystem¹⁰ | 5.4.9 |
| Opcode by Field |  |  |  |  |  |
| (07:02) | (01:00) | | | | |
| Function | Data Transfer³ | Combined Opcode¹ | Namespace Identifier Used ² | Command | Reference ⁸ |
| 0011 00b | 01b | 31h | Yes | Manage Exported Namespace¹⁰ | 5.4.8 |
| 0011 01b | 01b | 35h | No | Manage Exported Port¹⁰ | 5.4.10 |
| 0011 10b | 00b | 38h | No | Cross-Controller Reset | 5.4.3 |
| 0011 10b | 01b | 39h | No | Send Discovery Log Page | 5.4.11 |
| 0011 11b | 01b | 3Dh | No | Track Send | 5.2.28 |
| 0011 11b | 10b | 3Eh | No | Track Receive | 5.2.27 |
| 0100 00b | 01b | 41h | No | Migration Send | 5.2.17 |
| 0100 00b | 10b | 42h | No | Migration Receive | 5.2.16 |
| 0100 01b | 01b | 45h | No | Controller Data Queue | 5.2.4 |
| 0111 11b | 00b | 7Ch | No | Doorbell Buffer Config | 5.3.5 |
| 0111 11b | 11b⁹ | 7Fh | No | Fabrics Commands⁹ | 6 |
| 1000 00b | 00b | 80h | Yes | Format NVM | 5.2.10 |
| 1000 00b | 01b | 81h | NOTE 7 | Security Send | 5.2.25 |
| 1000 00b | 10b | 82h | NOTE 7 | Security Receive | 5.2.23 |
| 1000 01b | 00b | 84h | No | Sanitize | 5.2.22 |
| 1000 01b | 01b | 85h | Yes | Load Program | CP |
| 1000 01b | 10b | 86h | Yes⁴ | Get LBA Status | NVM, ZNS |
| 1000 10b | 00b | 88h | Yes | Program Activation Management | CP |
| 1000 10b | 01b | 89h | Yes | Memory Range Set Management | CP |
| 1000 11b | 00b | 8Ch | Yes⁴ | Sanitize Namespace | 5.2.23 |
| | | | | | |
| Vendor Specific | | | | | |
| 11xx xxb | NOTE 3 | C0h to FFh | | Vendor specific | |
| Notes: | | | | | |
| 1. Opcodes not listed are reserved. | | | | | |
| 2. A subset of commands use the Namespace Identifier (NSID) field. If the Namespace Identifier field is used, then the value FFFFFFFFh is supported in this field unless otherwise indicated in footnotes in this figure that a specific command does not support that value or supports that value only under specific conditions. When this field is not used, the field is cleared to 0h as described in Figure 92. | | | | | |
| 3. 00b = no data transfer; 01b = host to controller; 10b = controller to host; 11b = bidirectional. Refer to the Data Transfer Direction field in Figure 91. | | | | | |
| 4. This command does not support the use of the Namespace Identifier (NSID) field set to FFFFFFFFh. | | | | | |
| 5. Support for the Namespace Identifier field set to FFFFFFFFh depends on the Directive Operation (refer to section 8.1.9). | | | | | |
| 6. Use of the Namespace Identifier field depends on the CNS value in the Identify Command as described in Figure 326. | | | | | |
| 7. The use of the Namespace Identifier is Security Protocol specific. | | | | | |
| 8. Section 5.1.2 contains commands common to all transport models, section 5.3 contains commands specific to the Memory-based transport model, and section 5.4 contains commands specific to the Message-based transport model. NVM = NVM Command Set specific, ZNS = Zoned Namespace Command Set specific, CP = Computational Programs Command Set specific. | | | | | |
| 9. All Fabrics commands use the opcode 7Fh with the data transfer direction specified as shown in Figure 574. Refer to section 6 for details. | | | | | |
| 10. Support for this command is prohibited in NVM subsystems that use a Memory-Based Transport Model (e.g., the PCIe transport) for any controller. | | | | | |
| 11. Use of the Namespace Identifier field is specified further in section 5.2.12.1 and Figure 206. | | | | | |

