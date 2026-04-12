"""
Convert all 3 council workflows from parallel to sequential expert execution
and upgrade model from qwen2.5:7b to deepseek-r1:32b.
"""
import json
import os

BASE = r"c:\saleh26\salehsaas\SaleHSaaS3\n8n\workflows"
NEW_MODEL = "deepseek-r1:32b"
OLD_MODEL = "qwen2.5:7b"


def upgrade_model(workflow):
    """Replace all occurrences of OLD_MODEL with NEW_MODEL in jsonBody fields."""
    count = 0
    for node in workflow.get("nodes", []):
        params = node.get("parameters", {})
        if "jsonBody" in params and OLD_MODEL in params["jsonBody"]:
            params["jsonBody"] = params["jsonBody"].replace(OLD_MODEL, NEW_MODEL)
            count += 1
    return count


def patch_innovation(workflow):
    """Convert innovation council: parallel experts → sequential chain."""
    conns = workflow["connections"]

    # merge_context → expert_entrepreneur only (was: fan-out to 3)
    conns["merge_context"]["main"][0] = [
        {"node": "expert_entrepreneur", "type": "main", "index": 0}
    ]

    # expert_entrepreneur → expert_tech (was: → collect_votes)
    conns["expert_entrepreneur"]["main"][0] = [
        {"node": "expert_tech", "type": "main", "index": 0}
    ]

    # expert_tech → expert_strategy (was: → collect_votes)
    conns["expert_tech"]["main"][0] = [
        {"node": "expert_strategy", "type": "main", "index": 0}
    ]

    # expert_strategy → collect_votes (unchanged)
    # Already correct

    model_count = upgrade_model(workflow)
    print(f"  Innovation: sequential chain applied, {model_count} model refs updated")


def patch_tech_governance(workflow):
    """Convert tech governance council: parallel experts → sequential chain."""
    conns = workflow["connections"]

    # merge_context → expert_security only (was: fan-out to 3)
    conns["merge_context"]["main"][0] = [
        {"node": "expert_security", "type": "main", "index": 0}
    ]

    # expert_security → expert_architecture (was: → collect_opinions)
    conns["expert_security"]["main"][0] = [
        {"node": "expert_architecture", "type": "main", "index": 0}
    ]

    # expert_architecture → expert_quality (was: → collect_opinions)
    conns["expert_architecture"]["main"][0] = [
        {"node": "expert_quality", "type": "main", "index": 0}
    ]

    # expert_quality → collect_opinions (unchanged)

    model_count = upgrade_model(workflow)
    print(f"  Tech Governance: sequential chain applied, {model_count} model refs updated")


def patch_legal_review(workflow):
    """Convert legal review: parallel analysts/rebuttals → sequential chains."""
    conns = workflow["connections"]

    # Round 1: merge_context → analyst_affirmative only (was: fan-out to 2)
    conns["merge_context"]["main"][0] = [
        {"node": "analyst_affirmative", "type": "main", "index": 0}
    ]

    # analyst_affirmative → analyst_negative (was: → collect_debate_r1)
    conns["analyst_affirmative"]["main"][0] = [
        {"node": "analyst_negative", "type": "main", "index": 0}
    ]

    # analyst_negative → collect_debate_r1 (unchanged)

    # Round 2: collect_debate_r1 → rebuttal_affirmative only (was: fan-out to 2)
    conns["collect_debate_r1"]["main"][0] = [
        {"node": "rebuttal_affirmative", "type": "main", "index": 0}
    ]

    # rebuttal_affirmative → rebuttal_negative (was: → collect_debate_r2)
    conns["rebuttal_affirmative"]["main"][0] = [
        {"node": "rebuttal_negative", "type": "main", "index": 0}
    ]

    # rebuttal_negative → collect_debate_r2 (unchanged)

    model_count = upgrade_model(workflow)
    print(f"  Legal Review: sequential chains applied (2 rounds), {model_count} model refs updated")


PATCHES = {
    "council_innovation": patch_innovation,
    "council_tech_governance": patch_tech_governance,
    "council_legal_review": patch_legal_review,
}

for name, patch_fn in PATCHES.items():
    for suffix in ["", "_import"]:
        filepath = os.path.join(BASE, f"{name}{suffix}.json")
        if not os.path.exists(filepath):
            print(f"  SKIP (not found): {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both single workflow and array format
        if isinstance(data, list):
            workflow = data[0]
        else:
            workflow = data

        print(f"\nPatching: {name}{suffix}.json")
        patch_fn(workflow)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  Saved: {filepath}")

print("\n✅ All 3 councils converted to sequential + deepseek-r1:32b")
