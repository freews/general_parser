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
### 🖼️ Figures (2)

#### Figure 1: Figure 142 defines all Admin commands. Refer to Figure 28 for mandatory, optional, and prohibited
commands for the various controller types.
![Figure 142 defines all Admin commands. Refer to Figure 28 for mandatory, optional, and prohibited
commands for the various controller types.](../section_images/Figure_5_Admin_Command_Set_1.png)


#### Figure 2: Figure 142: Opcodes for Admin Commands
![Figure 142: Opcodes for Admin Commands](../section_images/Figure_5_Admin_Command_Set_2.png)

