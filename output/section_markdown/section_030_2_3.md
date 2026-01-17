### 2.3 Interface Communication Protocol

> **Section ID**: 2.3 | **Page**: 17-17

TCG Storage Security Subsystem Class (SSC): Opal  |  Version 2.30  |  1/30/2025  |  PUBLISHED 
Page 16 
© TCG 2025 
2 Opal SSC Overview 
2.1 Opal SSC Use Cases and Threats 
Start of Informative Comment 
The Opal SSC is an implementation profile for Storage Devices built to: 
• 
Protect the confidentiality of stored user data against unauthorized access once it leaves the owner’s control 
(following a power cycle and subsequent deauthentication) 
• 
Enable interoperability between multiple Storage Device vendors 
An Opal SSC compliant Storage Device: 
• 
Facilitates feature discoverability 
• 
Provides some user definable features (e.g. access control, locking ranges, user passwords, etc.) 
• 
Supports Opal SSC unique behaviors (e.g. communication, table management) 
This specification addresses a limited set of use cases. They are: 
• 
Deploy Storage Device & Take Ownership: the Storage Device is integrated into its target system and ownership 
transferred by setting or changing the Storage Device’s owner credential. 
• 
Activate or Enroll Storage Device: LBA ranges are configured and data encryption and access control credentials 
(re)generated and/or set on the Storage Device. Access control is configured for LBA range unlocking. 
• 
Lock & Unlock Storage Device: unlocking of one or more LBA ranges by the host and locking of those ranges 
under host control via either an explicit lock or implicit lock triggered by a reset event. MBR shadowing provides 
a mechanism to boot into a secure pre-boot authentication environment to handle device unlocking. 
• 
Repurpose & End-of-Life: erasure of data within one or more LBA ranges and reset of locking credential(s) for 
Storage Device repurposing or decommissioning.  
End of Informative Comment 
2.2 Security Providers (SPs) 
An Opal SSC compliant Storage Device SHALL support at least two Security Providers (SPs): 
1) Admin SP 
2) Locking SP 
The Locking SP MAY be created by the Storage Device manufacturer. 
2.3 Interface Communication Protocol 
An Opal SSC compliant Storage Device SHALL implement the synchronous communications protocol as defined in 
Section 3.3.4. 
This communication protocol operates based upon configuration information defined by:  
1) the values reported via Level 0 Discovery (see section 3.1.1);  
The combination of the host's communication properties and the TPer's communication properties (see section 
4.1.1.1). 
