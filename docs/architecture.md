# HRI Grounding Architecture (Runtime)

The HRI grounding architecture translates an AI-generated multi-robot plan into an operator interface in four runtime stages. This document walks through each stage, the equations from the paper, and how the format contract and DTO connect them.

## Overview

The full pipeline (Eq. 1 in the paper):

```
Context (S, A, G) + Instruction I(F) ──L──► P ──R──► U,    P ──B──► C
```

The four runtime stages:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                      HRI Grounding Architecture                           │
│                                                                           │
│  Context: S (scene graph), A (robot API), G (goal)                        │
│  Instruction: I(F) — prompt template parameterized by format contract F   │
│                                                                           │
│  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐   │
│  │  STAGE 1     │  │  STAGE 2    │  │  STAGE 3    │  │  STAGE 4       │   │
│  │  Plan Gen.   │─►│  Render (R) │  │  Bind (B)   │─►│  Dispatch      │   │
│  │              │  │             │  │             │  │                │   │
│  │ S,A,G + I(F) │  │ DTO → UI    │  │ DTO → UI    │  │ Operator       │   │
│  │  → prompt    │  │ Vis         │  │ Cmd ────────│──│► confirms →    │   │
│  │ P=L(S,A,G|I) │  │             │  │             │  │ publish to ROS │   │
│  └──────────────┘  └──────┬──────┘  └──────┬──────┘  └────────────────┘   │
│                           │                │                              │
│                           └───────┬────────┘                              │
│                                   │                                       │
│                          Co-located on the                                │
│                          same interface element                           │
│                                                                           │
│  Format contract F specifies plan step fields (DTO schema, center of      │
│  Fig. 1 in the paper). The grounding layer consumes the DTO for           │
│  rendering (R) and binding (B).                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

## Stage 1: Plan Generation

**Equation:** P = L(S, A, G | I) &ensp; (Eq. 2)

**Context:** S (scene graph), A (robot API), G (operator goal)
**Instruction:** I(F) — prompt template parameterized by format contract F
**Output:** Mission plan P — a JSON array of command steps

The context artifacts (S, A, G) are combined with the instruction template I(F) to form the full prompt. I(F) contains the natural-language instructions that tell the LLM how to consume S, A, G and structure its output according to F. The planner *L* returns a plan P whose fields match *F*.

This is the only stage that involves an LLM. Stages 2-4 are deterministic.

The architecture is model-agnostic: any LLM that can produce valid JSON from a structured prompt works. The paper tested five planner models across two providers.

**What can vary at runtime:** S and G may change between missions or during execution (e.g., a new operator goal triggers replanning). A, F, and the instruction template I(F) are typically fixed per system configuration.

## Stage 2: Rendering (R) — Visualization Layer

**Equation:** U = R(P | F) &ensp; (Eq. 3)

**Input:** Plan P (through DTO entries)
**Output:** Visual interface elements (UI_Vis)

Each command step c_i in P is rendered as a human-readable interface element showing the assigned robot, action type, target object, and spatial parameters. This is the "visible" half of the co-located control.

The rendering logic consumes DTO fields and is independent of which format contract variant (F1 or F2) produced the plan — the DTO registration (field extension Step 2) normalizes the differences before rendering.

Two rendering implementations were tested in the paper: a C#/Unity mixed-reality application (Study 2) and a TypeScript/React web application (configuration sweep and physical demo).

## Stage 3: Binding (B) — Command Layer

**Equation:** C = B(P | S, A) &ensp; (Eq. 4)

**Input:** Plan P (through DTO entries), scene graph S, robot API A
**Output:** ROS command payloads (UI_Cmd)

Each command step c_i is bound to a robot command specification: the ROS topic name (derived from robot name and action), message type (from DTO field `ros_message_type`), and parameter payload.

The payload is constructed per `ros_message_type` from the DTO fields. For movement commands (`geometry_msgs/PoseStamped`), the payload includes the target position. For boolean triggers (`std_msgs/Bool`), the payload is a simple data flag. Parameters may include **late-bound scene-object references** that are resolved against the live scene graph *S* at the time of command dispatch, enabling real-time parameter binding.

The dispatch is transport-agnostic: the ROS message can be sent via ROS-TCP Connector or RosBridge WebSocket; the format contract and binding logic are unaffected by the choice of transport.

## Stage 4: Command Dispatch

**Input:** Bound command from Stage 3, operator confirmation
**Output:** ROS message published to target robot

When the operator confirms an action, the bound command from Stage 3 — the payload constructed per `ros_message_type` — is published to the target robot on `topicName` through standard ROS middleware. The operator reads the visualization (Stage 2) and dispatches the command (Stage 3) on the same interface element, so understanding and execution happen in one place.

## The Format Contract

The format contract *F* serves two roles simultaneously:

1. **At development time** — it **decouples** the stages. Planners and interface engines connect only through the shared field schema and can be swapped independently. A new planner or a new UI platform only needs to respect the same field definitions.

2. **At runtime** — it **couples** context-aware content back into the interface. A different environment (*S*), robot team (*A*), or operator goal (*G*) produces a different plan, and the format contract ensures that plan carries exactly the fields the grounding layer needs to generate the matching interface.

## Relationship to Field Extension

The field extension procedure (see [`field_extension_guide.md`](field_extension_guide.md)) is the **development-time** process for customizing this runtime architecture. Each extension step maps to a specific runtime stage:

| Extension step | What it customizes | Runtime effect |
|---|---|---|
| Step 1: Define field in F | Stage 1 input | Planner includes the new field in P |
| Step 2: Register in DTO | Prerequisite for Stages 2-3 | Parsing logic maps the new field for R and B |
| Step 3: Update R | Stage 2 adjustment | Visualization layer renders the new field |
| Step 4: Update B | Stage 3 adjustment | Command layer includes the new field in dispatch |
