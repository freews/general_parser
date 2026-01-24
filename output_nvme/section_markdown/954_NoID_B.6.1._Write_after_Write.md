#### B.6.1. Write after Write

> **Section ID**:  | **Page**: 779-780

In the example shown in Figure 817, the host loses communication with Controller 1 and does not receive
a response from Controller 1 for an idempotent command that changes user data at location X to A (e.g.,
an NVM Command Set Write command). The following events occur:
•
The host retries that command on Controller 2 (Retry: Write A at Location X), and the retry succeeds
quickly.
•
The completion of that retry leads to the host subsequently submitting a command that changes
the user data at the same location to B (Write B at Location X).
•
During this time, Controller 1 has been processing the original outstanding command (Write A at
Location X), and that command’s change of user data at location X to A finally takes effect after the
user data at location X has already been changed to B.
The final outcome is that the user data at location X is A, which is incorrect and an example of data
corruption.
For an idempotent command that changes user data or NVM subsystem state, this example shows why
the host should not report the results of that command, including any retry of that command, to higher-level
software until the host is able to determine that no further controller processing of that command and any
retry of that command is possible (refer to section 9.6.2).
