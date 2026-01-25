### A.7 Cache bench target

> **Section ID**:  | **Page**: 117-118

•
A benchmarking tool that’s a supplement for FB FIO Synth Flash tool on measuring performance
for cache applications.  This is different than the “B Cache” workload in FB FIO Synth Flash.
pp
•
Two workloads need to be tested:
o Tao Leader
o Memcache
•
The final allocator and throughput stats from the benchmark will be used to see if the targets
are met.
•
Send SSD latency versus time file to Facebook using one of the following methods:
o Send the raw results log file
o Run the “extract_latency.sh script and return the raw results log file, “.tsv” and “.png”
files.
•
Vendor NVMe CLI plug-in with “physical NAND bytes written” metric in the SMART / Health
Information Extended (Log Identifier C0h) needs to be working to get the write amplification.


---
### 📊 Tables (1)

#### Table 1: Table__A_7_Cache_bench_target
![Table__A_7_Cache_bench_target](../section_images/Table__A_7_Cache_bench_target.png)

| Workload | Get Rate | Set Rate | Read Latency (us) | | | | | Write Amp | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |

