from typing import Dict
from pydantic import BaseModel, Field


class Message(BaseModel):
    type: str = Field(default="success")
    code: int = Field(default=0)
    text: str = Field(default="")


class ForecastResult(BaseModel):
    watts: Dict[str, float]
    watt_hours: Dict[str, float]
    watt_hours_day: Dict[str, float]


class ForecastResponse(BaseModel):
    result: ForecastResult | dict
    message: Message

