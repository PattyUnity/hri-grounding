# Plan Generation (Stage 1)

This directory contains the prompt-assembly script for **Stage 1** of the HRI grounding architecture: assembling the four input artifacts into an instruction package *I* that an LLM converts into a mission plan *P*.

```
  Context:                                   Instruction:
  S (scene graph)     ──┐                    I(F) ──┐
  A (robot API)       ──┤                           │
  G (operator goal)   ──┼──► assemble_prompt.py ◄───┘
                                    │
                                    ▼
                              full prompt
                                    │
                                    ▼
                              LLM planner (L)
                                    │
                                    ▼
                              Plan P = L(S,A,G|I)     ← JSON matching F
```

## Prompt Structure

The prompt template (inside `assemble_prompt.py`) has four injection points corresponding to the four artifacts:

1. **Tool Awareness** — injects *A* (robot API): available actions and ROS message types per robot
2. **Environment Awareness** — injects *S* (scene graph): objects with types, IDs, and coordinates
3. **Role** — injects *G* (goal and constraints): what the robot team must achieve
4. **Instruction** — injects *F* (format contract): the required output structure for each plan step

The prompt is model-agnostic. In the paper, plans were generated with GPT-5.2, GPT-5, GPT-5-mini,Gemini 2.5 Pro, and Gemini 3 Pro Preview using identical prompts.

## Usage

```bash
# SAR scenario, F1 format
python assemble_prompt.py \
    --scene  ../artifacts/sar/inputs/scene_graph.json \
    --api    ../artifacts/sar/inputs/robot_api.json \
    --goal   ../artifacts/sar/inputs/goal.json \
    --format ../artifacts/format-contracts/format_contract_F1.json \
    --out    instruction_package.txt

# Warehouse scenario, F2 format
python assemble_prompt.py \
    --scene  ../artifacts/warehouse/inputs/scene_graph.json \
    --api    ../artifacts/warehouse/inputs/robot_api.json \
    --goal   ../artifacts/warehouse/inputs/goal.json \
    --format ../artifacts/format-contracts/format_contract_F2.json \
    --out    instruction_package.txt
```

The output `instruction_package.txt` is the complete prompt string ready to submit to any LLM API.

## Output

The LLM returns a JSON object whose structure matches the format contract *F*. Example outputs are provided in `artifacts/*/outputs/`. These example plans were generated during the paper's Study 1 evaluation.
