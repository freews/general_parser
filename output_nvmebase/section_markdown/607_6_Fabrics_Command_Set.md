## 6 Fabrics Command Set

> **Section ID**: 6 | **Page**: 513-513

Fabrics commands are used to create queues and initialize a controller. Fabrics commands have an
Opcode field of 7Fh and are distinguished by the Fabrics Command Type as shown in Figure 574. Fabrics
commands are processed regardless of the state of controller enable (CC.EN). The Fabrics command
capsule is defined in section 3.3.2.1.1 and the Fabrics response capsule and status is defined in section
3.3.2.1.2. The common Fabrics Submission Queue entry is shown in Figure 94 and the common Fabrics
Completion Queue entry is shown in Figure 99.
Restrictions on processing commands listed in Figure 574 are defined in the Admin Command Set in
section 5 (e.g., while the NVM subsystem is performing a sanitize operation or processing of a Format NVM
command).


---
### 📊 Tables (1)

#### Table 1: Table_6_Fabrics_Command_Set
![Table_6_Fabrics_Command_Set](../section_images/Table_6_Fabrics_Command_Set.png)

| Some Fabric Command Type by Field | | | | | | |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| (07:02) | (01:00) | Combined Fabrics Command Type<sup>2</sup> | O/M<sup>1</sup> | I/O Queue<sup>3</sup> | | Command |
| Function | Data Transfer<sup>4</sup> | | | | | |
| 0000 00b | 00b | 00h | M | No | | Property Set |
| 0000 00b | 01b | 01h | M | Yes | | Connect<sup>5</sup> |
| 0000 01b | 00b | 04h | M | No | | Property Get |
| 0000 01b | 01b | 05h | O | Yes | | Authentication Send |
| 0000 01b | 10b | 06h | O | Yes | | Authentication Receive |
| 0000 10b | 00b | 08h | O | Yes | | Disconnect |
| | | | | | | |
| 11xx xx b | Note 4 | C0h to FFh | O | | | Vendor specific |
| | | | | | | |
| Notes: | | | | | | |
| 1. O/M definition: O = Optional, M = Mandatory. | | | | | | |
| 2. Fabrics Command Types not listed are reserved. | | | | | | |
| 3. All Fabrics commands, other than the Disconnect command, may be submitted on the Admin Queue. The I/O Queue supports Fabrics commands as specified in this column. If a Fabrics command that is not supported on an I/O Queue is sent on an I/O Queue, that command shall be aborted with a status code of Invalid Field in Command. | | | | | | |
| 4. 00b = no data transfer; 01b = host to controller; 10b = controller to host; 11b = reserved. Refer to the Transfer Direction field in Figure 94. | | | | | | |
| 5. The Connect command is submitted and completed on the same queue that the Connect command creates. Refer to section 3.3.2.2. | | | | | | |

