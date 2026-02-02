##### C.2.3.1 Active Command Counter Behavior

> **Section ID**:  | **Page**: 121-121

The active command counters count Read commands, Write commands, and De-Allocate/TRIM
commands which exceed a configured latency threshold.  These active command counters count until
the command counter saturates or the Active Bucket Timer expires.  Below is the behavior for each of
these events:
• Active Command Counter Saturation:
If the Command Counter saturates, the counter shall maintain the active value and
not wrap.
• Active Bucket Timer Expiration:
If the Active Bucket Timer Expires, then the following occurs:
o The Active Bucket Command Counter values and associated
information are moved into Static Bucket Command Counters, the
Active Bucket Command Counters are then cleared to zero and re-
start counting.
o The active command counters shall count regardless of how the
Active Latency Minimum Window is configured.
