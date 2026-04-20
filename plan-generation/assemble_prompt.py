"""
Assemble an instruction package I from the four input artifacts.

Stage 1 (Plan Generation) in the HRI grounding architecture:
    prompt = context(S, A, G) + instruction I(F)
    P = L(S, A, G | I)   (Eq. 2 in the paper)

The prompt combines context data — scene graph (S), robot API (A), and
operator goal (G) — with the instruction template I(F), which tells the
LLM how to consume S, A, G and structure its output according to format
contract F.  The planner L returns a plan P whose fields match F.

Usage:
    python assemble_prompt.py \
        --scene  ../artifacts/sar/inputs/scene_graph.json \
        --api    ../artifacts/sar/inputs/robot_api.json \
        --goal   ../artifacts/sar/inputs/goal.json \
        --format ../artifacts/format-contracts/format_contract_F1.json \
        [--out instruction_package.txt]

Note: The format contract F is used as the response structure specification
in the prompt.  It tells the LLM what fields each plan step must contain.
The example plans in artifacts/*/outputs/ are LLM-generated outputs — they
are NOT part of the prompt assembly.
"""

import argparse
import json
import sys
from pathlib import Path


def load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def assemble(scene: dict, api: dict, goal: dict, format_contract: dict) -> str:
    """Return the assembled prompt: context(S, A, G) + instruction I(F)."""
    scene_str = json.dumps(scene, separators=(",", ":"))
    api_str = json.dumps(api, separators=(",", ":"))
    format_str = json.dumps(format_contract, separators=(",", ":"))

    # Goal text is used as-is (may include constraints in natural language)
    goal_text = goal.get("goal", "")
    constraints = goal.get("constraints", "")
    full_goal = f"{goal_text} {constraints}".strip() if constraints else goal_text

    prompt = (
        f"Tool Awareness: Given robot APIs; <{api_str}>. "
        f"Robot cannot perform actions not listed in their API pool. "
        f"Environment Awareness: Assume map and object locations are known "
        f"from prior exploration and described in the scene graph; <{scene_str}>."
        f"Role: Generate a sequential, task-allocation plan using the robot "
        f"capabilities in the APIs and specific detail in scene graph above "
        f"to achieve the goal: {full_goal}. "
        f"Instruction: Follow the structure in the example: <{format_str}>, "
        f"generate 'mission_plan' in valid JSON. No explanations or markdown."
        f"Use coordinates, names, field name EXACTLY from the scene graph "
        f"and robot APIs (not the example). "
    )

    return prompt


def main():
    parser = argparse.ArgumentParser(
        description="Assemble an HRI grounding prompt: context(S, A, G) + instruction I(F)."
    )
    parser.add_argument("--scene", required=True, help="Path to scene_graph.json (S)")
    parser.add_argument("--api", required=True, help="Path to robot_api.json (A)")
    parser.add_argument("--goal", required=True, help="Path to goal.json (G)")
    parser.add_argument(
        "--format", required=True,
        help="Path to format_contract .json (F) — specifies required plan output fields"
    )
    parser.add_argument("--out", help="Output file path. If omitted, prints to stdout.")
    args = parser.parse_args()

    scene = load_json(args.scene)
    api = load_json(args.api)
    goal = load_json(args.goal)
    format_contract = load_json(args.format)

    prompt = assemble(scene, api, goal, format_contract)

    if args.out:
        Path(args.out).write_text(prompt, encoding="utf-8")
        print(f"Instruction package written to {args.out}")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
