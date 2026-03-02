#### C.5.1 Power Off/On When Latency Monitoring Feature is Enabled

> **Section ID**:  | **Page**: 127-127

When powering off, the Active Bucket Information (Counters, Measured Latency, Latency Timestamp,
Active Bucket Timer) may be slightly off due to concerns with flushing data with unsafe power down.
The Active Bucket Information shall maintain coherency compared to itself when flushing data with
unsafe power down.  When the device powers back on the Latency Monitoring Feature shall restore the
Active/Static Bucket/Debug Information including loading the Active Bucket Counter.  Once the
restoration is complete then the device shall resume the Latency Monitor functionality.  The device shall
start capturing latency data within 2 minutes of power on.  Thus, commands for the first 2 minutes may
not be monitored.  The Active Latency Window is not enforced across power cycles.  Thus, after a
power cycle the Active Latency Window shall not start until a Bucket Counter is incremented.
