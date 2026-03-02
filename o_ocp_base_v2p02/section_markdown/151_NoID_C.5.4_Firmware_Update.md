#### C.5.4 Firmware Update

> **Section ID**:  | **Page**: 127-127

When activating new firmware, if the Latency Monitoring Feature is enabled, the firmware activation
shall reset the Latency Monitoring Feature just as if a Set Features command to enable the feature was
received.  The Latency Monitoring Log shall start updating properly within 2 minutes of firmware
activation completing.  Thus, there are command latencies which could be missed after initially
activating new firmware.
