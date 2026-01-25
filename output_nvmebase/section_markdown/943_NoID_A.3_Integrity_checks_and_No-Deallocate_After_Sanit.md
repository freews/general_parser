### A.3 Integrity checks and No-Deallocate After Sanitize

> **Section ID**:  | **Page**: 773-773

Another issue is availability of the data returned through the interface. Some of the sanitize operations (e.g.,
Block Erase) affect the physical devices in such a way that directly reading the accessible storage may
trigger internal integrity checks resulting in error responses instead of returning the contents of the storage.
Other sanitize operations (e.g., Crypto Erase) may scramble the vendor specific internal format of the data,
also resulting in error responses instead of returning the contents of the storage.
To compensate for these issues, a controller may perform additional internal write operations to media that
is able to be allocated for user data (i.e., additional media modification, refer to section 8.1.26.2) so that all
media in the sanitization target that is allocated for user data is readable without error. However, this has
the side effect of potentially significant additional wear on the media as well as the side effect of obscuring
the results of the initial sanitize operation (i.e., the writes destroy the ability to forensically audit the result
of the initial sanitize operation). Given this side effect, process audits of sanitize behavior only provide
effective results when the No-Deallocate After Sanitize bit is set the same way (e.g., set to ‘1’) for both
process audits and the individual forensic device audits.
The Sanitize command introduced in NVM Express Base Specification, Revision 1.3 included a mechanism
to specify that sanitized media in the NVM subsystem that is allocated for user data not be deallocated,
thereby allowing observations of the results of the sanitization operation. However, some architectures and
products (e.g., integrity checking circuitry) interact with this capability in such a way as to defeat the sanitize
result observability purpose. New features were added to NVM Express Base Specification, Revision 1.4
that include extended information about the sanitization capabilities of devices, a new asynchronous event,
and configuration of the response to No-Deallocate After Sanitize requests. These features are intended to
both support new systems that understand the new capabilities, as well as to help manage legacy systems
that do not understand the new capabilities without losing the ability to sanitize as requested.
These issues in returning the contents of accessible storage do not apply if the sanitization target is in the
Media Verification state (refer to section 8.1.26.4.6). In that state, failure of internal integrity checks do not
cause error responses to Read commands (refer to the Media Verification section of the NVM Express
NVM Command Set Specification). Because the command that caused entry to the Media Verification state
specified the Enter Media Verification State (EMVS) bit set to ‘1’, the controller does not perform the
additional media modification described in this section.
