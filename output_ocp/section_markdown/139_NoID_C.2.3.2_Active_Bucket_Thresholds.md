##### C.2.3.2 Active Bucket Thresholds

> **Section ID**:  | **Page**: 121-122

There are multiple Active Command Counter Buckets.  The configured latency thresholds determine
which Bucket the command counter shall be incremented in.  Below is a picture showing how there are
multiple Buckets and thresholds for each Bucket.
If the Read, Write, De-allocate/TRIM command completion time is below Threshold A then no counter
is incremented.  If the threshold is equal or greater than A and less than B, then the corresponding
command counter in Active Bucket 0 increments.  If it is equal to or greater than B and less than
threshold C, then the corresponding command counter in Active Bucket 1 increments.   If it is equal to
or greater than C and less than threshold D, then the corresponding command counter in Active Bucket 2
increments.  If it is equal to or greater than threshold D, then the corresponding command counter in
Active Bucket 3 increments.  By following this process all latencies greater than threshold A are counted
for Read, Write and De-Allocate/TRIM commands.  When configuring the Latency Monitor Feature the
thresholds shall always be configured such that Active Threshold A < Active Threshold B < Active
Threshold C < Active Threshold D.
