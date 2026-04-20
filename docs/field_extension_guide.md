# Field Extension Guide (Development Time)

This guide explains how to add a new field to the HRI grounding architecture. The four-step **field extension procedure** is a development-time process that customizes the runtime pipeline.

> **Important distinction:** The field extension procedure (4 development-time steps) is separate from the HRI grounding architecture (4 runtime stages). Each extension step prepares a specific runtime stage to handle the new field. See the mapping below.

## The Four Steps

```
  FIELD EXTENSION (development time)         HRI GROUNDING (runtime)
  ──────────────────────────────────         ───────────────────────

  Step 1: Define field in F           ───►   Affects Stage 1 (plan generation)
          format contract                    Planner includes the field in P.

  Step 2: Register field in DTO       ───►   Prerequisite for Stages 2 & 3
          parsing rules                      Tells R and B how to consume P.

  Step 3: Update R (visualization)    ───►   Dev-time adjustment of Stage 2
          rendering logic                    R now renders the new field.

  Step 4: Update B (command layer)    ───►   Dev-time adjustment of Stage 3
          binding logic                      B now includes the field in cmd.
```

Steps 3 and 4 are conditional depending on the field's purpose:

| Field purpose | Steps needed | Example |
|---|---|---|
| Display-only (operator sees it) | 1, 2, 3 | `priority` |
| Dispatch-only (affects command) | 1, 2, 4 | `timeout` |
| Both display and dispatch | 1, 2, 3, 4 | `estimated_duration` |

---

### Step 1: Define the field in the format contract (F)

Add the new field to the format contract JSON. This tells the LLM planner (Stage 1) to include it in each command step of the generated plan *P*.

**Example:** Adding a `priority` field to F1.

```json
{
  "fields": {
    "robot_ns": "string",
    "action": "string",
    "target_object": "string",
    "obj_id": "integer",
    "params": "object",
    "msg": "string",
    "priority": "string — low | medium | high"
  },
  "example_step": {
    "robot_ns": "/robot1",
    "action": "move",
    "target_object": "Extinguisher",
    "obj_id": 1,
    "params": { "position": { "x": 1.6, "y": -0.6, "z": 0.0 } },
    "msg": "geometry_msgs/PoseStamped",
    "priority": "high"
  }
}
```

**Runtime effect:** When the instruction package *I* is assembled with this updated *F*, the LLM will produce plan steps that include a `priority` value.

---

### Step 2: Register the field in the DTO schema

Add the field to the DTO definition and update the parsing logic so that Stages 2 (rendering) and 3 (binding) can consume it. This step is a **prerequisite** for both downstream stages — without registration, the new field in *P* would be ignored.

For the TypeScript/React implementation, update the `ActionParameters` interface in `mission.ts`:

```typescript
export interface ActionParameters {
  robot_name: string;
  target_position: TargetPosition;
  target_object: string;
  object_id: number;
  ros_message_type: string;
  params?: any;
  priority?: string;  // ← new field
}
```

If using F2 (nested), also update the extraction rule in `normalizeMissionPlan()` so the parser knows where to find the field inside the `parameters` sub-object.

**Runtime effect:** After DTO registration, every plan step parsed from *P* will carry the `priority` field in its DTO entry, available for Stages 2 and 3 to consume.

---

### Step 3: Update rendering if the field should be visible (Stage 2)

If the new field should be visible to the operator, update the visualization layer *R* to display it. For example, a `priority` field might be rendered as a colored label on the interface element:

- `high` → red label
- `medium` → yellow label
- `low` → grey label

For the TypeScript/React implementation, update `MissionButton.tsx` to read `action.parameters.priority` and render accordingly.

If the field is purely for command construction (not operator-facing), skip this step.

---

### Step 4: Update binding if the field affects dispatch (Stage 3)

If the new field changes how the robot command is constructed or dispatched, update the command layer *B*. For example, a `timeout` field might set a deadline on the ROS action call, or an `execution_speed` field might be included in the command payload.

For the TypeScript/React implementation, update `publishAction()` in `useRosBridge.ts` to read the new DTO field and incorporate it into the ROS message.

If the field is purely informational (display-only), skip this step.

---

## Worked Example: F1 vs F2

Suppose you add `estimated_duration` (in seconds) to both format contracts. This field is both display and dispatch, so all four steps apply.

**F1 (flat):** The field appears at the top level of each plan step.
```json
{
  "robot_ns": "/robot1",
  "action": "move",
  "target_object": "Fire",
  "obj_id": 1,
  "params": { "position": { "x": 6.56, "y": -5.84, "z": 0.0 } },
  "msg": "geometry_msgs/PoseStamped",
  "estimated_duration": 12
}
```

**F2 (nested):** The field appears inside the `parameters` sub-object.
```json
{
  "action": "move",
  "parameters": {
    "robot_name": "robot1",
    "target_object": "Fire",
    "object_id": 1,
    "target_position": { "x": 6.56, "y": -5.84, "z": 0.0 },
    "ros_message_type": "geometry_msgs/PoseStamped",
    "estimated_duration": 12
  }
}
```

**DTO (after registration, Step 2):** Both produce the same entry.
```json
{
  "action": "move",
  "robot_name": "robot1",
  "target_object": "Fire",
  "object_id": 1,
  "target_position": { "x": 6.56, "y": -5.84, "z": 0.0 },
  "ros_message_type": "geometry_msgs/PoseStamped",
  "estimated_duration": 12
}
```

The two format contracts define different plan structures (Step 1), and the DTO registration rules (Step 2) normalize them into the same internal representation. Rendering (Step 3) and binding (Step 4) then operate identically regardless of which format contract produced the plan.
