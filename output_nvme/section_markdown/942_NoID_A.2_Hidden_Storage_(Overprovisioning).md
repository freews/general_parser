### A.2 Hidden Storage (Overprovisioning)

> **Section ID**:  | **Page**: 773-773

Sanitize operations purge all physical storage in the sanitization target that is able to hold user data. Many
NVMe SSDs contain more physical storage than is addressable through the interface (e.g.,
overprovisioning). That physical storage is used for vendor specific purposes which may include providing
increasing endurance, improving performance, and providing extra capacity to allow retiring bad or worn-
out storage without affecting capacity. This excess capacity as well as any retired storage are not accessible
through the interface. Vendor specific innovative use of this extra capacity supports advantages to the end
user, but the lack of observability makes it difficult to ensure that all storage within the sanitization target
was correctly purged. Only the accessible storage is able to be audited for the results of a sanitization
operation.
