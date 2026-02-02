##### C.2.3.4 Active Latency Timestamp Format

> **Section ID**:  | **Page**: 122-123

The format of the Latency Timestamp follows the Timestamp which is defined in NVMe 1.4b.  The
Latency Timestamp allows an understanding of where a latency excursion occurred in terms of time.
The Latency Timestamp time reported shall be based on CQ completion.
If the device receives a Set Features with a Timestamp, then the device shall use this combined with the
Power on Hours to determine the Latency Timestamp of when the latency event occurred.  If the device
receives multiple Set Features with a Timestamp the most recent Timestamp shall be used.
If the device does not receive a Set Features with a Timestamp, then the Latency Timestamp shall be
generated based on Power on Hours.
If the device receives a Set Features with a Timestamp and then the device is powered off.  When the
device is powered on it shall use the most recent Timestamp it received even if this Timestamp was from
before the device was powered off.
The Active Latency Timestamp Units shall be populated when the Latency Timestamp is updated to
indicate if the Latency Timestamp used Timestamp with Power on Hours to generate the Latency
Timestamp or if only Power on Hours were used to generate the Latency Timestamp.
