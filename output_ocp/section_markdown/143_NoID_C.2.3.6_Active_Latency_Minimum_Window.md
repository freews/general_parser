##### C.2.3.6 Active Latency Minimum Window

> **Section ID**:  | **Page**: 123-125

This affects both the Active Measured Latency and the Active Latency Timestamp.  This defines the
minimum time between updating the Active Measured Latency and the Active Latency Timestamp for a
single Active Bucket/Counter combination.  The feature is only used if the Active Latency Mode is set
to 0001h.
If the Active Latency Minimum Window timer is running and the Measured Latency and Latency
Timestamp have been updated, then the Latency Timestamp and Active Measured Latency will not be
updated again until the Active Latency Minimum Window timer has expired.  Below are some examples
of this:
Example 1:
Assume:
• Active Latency Minimum Window of 5 seconds.
• Latency Mode is Configured for Largest Latency.
• Bucket 2 has a threshold range of 40ms to 400ms.
Example 2:
Assume:
• Active Latency Minimum Window of 5 seconds.
• Latency Mode is Configured for First Latency Event.
• Bucket 2 has a threshold range of 40ms to 400ms.
The Active Latency Minimum Window acts as a filter to ensure there are not a large number of events to
update the Active Measured Latency and the Latency Timestamp.  Thus, if the queue depth is 128
commands deep and there is a latency event, then there are not 128 updates to these data structures.
Rather the first event is recorded, and the rest of the events are filtered out.  It should be noted that the
Active Latency Window is not enforced across power cycles.  Thus, after a power cycle the Active
Latency Window shall not start until a Bucket Counter is incremented.


---
### 📊 Tables (2)

#### Table 1: Table__C_2_3_6_Active_Latency_Minimum_Window_1
![Table__C_2_3_6_Active_Latency_Minimum_Window_1](../section_images/Table__C_2_3_6_Active_Latency_Minimum_Window_1.png)

| Time in seconds | Read Counter Bucket 2 Latency Event | Active Read Counter Bucket 2 Value | Actual Latency | Active Measured Latency | Latency Stamp | Comment |
|---|---|---|---|---|---|---|
| 0 | N | 0 | - | - | FFFF_FFFF_FFFF_FFFh | Actual Latency and Active Measured latency are invalid. |
| 0.5 | Y | 1 | 50ms | 50ms | 0.5 Seconds | First Latency Event. This starts the Active Latency Minimum window. New latency events will not be recorded until the 5 second Active Minimum Window expires at 5.5 seconds. |
| 5.25 | Y | 2 | 100ms | 50ms | 0.5 Seconds | Measured Latency and Latency Timestamp is not updated due to Minimum Window is not expired; however, the Active Read Counter is updated. |
| 6 | Y | 3 | 75ms | 75ms | 6 Seconds | Minimum Window is expired and 75ms is greater than previous number of 50ms, so the Active Measured Latency and Latency Timestamp are updated. |


#### Table 2: Table__C_2_3_6_Active_Latency_Minimum_Window_2
![Table__C_2_3_6_Active_Latency_Minimum_Window_2](../section_images/Table__C_2_3_6_Active_Latency_Minimum_Window_2.png)

| Time in seconds | Read Counter Bucket 2 Latency Event | Active Read Counter Bucket 2 Value | Actual Latency | Active Measured Latency | Latency Stamp | Comment |
|---|---|---|---|---|---|---|
| 0 | N | 0 | - | - | FFFF_FFFF_FFFF_FFFh | Actual Latency and Active Measured latency are invalid. |
| 0.5 | Y | 1 | 150ms | 150ms | 0.5 Seconds | First Latency Event. |
| 10 | Y | 2 | 200ms | 150ms | 0.5 Seconds | Since the device is in First Latency Event mode, no additional events are recorded. |
| 15 | Y | 3 | 75ms | 150ms | 0.5 Seconds | Since the device is in First Latency Event mode, no additional events are recorded. |

