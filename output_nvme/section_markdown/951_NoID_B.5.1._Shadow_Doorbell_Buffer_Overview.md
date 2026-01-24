#### B.5.1. Shadow Doorbell Buffer Overview

> **Section ID**:  | **Page**: 778-779

Controllers that support the Doorbell Buffer Config command are typically emulated controllers where this
feature is used to enhance the performance of the host running in Virtual Machines. If supported by the
controller, the host may enable Shadow Doorbell buffers by submitting the Doorbell Buffer Config command
(refer to section 5.3.5).
After the completion of the Doorbell Buffer Config command, the host shall submit commands by updating
the appropriate entry in the Shadow Doorbell buffer instead of updating the controller's corresponding
doorbell property. If updating an entry in the Shadow Doorbell buffer changes the value from being less
than or equal to the value of the corresponding EventIdx buffer entry to being greater than that value, then
the host shall also update the controller's corresponding doorbell property to match the value of that entry
in the Shadow Doorbell buffer. Queue wrap conditions shall be taken into account in all comparisons in this
paragraph.
The controller may read from the Shadow Doorbell buffer and update the EventIdx buffer at any time (e.g.
before the host writes to the controller's doorbell property).
