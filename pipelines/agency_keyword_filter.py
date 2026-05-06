"""
title: Agency Keyword Prompt Filter
author: Saleh Custom
version: 2.3 - Block Content Fix
license: MIT
description: Adds agency-agents system prompt when keyword like 'agency frontend' is detected
requirements: none
"""

import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue

            if not isinstance(block, dict):
                continue

            block_type = str(block.get("type", "")).lower()
            if block_type in {"text", "input_text"}:
                value = block.get("text") or block.get("input_text")
                if isinstance(value, str) and value.strip():
                    parts.append(value)

        return "\n".join(parts).strip()

    if isinstance(content, dict):
        for key in ("text", "content", "value"):
            value = content.get(key)
            if isinstance(value, str):
                return value

    return ""

class Valves(BaseModel):
    """Empty Valves - no extra attributes"""
    pass

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        pass

    def __init__(self):
        self.type = "filter"
        self.valves = self.Valves()

    async def inlet(
        self,
        body: Dict[str, Any],
        __user__: Optional[Dict] = None
    ) -> Dict[str, Any]:
        messages = body.get("messages", [])
        if not messages:
            return body

        last_message = messages[-1]
        if last_message.get("role") != "user":
            return body

        original_content = _normalize_content(last_message.get("content", "")).strip()
        content = original_content.lower()

        agency_prompts = {
            "agency frontend": """You are a Senior Frontend Developer agent from agency-agents.
Specialize in React, Tailwind CSS, Next.js, TypeScript, responsive design, accessibility.
Always write clean, modular code. Use latest best practices. Explain your decisions.
Prioritize mobile-first and dark mode if requested.""",

            "agency pm": """You are Senior Project Manager agent from agency-agents.
Role: Agile/Scrum expert with 15+ years.
Guidelines: Break down tasks, create roadmaps, prioritize backlog, manage risks, dependencies.
Format responses with bullet points, tables, or Jira-style tickets."""
        }

        matched_key = next((k for k in agency_prompts if k in content), None)
        if matched_key:
            prompt = agency_prompts[matched_key]

            has_system = any(m.get("role") == "system" for m in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": prompt})
            else:
                for msg in messages:
                    if msg.get("role") == "system":
                        existing = _normalize_content(msg.get("content", ""))
                        msg["content"] = prompt + "\n\n" + existing if existing else prompt
                        break

            last_message["content"] = re.sub(
                re.escape(matched_key),
                "",
                original_content,
                count=1,
                flags=re.IGNORECASE,
            ).strip()
            body["messages"] = messages

        return body