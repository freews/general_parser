#### C.2.3 Active Bucket Description

> **Section ID**:  | **Page**: 119-120

The high-level concept is to create 4 real time buckets groups of active latency tracking command counters.
Each bucket will count latency events which exceed a configured latency threshold.  Below is a description
of each bucket:
Each bucket contains the following:
• Saturating Read Command Counter with an associated Measured Latency and Latency
Timestamp.
• Saturating Write Command Counter with an associated Measured Latency and Latency
Timestamp.
• Saturating De-allocate/TRIM Command Counter with an associated Measured Latency and
Latency Timestamp.
For clarity, the opcode to Counter mapping is below:
In addition to the command counters there is a Measured Latency data structure and a Latency
Timestamp data structure associated with each command counter.  The Measured Latency and Latency
Timestamp have a direct relationship such that both are updated, or neither are updated.  The Measured
Latency and Latency Timestamp will be described later in this document.


---
### 📊 Tables (1)

#### Table 1: Table__C_2_3_Active_Bucket_Description
![Table__C_2_3_Active_Bucket_Description](../section_images/Table__C_2_3_Active_Bucket_Description.png)

| Bucket Counter | Opcode | Command |
| :--- | :--- | :--- |
| Read Command Counter | 02h | Read |
| Write Command Counter | 01h | Write |
| De-allocate/TRIM Command Counter | 09h with Attribute – Deallocate (AD) = 1 | Dataset Management |

