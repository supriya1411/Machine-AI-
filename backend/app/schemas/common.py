from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    meta: Optional[Any] = Field(default_factory=dict)

class ApiErrorResponse(BaseModel):
    success: bool = False
    data: Optional[Any] = None
    message: str
    error_code: str = "INTERNAL_ERROR"
