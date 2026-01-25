#### B.6.4. Retried Command Affects Another Host

> **Section ID**:  | **Page**: 781-782

In the example shown in Figure 820, two hosts use Location X in a namespace for coordination. Writing the
value A to Location X indicates that step A in a processing sequence has been completed, and writing the
value B indicates that step B in the processing sequence has been completed, where higher-level software
requires that step B follow step A.
Host 1 indicates completion of step A by writing the value A to Location X, but loss of communication
prevents Host 1 from receiving the completion of that command. Host 2 observes that step A is complete,
quickly performs step B, and indicates completion of step B by writing the value B to Location X.
In the absence of receiving a completion for the original command, Host 1 retries writing the value A to
Location X, overwriting the completion of step B reported by Host 2. This example shows that retry of
commands that are able to affect the behavior of other hosts is problematic. In this example, higher-level
software needs a mechanism to indicate that the writes to Location X are not safe to retry after a delay.
This sort of higher-level software usage of ordinary NVMe commands (e.g., NVM Command Set Write
commands) for coordination and synchronization among multiple hosts is strongly discouraged because
retry of these commands after communication loss is problematic. Higher-level software should instead use
mechanisms intended for coordination among multiple hosts. Two examples of such mechanisms are:
•
Reservations (refer to section 8.1.24); and
•
Compare and Write fused operations (refer to the Fused Operation section of the NVM Express
NVM Command Set Specification).
In addition, command retries that modify NVM subsystem state (e.g., a Set Features command that modifies
a feature that has any scope that is visible to other hosts as described in Figure 403) are able to affect the
behavior of other hosts. Use of commands that modify NVM subsystem state for coordination and
synchronization among multiple hosts is likewise strongly discouraged.
