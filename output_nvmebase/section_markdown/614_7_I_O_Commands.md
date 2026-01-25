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
### 🖼️ Figures (1)

#### Figure 1: Figure 589: Opcodes for I/O Commands
![Figure 589: Opcodes for I/O Commands](../section_images/Figure_7_I_O_Commands.png)

