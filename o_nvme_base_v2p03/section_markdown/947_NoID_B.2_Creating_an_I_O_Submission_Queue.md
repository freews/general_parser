### B.2 Creating an I/O Submission Queue

> **Section ID**:  | **Page**: 775-776

This example describes how the host creates an I/O Submission Queue that utilizes non-contiguous PRP
entries. Creating an I/O Submission Queue that utilizes a PRP List is only valid if the controller supports
non-contiguous queues as indicated in CAP.CQR.
Prior to creating an I/O Submission Queue, the host shall create the I/O Completion Queue that the SQ
uses with the Create I/O Completion Queue command.
To create an I/O Submission Queue, the host builds a Create I/O Submission Queue command for the
Admin Submission Queue. The host builds the Create I/O Submission Queue command in the next free
Admin Submission Queue command location. The attributes of the command are:
•
CDW0.OPC is set to 01h;
•
CDW0.FUSE is cleared to 00b indicating that this is not a fused operation;
•
CDW0.CID is set to a free command identifier;
•
The NSID field is cleared to 0h; Submission Queues are not specific to a namespace;
•
MPTR is cleared to 0h; metadata is not used for this command;
•
PRP1 is set to the physical address of the PRP List. The PRP List is shown in Figure 815 for a
PRP List with three entries;
•
PRP2 is cleared to 0h; PRP Entry 2 is not used for this command;
•
CDW10.QSIZE is set to the size of queue to create. In this case, the value is set to 191, indicating
a queue size of 192 entries. The queue size shall not exceed the maximum queue entries
supported, indicated in the CAP.MQES field;
•
CDW10.QID is set to the Submission Queue identifier;
•
CDW11.CQID is set to the I/O Completion Queue identifier where command completions are
posted;
•
CDW11.QPRIO is set to 10b, indicating a Medium priority queue; and
•
CDW11.PC is cleared to ‘0’ indicating that the data buffer indicated by PRP1 is not physically
contiguously.
The host then completes a transport specific action in order to submit the command for processing. The
host shall maintain the PRP List unmodified in host memory until the Submission Queue is deleted.


---
### 🖼️ Figures (1)

#### Figure 1: Figure 815: PRP List Describing I/O Submission Queue
![Figure 815: PRP List Describing I/O Submission Queue](../section_images/Figure__B_2_Creating_an_I_O_Submission_Queue.png)

