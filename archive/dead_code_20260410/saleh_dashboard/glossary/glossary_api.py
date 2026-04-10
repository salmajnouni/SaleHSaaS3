"""
Glossary API Module for SaleH SaaS Dashboard
يُضاف هذا الملف كـ router لخدمة الـ Dashboard
"""
import json
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/glossary", tags=["glossary"])

GLOSSARY_PATH = Path("/app/glossary/glossary.json")


def load_glossary() -> dict:
    """Load the glossary from the JSON file."""
    if not GLOSSARY_PATH.exists():
        return {"categories": {}}
    with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_glossary(data: dict):
    """Save the glossary to the JSON file."""
    GLOSSARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GLOSSARY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class NewTerm(BaseModel):
    category: str
    term_ar: str
    term_en: str
    definition_ar: str
    definition_en: str
    source: Optional[str] = "مُضاف يدوياً"


@router.get("/")
async def get_all_terms():
    """Get all glossary terms organized by category."""
    glossary = load_glossary()
    return glossary


@router.get("/search")
async def search_terms(q: str):
    """Search for a term in the glossary (Arabic or English)."""
    glossary = load_glossary()
    results = []
    q_lower = q.lower()
    for cat_key, category in glossary.get("categories", {}).items():
        for term in category.get("terms", []):
            if (q_lower in term.get("term_ar", "").lower() or
                    q_lower in term.get("term_en", "").lower() or
                    q_lower in term.get("definition_ar", "").lower() or
                    q_lower in term.get("definition_en", "").lower()):
                results.append({
                    "category_ar": category.get("name_ar"),
                    "category_en": category.get("name_en"),
                    **term
                })
    return {"query": q, "count": len(results), "results": results}


@router.get("/categories")
async def get_categories():
    """Get all categories with their names."""
    glossary = load_glossary()
    categories = []
    for key, cat in glossary.get("categories", {}).items():
        categories.append({
            "key": key,
            "name_ar": cat.get("name_ar"),
            "name_en": cat.get("name_en"),
            "term_count": len(cat.get("terms", []))
        })
    return categories


@router.post("/add")
async def add_term(new_term: NewTerm):
    """Add a new term to the glossary."""
    glossary = load_glossary()
    categories = glossary.get("categories", {})

    if new_term.category not in categories:
        raise HTTPException(status_code=404, detail=f"Category '{new_term.category}' not found.")

    # Generate a new ID
    existing_terms = categories[new_term.category].get("terms", [])
    prefix = new_term.category[:2]
    new_id = f"{prefix}_{str(len(existing_terms) + 1).zfill(3)}"

    term_obj = {
        "id": new_id,
        "term_ar": new_term.term_ar,
        "term_en": new_term.term_en,
        "definition_ar": new_term.definition_ar,
        "definition_en": new_term.definition_en,
        "related_terms": [],
        "source": new_term.source
    }

    categories[new_term.category]["terms"].append(term_obj)
    glossary["metadata"]["total_terms"] = sum(
        len(cat.get("terms", [])) for cat in categories.values()
    )
    save_glossary(glossary)

    return {"message": "تم إضافة المصطلح بنجاح", "term": term_obj}
