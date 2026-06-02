"""Agent 可注册动作。"""

from agent.actions.base import Action
from agent.actions.parse_document import ParseDocumentAction
from agent.actions.generate_cases import GenerateCasesAction
from agent.actions.validate_cases import ValidateCasesAction
from agent.actions.save_cases import SaveCasesAction

__all__ = [
    "Action",
    "ParseDocumentAction",
    "GenerateCasesAction",
    "ValidateCasesAction",
    "SaveCasesAction",
]
