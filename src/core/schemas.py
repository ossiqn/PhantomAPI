from pydantic import BaseModel, HttpUrl, field_validator
from typing   import Optional, Any

class ExtractionRequest(BaseModel):
    url:               HttpUrl
    prompt:            str
    wait_for_selector: Optional[str]     = None
    javascript:        Optional[str]     = None
    webhook_url:       Optional[HttpUrl] = None

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Prompt field cannot be empty.")
        return stripped

    @field_validator("javascript")
    @classmethod
    def javascript_length_guard(cls, value: Optional[str]) -> Optional[str]:
        if value and len(value) > 2000:
            raise ValueError("Custom JavaScript cannot exceed 2000 characters.")
        return value

class ExtractionResponse(BaseModel):
    success:        bool
    url:            str
    extracted_data: dict[str, Any]
    tokens_used:    Optional[int]   = None
    proxy_used:     Optional[str]   = None
    elapsed_ms:     Optional[float] = None

class ExtractionQueuedResponse(BaseModel):
    success: bool
    message: str
    task_id: str

class HealthResponse(BaseModel):
    status:      str
    service:     str
    version:     str
    environment: str
    proxy_count: int

class ErrorResponse(BaseModel):
    success: bool          = False
    error:   str
    detail:  Optional[str] = None
    code:    Optional[int] = None
