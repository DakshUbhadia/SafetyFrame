"""Cross-run, fail-closed reservations for generation calls; not an account balance API."""

from contextlib import contextmanager
from pathlib import Path
from .artifacts import digest, read_json, write_json
from .preflight import nonnegative_number


@contextmanager
def exclusive_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = path.open("x", encoding="utf-8")
    except FileExistsError:
        raise RuntimeError(f"Lock already exists: {path}. Reconcile interrupted work before removing it.") from None
    try:
        handle.write("Exclusive run/budget lock; remove only after verifying no active process.\n")
        handle.close()
        yield
    finally:
        path.unlink()


class BudgetLedger:
    def __init__(self, path, config):
        self.path, self.config = Path(path), config

    def reserve(self, call_id, messages, model):
        pricing = model.get("pricing", {})
        rates = [pricing.get("input_credits_per_million"), pricing.get("output_credits_per_million")]
        if not all(nonnegative_number(rate) for rate in rates):
            raise ValueError("Published model pricing is required before generation")
        # UTF-8 byte count plus protocol overhead overestimates ordinary text tokenization.
        # This is a liability estimate, not a provider-enforced hard credit cap.
        byte_count = sum(len(item["content"].encode()) for item in messages) + 4096
        bound = (byte_count * rates[0] + model["generation"]["max_output_tokens"] * rates[1]) / 1_000_000
        with exclusive_lock(self.path.with_suffix(".lock")):
            ledger = read_json(self.path) if self.path.exists() else {"calls": {}}
            if call_id in ledger["calls"]:
                if ledger["calls"][call_id]["request_hash"] != digest([messages, model["model_id"], model["generation"]]):
                    raise RuntimeError("Budget call identity changed")
                return
            spent = sum(item["liability"] for item in ledger["calls"].values())
            budget = self.config["budget"]
            if spent + bound > budget["available"] - budget["protected_reserve"]:
                raise RuntimeError("Budget reserve would be crossed; no generation call sent")
            ledger["calls"][call_id] = {"liability": bound, "status": "reserved_or_unknown",
                                        "request_hash": digest([messages, model["model_id"], model["generation"]]),
                                        "model_id": model["model_id"]}
            write_json(self.path, ledger)

    def settle(self, call_id, result, model):
        usage = result.get("summary", {}).get("usage") or {}
        if not all(nonnegative_number(usage.get(name)) for name in ("input_tokens", "output_tokens")):
            return  # Retain the full reservation when accounting is unavailable.
        rates = model["pricing"]
        estimated = (usage["input_tokens"] * rates["input_credits_per_million"]
                     + usage["output_tokens"] * rates["output_credits_per_million"]) / 1_000_000
        reported = usage.get("cost")
        with exclusive_lock(self.path.with_suffix(".lock")):
            ledger = read_json(self.path)
            ledger["calls"][call_id].update(liability=max(estimated, reported if nonnegative_number(reported) else estimated),
                                             status="usage_recorded", usage=usage)
            write_json(self.path, ledger)
