from fastapi import APIRouter, Depends
from src.api.schemas.test import TestRequest, TestResponse
from src.api.schemas.auth import User
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/test", tags=["Test"])

@router.post("/", response_model=TestResponse)
def test(
    request: TestRequest,
    current_user: User = Depends(get_current_user),
):
    result = request.test_1 + request.test_2
    return TestResponse(test=result)