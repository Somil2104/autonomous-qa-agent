from pydantic import BaseModel
from typing import List

class TestCase(BaseModel):
    id: int
    title: str
    description: str

class GenerateTestCasesRequest(BaseModel):
    documentation_filenames: List[str]
    html_filenames: List[str]

class GenerateTestCasesResponse(BaseModel):
    test_cases: List[TestCase]
    status: str
