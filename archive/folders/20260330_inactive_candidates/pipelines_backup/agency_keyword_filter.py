"""
title: Agency Keyword Prompt Filter
author: Saleh Custom
version: 2.2 - Clean Valves Fix
license: MIT
description: Adds agency-agents system prompt when keyword like 'agency frontend' is detected
requirements: none
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel

class Valves(BaseModel):
    """Empty Valves - no extra attributes"""
    pass

class Pipeline:
    class Valves(BaseModel):
        """Empty Valves - no extra attributes"""
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

        content = last_message.get("content", "").strip().lower()

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
                        msg["content"] = prompt + "\n\n" + msg["content"]
                        break

            last_message["content"] = content.replace(matched_key, "").strip()
            body["messages"] = messages

        return body