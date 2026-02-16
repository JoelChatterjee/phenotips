"""Local LLM orchestration for pedigree extraction and follow-up prompts."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.pedigree_builder import default_pedigree, load_json_payload

PROMPT_TEMPLATE = """You are an empathetic genetic counselor building a family pedigree. Be kind, ask one question at a time if needed, handle sensitive topics gently (e.g., \"I'm sorry to hear that—tell me more if comfortable\").
History: {history}
User: {user_input}
Extract/update as strict JSON (no extra text): {{\"people\": [{{\"id\": int (sequential), \"name\": str, \"gender\": \"M/F/O\", \"dob\": \"YYYY-MM-DD or approx\", \"conditions\": [str]}}],
\"relationships\": [{{\"from\": id, \"to\": id, \"type\": \"parent/child/sibling/spouse/adopted\"}}]}}
If incomplete, respond with JSON + follow-up question after. If done, just JSON.
Handle corrections: If user says \"Fix: Bob is uncle\", update graph.
"""


@dataclass
class LLMResponse:
    pedigree: Dict[str, Any]
    follow_up_question: Optional[str] = None
    raw_text: str = ""


class PedigreeChatEngine:
    """Wrapper around local Ollama model with deterministic parsing fallback."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "No prior history"
        return "\n".join(f"{m['role']}: {m['content']}" for m in history)

    def build_prompt(self, history: List[Dict[str, str]], user_input: str) -> str:
        return PROMPT_TEMPLATE.format(history=self._format_history(history), user_input=user_input)

    def _call_ollama_langchain(self, prompt: str) -> str:
        """Try LangChain + Ollama, fall back to local deterministic parser when unavailable."""
        try:
            from langchain_core.prompts import PromptTemplate
            from langchain_ollama import OllamaLLM

            llm = OllamaLLM(model=self.model_name, temperature=0.1)
            prompt_chain = PromptTemplate.from_template("{prompt}")
            chain = prompt_chain | llm
            response = chain.invoke({"prompt": prompt})
            return response if isinstance(response, str) else str(response)
        except Exception:
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """Offline deterministic parsing for development/testing without LLM runtime."""
        user_line = prompt.split("User:")[-1].strip().lower()
        base = default_pedigree()

        if "mother" in user_line:
            base["people"].append({"id": 1, "name": "Mother", "gender": "F", "dob": "approx", "conditions": []})
        if "father" in user_line:
            base["people"].append({"id": len(base["people"]) + 1, "name": "Father", "gender": "M", "dob": "approx", "conditions": []})
        if "me" in user_line or "i am" in user_line:
            base["people"].append({"id": len(base["people"]) + 1, "name": "Proband", "gender": "O", "dob": "approx", "conditions": []})

        if len(base["people"]) >= 2:
            base["relationships"].append({"from": 1, "to": 2, "type": "spouse"})

        follow_up = "Who else in your family should be included?"
        return f"{json.dumps(base)}\n{follow_up}"

    def _split_json_and_question(self, text: str) -> LLMResponse:
        lines = text.strip().splitlines()
        json_candidate = ""
        follow_up = None

        if lines:
            json_candidate = lines[0].strip()
            if len(lines) > 1:
                follow_up = " ".join(l.strip() for l in lines[1:] if l.strip())

        if not json_candidate.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_candidate = text[start : end + 1]
                remaining = (text[:start] + text[end + 1 :]).strip()
                if remaining:
                    follow_up = remaining

        pedigree = load_json_payload(json_candidate)
        return LLMResponse(pedigree=pedigree, follow_up_question=follow_up, raw_text=text)

    def process_user_message(self, history: List[Dict[str, str]], user_input: str) -> LLMResponse:
        prompt = self.build_prompt(history, user_input)
        output = self._call_ollama_langchain(prompt)
        return self._split_json_and_question(output)
