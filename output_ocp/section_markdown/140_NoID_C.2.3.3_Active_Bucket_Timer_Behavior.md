##### C.2.3.3 Active Bucket Timer Behavior

> **Section ID**:  | **Page**: 122-122

The Active Bucket Timer times how long the Bucket Command Counters have been counting.  When
the Active Bucket Timer is equal to the Active Bucket Timer Threshold then the following operations
shall occur:
1.  The following data is moved:
a. Active Bucket Counters 0 - 3 is moved to Static Bucket Counters 0 - 3.
b. Active Latency Timestamps are moved to Static Latency Timestamps.
c. Active Measured Latencies are moved to Static Measured Latencies.
d. Active Latency Timestamp Units are moved to Static Latency Timestamp Units.
2. The Active Bucket items shall then be updated as follows:
a. Active Bucket Counters 0 - 3 are cleared to zero.
b. Active Latency Timestamps are set to invalid (FFFF_FFFF_FFFF_FFFFh).
c. Active Measured Latencies are cleared to zero.
d. Active Latency Timestamp Units are cleared to zero.
e. The Active Latency Minimum Window, if it is running, may be reset or continue to
count.
f. Active Bucket Timer is cleared to zero and starts the process of counting over.
When looking at the data structures in the Latency Monitor (Log Identifier C3h) it should be noted that
the data in item #1 and #2 above is 16-byte aligned, and the data can be moved simply by doing a data
move of the entire data structure.
