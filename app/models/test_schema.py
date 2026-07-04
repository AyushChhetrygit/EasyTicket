import sys
from pathlib import Path

from pydantic import ValidationError

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.models.ai_schemas import TicketAnalysisResult


ai_response = {
    "category": "billing",
    "subcategory": "subscription_activation",
    "classification_confidence": 0.92,
    "priority": "P1",
    "assigned_team": "Billing Support",
    "reason": "Payment was deducted but the subscription remains inactive.",
}


try:
    result = TicketAnalysisResult.model_validate(ai_response)

    print("Validation successful")
    print(result)
    print(result.model_dump())
    print(result.model_dump_json(indent=2))

except ValidationError as error:
    print("Invalid AI response")
    print(error)
