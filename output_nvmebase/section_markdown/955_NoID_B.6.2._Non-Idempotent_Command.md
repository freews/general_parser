#### B.6.2. Non-Idempotent Command

> **Section ID**:  | **Page**: 780-780

In the example shown in Figure 818, the host loses communication with Controller 1 and does not receive
a response from Controller 1 for a Namespace Management command that creates a namespace (refer to
section 5.2.21). The host ensures that no further controller processing of that command is possible (refer
to section 9.6.2), and then retries that command on Controller 2, which creates a second namespace.
This example shows why higher-level software (e.g., an associated application, filesystem or database)
should take steps to determine that a retry of a non-idempotent command does not cause unintended
changes to NVM subsystem state (e.g., number of namespaces).
