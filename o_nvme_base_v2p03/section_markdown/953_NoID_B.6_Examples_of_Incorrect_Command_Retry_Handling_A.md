### B.6 Examples of Incorrect Command Retry Handling After Communication Loss

> **Section ID**:  | **Page**: 779-779

Section 9.6.3 describes requirements for host retry of outstanding commands after communication loss. In
this situation, the response of a command is unknown and hence the host has no information about the
extent, if any, to which the controller has processed that command. Many commands are not safe to
unconditionally retry if they have been processed in part or completely. This annex describes examples of
problematic situations caused by retrying an outstanding command without regard to the consequences of
that retry.
