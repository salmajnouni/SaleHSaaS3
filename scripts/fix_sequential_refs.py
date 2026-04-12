"""
Fix sequential expert nodes: each expert should reference $('merge_context')
instead of $json for question/webContext/ragContext, since in sequential mode
$json comes from the previous expert's HTTP response, not from merge_context.
"""
import json
import os
import re

BASE = r"c:\saleh26\salehsaas\SaleHSaaS3\n8n\workflows"

# ============================================================
# The fix: In expert jsonBody, replace $json.X with
# $('merge_context').first().json.X for question/webContext/ragContext
# ============================================================
FIELD_REPLACEMENTS = {
    "$json.question": "$('merge_context').first().json.question",
    "$json.webContext": "$('merge_context').first().json.webContext",
    "$json.ragContext": "$('merge_context').first().json.ragContext",
}

# Expert node name patterns (all councils)
EXPERT_NODES = {
    # Innovation
    "expert_entrepreneur", "expert_tech", "expert_strategy",
    # Tech Governance
    "expert_security", "expert_architecture", "expert_quality",
    # Legal Review  
    "analyst_affirmative", "analyst_negative",
    "rebuttal_affirmative", "rebuttal_negative",
}

# For legal review rebuttals, they reference collect_debate_r1 data
# rebuttal_affirmative and rebuttal_negative use $json.question, 
# $json.affirmativeArg, $json.negativeArg which come from collect_debate_r1
# In sequential mode, rebuttal_negative receives rebuttal_affirmative's output
# So rebuttals also need explicit node references
REBUTTAL_FIELD_REPLACEMENTS = {
    "$json.question": "$('collect_debate_r1').first().json.question",
    "$json.affirmativeArg": "$('collect_debate_r1').first().json.affirmativeArg",
    "$json.negativeArg": "$('collect_debate_r1').first().json.negativeArg",
}


def fix_expert_refs(workflow, council_name):
    """Fix expert nodes to use explicit node references instead of $json."""
    count = 0
    for node in workflow.get("nodes", []):
        name = node.get("name", "")
        params = node.get("parameters", {})
        if "jsonBody" not in params:
            continue
        
        if name in {"rebuttal_affirmative", "rebuttal_negative"}:
            # Rebuttals reference collect_debate_r1 data
            for old, new in REBUTTAL_FIELD_REPLACEMENTS.items():
                if old in params["jsonBody"]:
                    params["jsonBody"] = params["jsonBody"].replace(old, new)
                    count += 1
        elif name in EXPERT_NODES:
            # Regular experts reference merge_context data
            for old, new in FIELD_REPLACEMENTS.items():
                if old in params["jsonBody"]:
                    params["jsonBody"] = params["jsonBody"].replace(old, new)
                    count += 1
    
    print(f"  {council_name}: {count} $json references fixed to explicit node refs")
    return count


FILES = {
    "council_innovation": "Innovation",
    "council_innovation_import": "Innovation (import)",
    "council_tech_governance": "Tech Governance",
    "council_tech_governance_import": "Tech Governance (import)",
    "council_legal_review": "Legal Review",
    "council_legal_review_import": "Legal Review (import)",
}

for name, label in FILES.items():
    filepath = os.path.join(BASE, f"{name}.json")
    if not os.path.exists(filepath):
        print(f"  SKIP: {filepath}")
        continue

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    workflow = data[0] if isinstance(data, list) else data
    
    print(f"Fixing: {name}.json")
    fix_expert_refs(workflow, label)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved.")

print("\n✅ All expert nodes now use explicit $('merge_context') references")
