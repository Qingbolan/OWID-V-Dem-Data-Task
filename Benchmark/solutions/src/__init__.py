from .ClaudeSQLAgent import ClaudeSQLAgentWorkflow
from .SQLAgent import SQLAgentWorkflow

SOLUTIONS = {"SQLAgent": SQLAgentWorkflow, "ClaudeSQLAgent": ClaudeSQLAgentWorkflow}

__all__ = ["SOLUTIONS", "SQLAgentWorkflow", "ClaudeSQLAgentWorkflow"]
