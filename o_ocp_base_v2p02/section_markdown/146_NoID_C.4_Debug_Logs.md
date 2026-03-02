### C.4 Debug Logs

> **Section ID**:  | **Page**: 126-126

The Latency Monitoring Feature can also enable debug logs to trigger.  The Debug Log Trigger Enable
configures which counters shall trigger a debug log the first time the Bucket/Counter combination is
incremented.  Only a single debug log shall be generated.  Once a Latency Monitor debug log is
generated, until the Latency Monitor debug log is discarded another Latency Monitor debug log cannot
be generated.  The Latency Monitor debug log shall be discarded using Set Features for the Latency
Monitor or by reading the Latency Monitor Debug Log.
The Set Features for the Latency Monitor has two mechanisms for discarding the Debug Log.  One
method discards the debug log and resets the Latency Monitor feature to a new set of configured values
based on the fields in Set Features.  The other method discards the Debug Log and has no effect on any
of the other features associated with the Latency Monitor Feature.  Thus, the Latency Monitor Feature
will keep running undisturbed when the Debug Log is discarded.
When the Latency Monitor debug log trigger event happens, the following data shall be captured:
Debug Log Measured Latency, Debug Log Latency Timestamp, Debug Log Trigger Source, Debug Log
Timestamp Units, Debug Log Pointer as well as internal information required to debug the issue to root
cause.
