### A.2 Performance Requirements

> **Section ID**:  | **Page**: 115-115

The following numbers are the Facebook performance targets for data storage SSD across all form
factors.  They are provided to serve as a guidance for SSD Vendors.  Performance scripts can be found
on GitHub at https://github.com/facebookincubator/FioSynth.
The targets are broken down into the following segments:


---
### 📊 Tables (1)

#### Table 1: Table__A_2_Performance_Requirements
![Table__A_2_Performance_Requirements](../section_images/Table__A_2_Performance_Requirements.png)

| Requirement ID | Description |
| :--- | :--- |
| FB-PERF-1 | FB-FIO Synth Flash Targets (for all capacities). |
| FB-PERF-2 | fb-FIOSynthFlash TRIM Rate targets. |
| FB-PERF-3 | IO.go benchmark target. |
| FB-PERF-4 | Fileappend benchmark target. |
| FB-PERF-5 | Sequential write bandwidth. |
| FB-PERF-6 | Cache bench target. |
| FB-PERF-7 | All targets shall be achieved by using “kyber” as the I/O scheduler. |
| FB-PERF-8 | |
| | **Form Factor** | **Capacity** | **Max Average Power Consumption to Achieve All Performance Targets** |
| | M.2 | 2TB and smaller | 8.5W |
| | E1.S | 2TB and smaller | 10W |
| | | 4TB | 12W |
| | The power measurement methodology is described in PCM-1 (device max average power), PCM-2 (device peak power), and PCM-3 (peak power limit). |

