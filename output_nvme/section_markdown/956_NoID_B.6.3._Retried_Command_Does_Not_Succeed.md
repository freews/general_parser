#### B.6.3. Retried Command Does Not Succeed

> **Section ID**:  | **Page**: 781-781

In the example shown in Figure 819, the host loses communication with Controller 1 and does not receive
a response to a Reservation Register command that unregisters the host (refer to section 7.6). The host
ensures that no further controller processing of that command is possible (refer to section 9.6.2), and then
retries that command on Controller 2. As a result of the original command unregistering the host, the host
is no longer a registrant, and for that reason, the controller returns a status code of Reservation Conflict
(refer to section 8.1.24.4).
This example shows why an error status code is able to be returned if a non-idempotent command is retried
after the original command has been processed. An analogous example is possible for the Compare and
Write fused operation (refer to the Fused Operation section of the NVM Express NVM Command Set
Specification) because that fused operation is not idempotent.
