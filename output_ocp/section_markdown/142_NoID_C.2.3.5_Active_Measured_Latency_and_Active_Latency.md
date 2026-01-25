##### C.2.3.5 Active Measured Latency and Active Latency Timestamp Updates

> **Section ID**:  | **Page**: 123-123

The Active Measured Latency is the latency measured from fetching the command in the SQ to updating
the CQ.  The Active Measured Latency data structure and the Active Latency Timestamp data structure
shall be updated atomically.  They shall not update independently.  Each Command Counter
(Read/Write/De-Allocate) has an Active Measured Latency and an Active Latency Timestamp structure
associated with it.  The Active Latency Configuration is used to configure this feature.
When the Latency Mode in the Active Latency Configuration is cleared to zero then the following
behavior shall be followed:
• The Active Measured Latency and Active Latency Timestamp will be loaded the first time the
command counter associated with it increments.
• The Active Measured Latency and Active Latency Timestamp will not be loaded again until the
Active Measured Latency is reset.
If the Latency Mode is set to 0001h in the Active Latency Configuration, then every time the associated
command counter is incremented the Active Measured Latency will report the largest measured latency
based on the associated command counter.  The Active Latency Timestamp will report the time when
the largest latency occurred.
The Active Latency Minimum window also affects when the Active Measured Latency and the Active
Latency Timestamp are updated.  This is described in the section on Active Latency Minimum Window
