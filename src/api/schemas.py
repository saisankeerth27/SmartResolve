from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    gemini_configured: bool
