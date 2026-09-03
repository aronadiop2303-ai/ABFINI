"""Model taxonomy used by the ABFINI V0.1 router."""
from dataclasses import dataclass
from enum import Enum


class ModelType(str, Enum):
    PROPRIETARY = "proprietary"
    OPEN_SOURCE = "open_source"
    OPEN_WEIGHT = "open_weight"
    HYBRID = "hybrid"
    LOCAL = "local"
    GATEWAY = "gateway"


@dataclass(frozen=True)
class ModelDescriptor:
    model: str
    provider: str
    model_type: ModelType


# The taxonomy is deliberately metadata-only: adding a provider/model must not
# require changing the router algorithm.
def describe_provider(provider: object) -> ModelDescriptor:
    model = str(getattr(provider, "model", provider.__class__.__name__))
    name = provider.__class__.__name__.lower()
    declared = getattr(provider, "model_type", None)
    if declared:
        model_type = ModelType(str(declared))
    elif "openrouter" in name:
        model_type = ModelType.GATEWAY
    elif "opencompatible" in name:
        model_type = ModelType.LOCAL
    else:
        model_type = ModelType.PROPRIETARY
    return ModelDescriptor(model=model, provider=provider.__class__.__name__, model_type=model_type)
