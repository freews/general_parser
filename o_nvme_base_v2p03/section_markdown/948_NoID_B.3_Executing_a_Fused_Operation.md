### B.3 Executing a Fused Operation

> **Section ID**:  | **Page**: 776-778

This example describes how the host creates and executes a fused command, specifically Compare and
Write for a total of 16 KiB of data. In this case, there are two commands that are created. The first command
is the Compare, referred to as CMD0. The second command is the Write, referred to as CMD1. In this case,
end-to-end data protection is not enabled and the size of each logical block is 4 KiB.
To build commands for a fused operation, the host utilizes two available adjacent command locations in the
appropriate I/O Submission Queue as is described in section 3.4.2.
The attributes of the Compare command are:
•
CMD0.CDW0.OPC is set to 05h for Compare;
•
CMD0.CDW0.FUSE is set to 01b indicating that this is the first command of a fused operation;
•
CMD0.CDW0.CID is set to a free command identifier;
•
CMD0.NSID is set to identify the appropriate namespace;
•
If metadata is being used in a separate buffer, then the location of that buffer is specified in the
CMD0.MPTR field;
•
The physical address of the first page of the data to compare:
If PRPs are used, CMD0.PRP1 is set to the physical address of the first page of the data
to compare and CMD0 PRP2 is set to the physical address of the PRP List The PRP List
p y
is shown in Figure 816 for a PRP List with three entries; or
If the command uses SGLs, CMD0.SGL1 is set to an appropriate SGL segment descriptor
depending on whether more than one descriptor is needed;
•
CMD0.CDW10.SLBA is set to the first LBA to compare against. Note that this field also spans
Command Dword 11;
•
CMD0.CDW12.LR is cleared to ‘0’ to indicate that the controller should apply all available error
recovery means to retrieve the data for comparison;
•
CMD0.CDW12.FUA is cleared to ‘0’, indicating that the data may be read from any location,
including a volatile cache, in the NVM subsystem;
•
CMD0.CDW12.PRINFO is cleared to 0h since end-to-end protection is not enabled;
•
CMD0.CDW12.NLB is set to 3h, indicating that four logical blocks of a size of 4 KiB each are to be
compared against;
•
CMD0.CDW14 is cleared to 0h since end-to-end protection is not enabled; and
•
CMD0.CDW15 is cleared to 0h since end-to-end protection is not enabled.
The attributes of the Write command are:
•
CMD1.CDW0.OPC is set to 01h for Write;
•
CMD1.CDW0.FUSE is set to 10b indicating that this is the second command of a fused operation;
•
CMD1.CDW0.CID is set to a free command identifier;
•
CMD1.NSID is set to identify the appropriate namespace. This value shall be the same as
CMD0.NSID;
•
If metadata is being used in a separate buffer, then the location of that buffer is specified in the
CMD1.MPTR field;
•
The physical address of the first page of data to write is identified:
If the command uses PRPs, then CMD1.PRP1 is set to the physical address of the first
page of the data to write and CMD1.PRP2 is set to the physical address of the PRP List.
The PRP List includes three entries; or
If the command uses SGLs, CMD1.SGL1 is set to an appropriate SGL segment descriptor
depending on whether more than one descriptor is needed;
•
CMD1.CDW10.SLBA is set to the first LBA to write. Note that this field also spans Command Dword
11. This value shall be the same as CMD0.CDW10.SLBA;
•
CMD1.CDW12.LR is cleared to ‘0’ to indicate that the controller should apply all available error
recovery means to write the data to the NVM;
•
CMD1.CDW12.FUA is cleared to ‘0’, indicating that the data may be written to any location,
including a volatile cache, in the NVM subsystem;
•
CMD1.CDW12.PRINFO is cleared to 0h since end-to-end protection is not enabled;
•
CMD1.CDW12.NLB is set to 3h, indicating that four logical blocks of a size of 4 KiB each are to be
compared against. This value shall be the same as CMD0.CDW12.NLB;
•
CMD1.CDW14 is cleared to 0h since end-to-end protection is not enabled; and
•
CMD1.CDW15 is cleared to 0h since end-to-end protection is not enabled.
The host then completes a transport specific action in order to submit the command for processing. Note
that the transport specific submit action shall indicate both commands have been submitted at one time.


---
### 🖼️ Figures (1)

#### Figure 1: Figure 816: PRP List Describing Data to Compare
![Figure 816: PRP List Describing Data to Compare](../section_images/Figure__B_3_Executing_a_Fused_Operation.png)

