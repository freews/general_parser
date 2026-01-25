## 7 I/O Commands

> **Section ID**: 7 | **Page**: 524-524

An I/O command is a command submitted to an I/O Submission Queue. Figure 589 lists the I/O commands
that are defined for use in all I/O Command Sets. The following subsections provide definitions for each
command. Refer to section 3.1.3.4 for mandatory, optional, and prohibited I/O commands for the various
controller types. The following subsections describe the definition for each of these commands.
The user data format and any end-to-end protection information is I/O Command Set specific. Refer to each
I/O Command Set specification for applicability and additional details, if any. Refer to the referenced NVM
Express I/O Command Set specification for all I/O Command Set specific commands described in Figure
589.
Commands shall only be submitted by the host when the controller is ready as indicated in the Controller
Status property (CSTS.RDY) and after appropriate I/O Submission Queue(s) and I/O Completion Queue(s)
have been created.
The submission queue entry (SQE) structure and the fields that are common to all I/O commands are
defined in section 4.1. The completion queue entry (CQE) structure and the fields that are common to all
I/O commands are defined in section 4.2. The command specific fields in the SQE and CQE structures (i.e.,
SQE Command Dwords 10-15, CQE Dword 0, and CQE Dword 1) for I/O commands supported across all
I/O Command Sets are defined in this section.


---
### 📊 Tables (1)

#### Table 1: Table_7_I_O_Commands
![Table_7_I_O_Commands](../section_images/Table_7_I_O_Commands.png)

| (07:02) | (01:00) | | | | |
| :--- | :--- | :--- | :--- | :--- | :--- |
| | | **Combined** | | | |
| | | **Opcode**<sup>1</sup> | | | |
| **Function** | **Data Transfer**<sup>3</sup> | | **Command**<sup>2</sup> | | **Reference** |
| 0000 00b | 00b | 00h | Flush<sup>4</sup> | | 7.2 |
| 0000 11b | 01b | 0Dh | Reservation Register | | 7.6 |
| 0000 11b | 10b | 0Eh | Reservation Report | | 7.8 |
| 0001 00b | 01b | 11h | Reservation Acquire | | 7.5 |
| 0001 00b | 10b | 12h | I/O Management Receive | | 7.3 |
| 0001 01b | 01b | 15h | Reservation Release | | 7.7 |
| 0001 10b | 00b | 18h | Cancel<sup>4</sup> | | 7.1 |
| 0001 11b | 01b | 1Dh | I/O Management Send | | 7.4 |
| 0111 11b | 11b<sup>5</sup> | 7Fh | Fabric Commands<sup>5</sup> | | 6 |
| | | | | | |
| 1xxx xx b | NOTE 3 | 80h to FFh | Vendor specific | | |
| | | | | | |
| Notes: | | | | | |
| 1. Op codes not listed are I/O Command Set specific or reserved. Refer to Figure 91 for Opcode details. | | | | | |
| 2. All I/O commands use the Namespace Identifier (NSID) field. The value FFFFFFFFh is not supported in this field unless footnote 4 in this figure indicates that a specific command does support that value. | | | | | |
| 3. 00b = no data transfer; 01b = host to controller; 10b = controller to host; 11b = bidirectional. Refer to the Transfer Direction field in Figure 91. | | | | | |
| 4. This command may support the use of the Namespace Identifier (NSID) field set to FFFFFFFFh. | | | | | |
| 5. All Fabrics commands use the opcode 7Fh with the direction of data transfer specified as shown in Figure 574. Refer to section 6 for details. | | | | | |

