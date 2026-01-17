#### 5.2.3 Type Table Modification

> **Section ID**: 5.2.3 | **Page**: 98-98

5.2.3 Type Table Modification 
In order to accommodate the additional life cycle states defined in this specification, the definition of the 
life_cycle_state type is changed from [2] to that described in Table 49: 
Table 49 - Life Cycle State Type Table Modification 


---
### 📊 Tables (1)

#### Table 1: Table 49 - Life Cycle State Type Table Modification
![Table 49 - Life Cycle State Type Table Modification](../section_images/table_098_0.png)

| UID | Name | Format | Size | Description |
|:---|:---|:---|:---|:---|
| 00 00 00 05<br>00 00 04 05 | life_cycle_state | Enumeration_Type,<br>0,<br>15 | | Used to represent the current life cycle state. The valid values are:<br><br>0 = issued,<br>1 = issued-disabled,<br>2 = issued-frozen,<br>3 = issued-disabled-frozen,<br>4 = issued-failed,<br>5-7 = reserved,<br>8 = manufactured-inactive,<br>9 = manufactured,<br>10 = manufactured-disabled,<br>11 = manufactured-frozen,<br>12 = manufactured-disabled-frozen,<br>13 = manufactured-failed,<br>14-15 = reserved |

