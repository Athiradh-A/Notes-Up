from pydantic import BaseModel, Field
from typing import List, Optional

class Topic(BaseModel):
    topic: str = Field(..., description="The name of the subject or concept")
    summary: str = Field(..., description="A concise explanation of the gap or content")
    status: str = Field("missing", description="covered, partially_covered, or missing")

class FacultyTopic(BaseModel):
    topic: str = Field(..., description="The core concept or learning objective")
    description: str = Field(..., description="Detailed explanation of what is expected to be known")
    importance: str = Field(..., description="High/Medium/Low importance to the course")
    page_reference: Optional[str] = Field(None, description="The page or slide number where this is discussed")

class StudentTopic(BaseModel):
    topic: str = Field(..., description="The concept identified in student notes")
    evidence: str = Field(..., description="Quote or summary from the notes proving this was covered")
    completeness: str = Field(..., description="Complete or Incomplete based on the evidence")

class AnalysisResponse(BaseModel):
    missing_topics: List[Topic] = Field(default_factory=list)
    covered_topics: List[str] = Field(default_factory=list)
    partially_covered_topics: List[Topic] = Field(default_factory=list)
    faculty_knowledge_map: List[FacultyTopic] = Field(default_factory=list)
    student_knowledge_map: List[StudentTopic] = Field(default_factory=list)

class ChatRequest(BaseModel):
    message: str
    context: dict
    history: list
