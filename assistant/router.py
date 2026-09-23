"""Model A, part 2: transparent routing-scoring function.

    score(model, intent) = w_a * accuracy[model][intent]
                         + w_c * (1 - cost[model])
                         + w_l * (1 - latency[model])

The model with the highest score is selected.  Every term is returned so the
UI and the report can show exactly why a model won.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import config


@dataclass
class RouteDecision:
    intent: str
    chosen: str
    scores: dict[str, float]
    breakdown: dict[str, dict[str, float]] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)


def score_model(name: str, intent: str, weights=None, pool=None) -> tuple[float, dict]:
    weights = weights or config.DEFAULT_WEIGHTS
    pool = pool or config.MODEL_POOL
    m = pool[name]
    acc = m["accuracy"][intent]
    cost_eff = 1.0 - m["cost"]
    lat_eff = 1.0 - m["latency"]
    parts = {
        "accuracy": weights["accuracy"] * acc,
        "cost_efficiency": weights["cost"] * cost_eff,
        "latency_efficiency": weights["latency"] * lat_eff,
    }
    return round(sum(parts.values()), 4), {k: round(v, 4) for k, v in parts.items()}


def route(intent: str, weights=None, pool=None) -> RouteDecision:
    weights = weights or config.DEFAULT_WEIGHTS
    pool = pool or config.MODEL_POOL
    scores, breakdown = {}, {}
    for name in pool:
        s, parts = score_model(name, intent, weights, pool)
        scores[name] = s
        breakdown[name] = parts
    chosen = max(scores, key=scores.get)
    return RouteDecision(intent=intent, chosen=chosen, scores=scores, breakdown=breakdown, weights=dict(weights))


def routing_gain(intents: list[str], weights=None, pool=None) -> dict:
    """How much dynamic routing beats always using one fixed model.

    For each query the routed model's score is compared with the score each
    fixed model would have earned on that same query.  Returns the average
    gap per fixed model and the mean across all fixed models.
    """
    pool = pool or config.MODEL_POOL
    gaps = {name: [] for name in pool}
    for it in intents:
        d = route(it, weights, pool)
        for name in pool:
            gaps[name].append(d.scores[d.chosen] - d.scores[name])
    per_model = {n: round(sum(g) / len(g), 4) for n, g in gaps.items()}
    return {"per_fixed_model": per_model, "mean_gap": round(sum(per_model.values()) / len(per_model), 4)}
