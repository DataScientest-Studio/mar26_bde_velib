from pydantic import BaseModel

class TestRequest(BaseModel):
    test_1: float
    test_2: float

class TestResponse(BaseModel):
    test: float