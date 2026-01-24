#### B.5.2. Example Algorithm for Controller Doorbell Property Updates

> **Section ID**:  | **Page**: 779-779

The host may use modular arithmetic where the modulus is the queue depth to decide if the controller
doorbell property should be updated, specifically:
•
Compute X as the new doorbell value minus the corresponding EventIdx value, modulo queue
depth; and
•
Compute Y as the new doorbell value minus the old doorbell value in the shadow doorbell buffer,
also modulo queue depth.
If X is less than or equal to Y, the controller doorbell property should be updated with the new doorbel
value.
