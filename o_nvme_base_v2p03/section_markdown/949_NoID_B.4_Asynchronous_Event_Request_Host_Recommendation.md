### B.4 Asynchronous Event Request Host Recommendations

> **Section ID**:  | **Page**: 778-778

This section describes the recommended the host procedure for Asynchronous Event Requests
The host sends n Asynchronous Event Request commands (refer to section 3.5.1, step 12). When an
Asynchronous Event Request completes (providing Event Type, Event Information, and Log Page details):
•
If the event(s) in the reported Log Page may be disabled with the Asynchronous Event
Configuration feature (refer to section 5.2.26.1.5), then the host issues a Set Features command
for the Asynchronous Event Configuration feature specifying to disable reporting of all events that
utilize the Log Page reported. The host should wait for the Set Features command to complete;
•
The host issues a Get Log Page command requesting the Log Page reported as part of the
Asynchronous Event Command completion. The host should wait for the Get Log Page command
to complete;
•
The host parses the returned Log Page. If the condition is not persistent, then the host should re-
enable all asynchronous events that utilize the Log Page. If the condition is persistent, then the
host should re-enable all asynchronous events that utilize the Log Page except for the one(s)
reported in the Log Page. The host re-enables events by issuing a Set Features command for the
Asynchronous Event Configuration feature;
•
The host should issue an Asynchronous Event Request command to the controller (restoring to n
the number of these commands outstanding); and
•
If the reporting of event(s) was disabled, the host should enable reporting of the event(s) using the
Asynchronous Event Configuration feature. If the condition reported may persist, the host should
continue to monitor the event (e.g., spare below threshold) to determine if reporting of the event
should be re-enabled.
