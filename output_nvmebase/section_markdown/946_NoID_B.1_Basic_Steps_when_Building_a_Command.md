### B.1 Basic Steps when Building a Command

> **Section ID**:  | **Page**: 775-775

When the host builds a command for the controller to execute, it first checks to make sure that the
appropriate Submission Queue (SQ) is not full. The Submission Queue is full when the number of entries
in the queue is one less than the queue size. Once an empty slot (pFreeSlot) is available:
1. The host builds a command at SQ[pFreeSlot] with:
a. CDW0.OPC is set to the appropriate command to be executed by the controller;
b. CDW0.FUSE is set to the appropriate value, depending on whether the command is a
fused operation;
c. CDW0.CID is set to a unique identifier for the command when combined with the
Submission Queue identifier;
d. The Namespace Identifier, NSID field, is set to the namespace the command applies to;
e. MPTR shall be filled in with the offset to the beginning of the Metadata Region, if there is
a data transfer and the namespace format contains metadata as a separate buffer;
f.
PRP1 and/or PRP2 (or SGL Entry 1 if SGLs are used) are set to the source/destination of
data transfer, if there is a data transfer; and
g. CDW10 – CDW15 are set to any command specific information;
and
2. The host then completes a transport specific action in order to submit the command for processing
