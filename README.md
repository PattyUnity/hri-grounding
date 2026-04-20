# HRI Grounding: Visible and Actionable AI-Generated Plans

Companion repository for the paper:

> **HRI Grounding for Visible and Actionable AI-Generated Plans in Multi-Robot Supervisory Control**
> *IEEE Robotics and Automation Letters (RA-L)*

This repository provides example input artifacts and a prompt-assembly script for **Stage 1 (plan generation)** of the HRI grounding architecture. The generated plan is then consumed by the web-based interface engine in a separate repository for **Stages 2-3 (rendering and command binding)**.

> **Interface engine (Stages 2-3):** [mission-control-hub](https://github.com/user/mission-control-hub)
>
> **Video demonstration:** [YouTube](https://youtube.com/watch?v=PLACEHOLDER)

---

## What Is HRI Grounding?

HRI grounding is an architecture that automatically translates a context-aware robot task plan into an operator interface where each plan step is both **visible** (the operator sees what the robot will do) and **actionable** (the operator dispatches the robot command with a single confirmation).

The architecture has four runtime stages:

```
       STAGE 1                    STAGES 2-3                  STAGE 4
    Plan Generation            Grounding Layer            Command Dispatch

 Context                            ┌─────────────┐
 S, A, G ──┐                        │  Stage 2    │
            ├──► prompt ──► L        │  Render (R) │──► UI
 Instruction    │              P     │  Eq. 3      │    Vis
 I(F)    ──┘    ▼           ──────► ├─────────────┤
          LLM planner (L)           │  Stage 3    │         Operator confirms
                                     │  Bind (B)   │──► UI  ──► published to
          Plan P = L(S,A,G|I)       │  Eq. 4      │    Cmd     robot via ROS
          Eq. 2                      └─────────────┘            (Stage 4)
                                        ▲
                                        │
                                  Format Contract (F)
                                  + DTO registration
```

| Stage | Paper ref | What happens | Equation |
|-------|-----------|--------------|----------|
| **1** | Plan generation | Context (*S*, *A*, *G*) is combined with instruction *I*(*F*) — a prompt template parameterized by the format contract — to form the full prompt. An LLM planner produces plan *P*. | P = L(S, A, G \| I) &nbsp; (Eq. 2) |
| **2** | Rendering (R) | The visualization layer reads each plan step through the DTO and renders a human-readable interface element showing the action, target, robot, and parameters. | U = R(P \| F) &nbsp; (Eq. 3) |
| **3** | Binding (B) | The command layer constructs a ready-to-dispatch ROS command for each step. Parameters may include late-bound scene-object references resolved at dispatch time. | C = B(P \| S, A) &nbsp; (Eq. 4) |
| **4** | Dispatch | The operator reads the visualization and confirms or rejects. On confirmation, the bound command is published to the target robot via ROS. | — |

Stages 2 and 3 produce **co-located** interface elements: on the same control, the operator sees what the robot will do and dispatches the command with a single click.

### What this repo covers vs. the interface engine

| Concern | This repo (`hri-grounding`) | Interface engine (`mission-control-hub`) |
|---------|----------------------------|----------------------------------------|
| Stage 1 (plan generation) | Input artifacts + prompt assembly | — |
| Stage 2 (rendering) | — | `MissionButton.tsx` |
| Stage 3 (binding) | — | `useRosBridge.ts` |
| Format contracts (F) | Schema definitions (F1, F2) | Consumed via DTO registration |
| DTO schema | Canonical field definitions | TypeScript interface + `normalizeMissionPlan()` |

---

## Field Extension Procedure (Development Time)

The field extension procedure is a **development-time** customization process, separate from the runtime stages above. It defines how adopters add application-specific fields to the architecture.

```
  FIELD EXTENSION (development time)        HRI GROUNDING (runtime)
  ──────────────────────────────────        ───────────────────────

  Step 1: Define field in F          ───►   Used by Stage 1 (plan generation)
          (format contract)                 Planner includes the field in F which directs the structure of the plan P.

  Step 2: Register field in DTO      ───►   Prerequisite for Stages 2 & 3
          (parsing rules)                   Tells R and B how to consume P.

  Step 3: Update R (visualization)   ───►   Dev-time adjustment of Stage 2
          if field should be visible        R now renders the new field.

  Step 4: Update B (command layer)   ───►   Dev-time adjustment of Stage 3
          if field affects dispatch         B now includes the field in the command.
```

Steps 3 and 4 are conditional: a display-only field (e.g., `priority`) needs Steps 1-3 but not 4. A dispatch-only field (e.g., `timeout`) needs Steps 1, 2, and 4 but not 3. See [`docs/field_extension_guide.md`](docs/field_extension_guide.md) for a worked example.

---

## Repository Structure

```
hri-grounding/
├── artifacts/
│   ├── format-contracts/             # Shared format contract schemas
│   │   ├── format_contract_F1.json   #   F1 (flat) — field definitions
│   │   └── format_contract_F2.json   #   F2 (nested) — field definitions
│   ├── sar/                          # Search-and-rescue scenario
│   │   ├── inputs/                   #   Stage 1 inputs: S, A, G
│   │   │   ├── scene_graph.json      #     S — environment objects + locations
│   │   │   ├── robot_api.json        #     A — robot capabilities + ROS types
│   │   │   └── goal.json             #     G — operator goal + constraints
│   │   └── outputs/                  #   Stage 1 outputs: example plans P
│   │       ├── example_plan_F1.json  #     P generated with F1
│   │       └── example_plan_F2.json  #     P generated with F2
│   └── warehouse/                    # Warehouse order-packing scenario
│       ├── inputs/                   #   (same structure as sar/)
│       └── outputs/
├── plan-generation/
│   ├── assemble_prompt.py            # Combines context (S,A,G) with instruction I(F)
│   └── README.md
├── docs/
│   ├── architecture.md               # Four-stage runtime architecture
│   └── field_extension_guide.md      # Four-step development-time procedure
└── LICENSE
```

**How artifacts map to the equations:**

| File | Symbol | Role in Stage 1 |
|------|--------|-----------------|
| `scene_graph.json` | *S* | Environment objects with types, IDs, and spatial coordinates |
| `robot_api.json` | *A* | Robot capabilities and associated ROS message types |
| `goal.json` | *G* | Operator goal text and optional constraints |
| `format_contract_F*.json` | *F* | Structured schema specifying required plan output fields |
| `assemble_prompt.py` | prompt = S, A, G + *I*(*F*) | Combines context with instruction template into a single LLM prompt |
| `example_plan_F*.json` | *P* | Example plan output (generated by an LLM given *I*) |

Both scenarios (SAR and warehouse) share the same format contracts F1 and F2 and the same prompt template *I*. Only *S*, *A*, and *G* differ per scenario.

---

## Getting Started

### Tutorial 1: Generate a plan using an existing format contract (F1 or F2)

Use the provided artifacts and prompt-assembly script to produce a plan *P* from any LLM.

```bash
cd plan-generation

# Assemble the instruction package I for SAR with F1
python assemble_prompt.py \
    --scene  ../artifacts/sar/inputs/scene_graph.json \
    --api    ../artifacts/sar/inputs/robot_api.json \
    --goal   ../artifacts/sar/inputs/goal.json \
    --format ../artifacts/format-contracts/format_contract_F1.json \
    --out    prompt.txt

# Send prompt.txt to any LLM API (OpenAI, Anthropic, Google, etc.)
# The response is a JSON plan P whose fields match F1.
```

To see what P looks like, check `artifacts/sar/outputs/example_plan_F1.json`.

### Tutorial 2: Render a plan as an operator interface (Stages 2-3)

Feed a generated plan (or an example plan from `outputs/`) to the web interface engine:

> **[mission-control-hub](https://github.com/user/mission-control-hub)**

The interface engine parses *P* through the DTO, renders each step as an interactive control (Stage 2), and binds each control to a ROS command (Stage 3). The operator confirms or rejects each step with a single click (Stage 4).

### Tutorial 3: Define a custom scenario

Create three JSON files following the schemas in `artifacts/sar/inputs/`:

1. **Scene graph** (`scene_graph.json`) — objects with type, ID, and x/y/z location
2. **Robot API** (`robot_api.json`) — robots with model name, context, and available actions (each with ROS message type)
3. **Goal** (`goal.json`) — natural-language goal text and optional constraints

Then run `assemble_prompt.py` with an existing format contract (F1 or F2) to generate the instruction package.

### Tutorial 4: Define a custom format contract and extend the architecture

To add application-specific fields beyond the canonical set, follow the four-step field extension procedure:

1. **Define the new field in F** — add it to the format contract JSON so the planner includes it in *P*
2. **Register in the DTO** — update the parsing logic so Stages 2-3 can consume the new field
3. **Update rendering (R)** — if the field should be visible to the operator
4. **Update binding (B)** — if the field affects command construction or dispatch

See [`docs/field_extension_guide.md`](docs/field_extension_guide.md) for a worked example with `priority` and `estimated_duration`.

---

## Format Contracts: F1 vs F2

| Property | F1 (flat) | F2 (nested) |
|----------|-----------|-------------|
| Structure | All fields at top level | Fields grouped under `parameters` |
| Robot field | `robot_ns` | `robot_name` |
| Position | Inside `params.position` | `target_position` at parameter level |
| ROS type | `msg` | `ros_message_type` |
| DTO registration | Direct field mapping (Step 2 of extension procedure) | Extraction rule unwraps `parameters` sub-object |

Both formats are parsed into DTO entries through their respective registration rules (field extension Step 2). After registration, Stages 2 (rendering) and 3 (binding) consume the DTO identically regardless of which format contract produced the plan.

---

## Paper Scenarios

### Search and Rescue (SAR)
Three robots (two legged robots, one aerial drone) must extinguish four fires and deliver first-aid kits to three survivors. Constraint: each extinguisher can handle only two fires.

### Warehouse Order Packing
Three robots (two wheeled UGVs, one aerial UAV) must pick items from shelves and pack three customer orders into respective boxes and drop at a collection point once the packing is done. Constraint: UGVs carry 3 items, UAVs carry 2; only UAVs can pack and only UGVs can move the packed boxes.

---

## Citation

```bibtex
@article{hrigrounding2025,
  title   = {{HRI} Grounding for Visible and Actionable {AI}-Generated Plans
             in Multi-Robot Supervisory Control},
  journal = {IEEE Robotics and Automation Letters},
  year    = {2025}
}
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
