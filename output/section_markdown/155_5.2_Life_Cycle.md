### 5.2 Life Cycle

> **Section ID**: 5.2 | **Page**: 95-95

transitions for Manufactured SPs” section (see section 5.2.2.2) and “State behaviors for Manufactured SPs” 
section (see section 5.2.2.3) of this specification. 
Start of Informative Comment 
Reverting the Locking SP will cause the media encryption keys to be eradicated (except for the GlobalRange key if 
the KeepGlobalRangeKey parameter is present and set to True), which has the side effect of securely erasing all 
data in the User LBA portion of the Storage Device. 
End of Informative Comment 
5.1.3.4 Interrupted RevertSP 
The RevertSP method and complete implementation of the necessary background operations MAY be aborted due 
to any reset condition, including power loss.   
When interrupted, the Data Removal Operation Interrupted bit SHALL be set to one in the Level 0 Discovery – 
Supported Data Removal Mechanism feature descriptor appropriately as defined in section 3.1.1.6.2. 
Further, the return status value of the RevertSP method does not mean that all necessary operations such as the 
data removal operation are complete. 
5.2 Life Cycle 
