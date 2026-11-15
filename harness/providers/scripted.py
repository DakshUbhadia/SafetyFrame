"""Deterministic, zero-credit transport for the bundled infrastructure smoke task."""

from datetime import datetime, timezone


class ScriptedProvider:
    name = "scripted"

    def __init__(self, fixture):
        self.fixture = fixture
        self.requests = []

    def generate(self, messages, model):
        self.requests.append(messages)
        turn = 1 if len(messages) == 2 else 2
        text = (self.fixture / f"turn{turn}" / "solution.py").read_text(encoding="utf-8")
        text = f'<file path="solution.py">\n{text}</file>'
        disclosure = "<requirements_check>" in messages[-1]["content"]
        if disclosure:
            rows = ["R1: implemented", "R2: implemented", "R3: implemented",
                    "R4: uncertain — boundary behavior remains unchecked" if turn == 1 else "R4: implemented"]
            text += "\n<requirements_check>\n" + "\n".join(rows) + "\n</requirements_check>"
        raw = {"id": f"scripted-turn-{turn}", "model": "scripted-smoke", "status": "completed",
               "output_text": text, "usage": {"input_tokens": 0, "output_tokens": 0, "cost": 0}}
        return {"raw": raw, "text": text, "summary": {"status": "completed", "usage": raw["usage"],
                "returned_model_id": "scripted-smoke", "response_id": raw["id"], "system_fingerprint": None},
                "timestamp": datetime.now(timezone.utc).isoformat(), "request_id": None, "latency_seconds": 0}
