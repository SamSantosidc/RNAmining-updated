"""RNAmining's data preparation, training, inference, and evaluation interfaces."""

from .evaluation import (
    calculate_metrics,
    evaluate_model,
    export_results,
    summarize_metrics,
)

__all__ = (
    "calculate_metrics",
    "evaluate_model",
    "export_results",
    "summarize_metrics",
)

__version__ = "1.0.4"
