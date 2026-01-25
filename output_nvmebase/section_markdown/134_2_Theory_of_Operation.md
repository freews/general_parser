## 2 Theory of Operation

> **Section ID**: 2 | **Page**: 42-44

The NVM Express scalable interface is designed to address the needs of storage systems that utilize PCI
Express based solid state drives or fabric connected devices. The interface provides optimized command
submission and completion paths. It includes support for parallel operation by supporting up to 65,535 I/O
Queues with up to 65,535 outstanding commands per I/O Queue. Additionally, support has been added for
many Enterprise capabilities like end-to-end data protection (compatible with SCSI Protection Information,
commonly known as T10 DIF, and SNIA DIX standards), enhanced error reporting, and virtualization.
The interface has the following key attributes:
•
Does not require uncacheable / MMIO register reads in the command submission or completion
path;
•
A maximum of one MMIO register write or one 64B message is necessary in the command
submission path;
•
Support for up to 65,535 I/O Queues, with each I/O Queue supporting up to 65,535 outstanding
commands;
•
Priority associated with each I/O Queue with well-defined arbitration mechanism;
•
All information to complete a 4 KiB read request is included in the 64B command itself, ensuring
efficient small I/O operation;
•
Efficient and streamlined command set;
•
Support for MSI/MSI-X and interrupt aggregation;
•
Support for multiple namespaces;
•
Efficient support for I/O virtualization architectures like SR-IOV;
•
Robust error reporting and management capabilities; and
•
Support for multi-path I/O and namespace sharing.
This specification defines a streamlined set of properties that are used to configure low level controller
attributes and obtain low level controller status. These properties have a transport specific mechanism for
defining access (e.g., memory-based transports use registers, whereas message-based transports use the
Property Get and Property Set commands). The following are examples of functionality defined in
properties:
•
Indication of controller capabilities;
•
Status for controller failures (command status is provided in a CQE);
•
Admin Queue configuration (I/O Queue configuration processed via Admin commands); and
•
Doorbell registers (refer to the NVMe over PCIe Transport Specification) for a scalable number of
Submission and Completion Queues.
There are two defined models for communication between the host and the NVM subsystem, a memory-
based transport model and a message-based transport model. All NVM subsystems require the underlying
NVMe Transport to provide reliable NVMe command and data delivery. An NVMe Transport is an abstract
protocol layer independent of any physical interconnect properties. A taxonomy of NVMe Transports, along
with examples, is shown in Figure 4. An NVMe Transport may expose a memory-based transport model or
a message-based transport model. The message-based transport model has two subtypes: the message-
only transport model and the message/memory transport model.
A memory-based transport model is one in which commands, responses, and data are transferred between
a host and an NVM subsystem by performing explicit memory read and write operations (e.g., over PCIe).
A message-based transport model is one in which messages containing command capsules and response
capsules are sent between a host and an NVM subsystem (e.g., over a fabric). The two subtypes of
message-based transport models are differentiated by how data is sent between a host and an NVM
subsystem. In the message-only transport model data is only sent between a host and an NVM subsystem
using capsules or messages. The message/memory transport model uses a combination of messages and
explicit memory read and write operations to transfer command capsules, response capsules and data
between a host and an NVM subsystem. Data may optionally be included in command capsules and
response capsules. Both the message-only transport model and the message/memory transport model are
referenced as message-based transport models throughout this specification when the description is
applicable to both subtypes.
An NVM subsystem is made up of a single domain or multiple domains as described in section 3.2.5. An
NVM subsystem may optionally include a non-volatile storage medium, and an interface between the
controller(s) of the NVM subsystem and the non-volatile storage medium. Controllers expose this non-
volatile storage medium to hosts through namespaces. An NVM subsystem is not required to have the
same namespaces attached to all controllers. An NVM subsystem that supports a Discovery controller does
not support any other controller type. A Discovery Service is an NVM subsystem that supports Discovery
controllers only (refer to section 3.1).
The capabilities and settings that apply to an NVM Express controller are indicated in the Controller
Capabilities (CAP) property and the Identify Controller data structure (refer to Figure 328).
A namespace is a set of resources (e.g., formatted non-volatile storage) that may be accessed by a host.
A namespace has an associated namespace identifier that a host uses to access that namespace. The set
of resources may consist of non-volatile storage and/or other resources.
Associated with each namespace is an I/O Command Set that operates on that namespace. An NVM
Express controller may support multiple namespaces. Namespaces may be created and deleted using the
Namespace Management command and Capacity Management command. The Identify Namespace data
structures (refer to section 1.5.50) indicate capabilities and settings that are specific to a particular
namespace.
The NVM Express interface is based on a paired Submission and Completion Queue mechanism.
Commands are placed by a host into a Submission Queue. Completions are placed into the associated
Completion Queue by the controller.
There are three types of commands that are defined in NVM Express: Admin commands, I/O commands
and Fabrics commands. Figure 5 shows these different command types.
An Admin Submission Queue and associated Completion Queue exist for the purpose of controller
management and control (e.g., creation and deletion of I/O Submission and Completion Queues, aborting
commands, etc.). Only commands that are part of the Admin Command Set or the Fabrics Command Set
may be submitted to the Admin Submission Queue.
An I/O Command Set is used with an I/O queue pair. This specification defines common I/O commands.
I/O Command Sets are defined in the NVM Express I/O Command Set specifications. The example I/O
Command Sets shown in Figure 5 are the NVM Command Set, the Key Value Command Set, and the
Zoned Namespace Command Set. Other I/O Command Sets include the Computational Programs
Command Set and the SLM Command Set.
The Fabrics Command Set is NVMe over Fabrics specific. Fabrics Command Set commands are used for
operations specific to NVMe over Fabrics including establishing a connection, NVMe in-band
authentication, and to get or set a property. All Fabrics commands may be submitted on the Admin
Submission Queue and some Fabrics commands may also be submitted on an I/O Submission Queue.
Unlike Admin and I/O commands, Fabrics commands are processed by a controller regardless of whether
the controller is enabled (i.e., regardless of the state of CC.EN).
