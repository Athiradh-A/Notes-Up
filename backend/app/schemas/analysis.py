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


class NoteGenerationRequest(BaseModel):
    topic: str = Field(..., description="The topic for which study notes should be generated")
    status: str = Field(..., description="The current coverage status of the topic")
    why_needed: str = Field("", description="Explanation of why this topic needs to be studied")
    student_knowledge: str = Field("", description="What the student already knows about this topic")
    missing_information: List[str] = Field(
        default_factory=list,
        description="Specific information that is missing from the student's notes"
    )
    faculty_context: str = Field(
        "",
        description="Relevant context extracted from the faculty learning material"
    )


class ChatRequest(BaseModel):
    notes: str = Field(..., description="The study notes that the assistant should use")
    question: str = Field(..., description="The student's question")