import base64
import json
import re
from typing import List, Dict, Any

from fastapi import UploadFile
from groq import Groq

from app.core.config import (
    GROQ_API_KEY,
    GROQ_VISION_MODEL,
    GROQ_TEXT_MODEL,
)


# ---------------------------------------------------------
# GROQ CLIENT
# ---------------------------------------------------------

client = Groq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------
# HELPER: CLEAN JSON RESPONSE
# ---------------------------------------------------------

def clean_json_response(text: str) -> str:
    """
    Removes markdown code fences if the model returns JSON
    inside ```json ... ```.
    """
    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def parse_json_response(content: str, label: str) -> Any:
    cleaned = clean_json_response(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    for opener, closer in [("{", "}"), ("[", "]")]:
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                pass

    print(f"{label} JSON ERROR:", repr(cleaned[:4000]))
    raise ValueError(f"Failed to parse {label.lower()} as JSON.")


def normalize_topic_list(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("topics", [])
        if not isinstance(items, list):
            items = data.get("faculty_topics", data.get("student_topics", []))
    else:
        items = []
    return [item for item in items if isinstance(item, dict)]


# ---------------------------------------------------------
# TRANSCRIBE STUDENT HANDWRITTEN IMAGES
# ---------------------------------------------------------

async def transcribe_images(
    image_files: List[UploadFile],
) -> str:

    all_transcriptions = []

    for i, img_file in enumerate(image_files):

        try:
            # Read image
            image_bytes = await img_file.read()

            if not image_bytes:
                raise ValueError(
                    f"Image file is empty: {img_file.filename}"
                )

            # Convert to base64
            base64_image = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            # Determine MIME type
            content_type = img_file.content_type or "image/jpeg"

            print(
                f"VISION REQUEST | "
                f"file={img_file.filename} | "
                f"type={content_type} | "
                f"size={len(image_bytes)} bytes | "
                f"model={GROQ_VISION_MODEL}"
            )

            # -------------------------------------------------
            # GROQ VISION REQUEST
            # -------------------------------------------------

            vision_response = client.chat.completions.create(

                model=GROQ_VISION_MODEL,

                messages=[
                    {
                        "role": "user",

                        "content": [

                            {
                                "type": "text",

                                "text": (
                                    "You are an expert handwriting "
                                    "transcriber.\n\n"

                                    f"Transcribe Note {i + 1} "
                                    "into clear, structured text.\n\n"

                                    "Requirements:\n"
                                    "- Preserve the original meaning.\n"
                                    "- Preserve headings when visible.\n"
                                    "- Preserve bullet points.\n"
                                    "- Preserve mathematical equations "
                                    "as accurately as possible.\n"
                                    "- Preserve formulas.\n"
                                    "- Preserve variable names.\n"
                                    "- Preserve examples.\n"
                                    "- Do not add information that is "
                                    "not present in the image.\n"
                                    "- If something cannot be read, write "
                                    "[illegible].\n\n"

                                    "Return only the transcription."
                                ),
                            },

                            {
                                "type": "image_url",

                                "image_url": {
                                    "url": (
                                        f"data:{content_type};"
                                        f"base64,{base64_image}"
                                    )
                                },
                            },
                        ],
                    }
                ],

                # Keep the response bounded
                max_completion_tokens=800,

                temperature=0.2,

                # qwen3.8 supports this
                reasoning_effort="none",

                # Explicitly disable streaming
                stream=False,
            )

            # -------------------------------------------------
            # EXTRACT RESPONSE
            # -------------------------------------------------

            transcription = (
                vision_response
                .choices[0]
                .message
                .content
            )

            if not transcription:
                raise ValueError(
                    f"Groq returned an empty transcription "
                    f"for {img_file.filename}"
                )

            print(
                f"VISION SUCCESS | "
                f"file={img_file.filename}"
            )

            all_transcriptions.append(
                f"--- Note {i + 1}: {img_file.filename} ---\n"
                f"{transcription}\n"
            )

        except Exception as e:

            # IMPORTANT:
            # This gives us the exact error in Render logs.
            print(
                f"VISION ERROR | "
                f"file={img_file.filename} | "
                f"type={type(e).__name__} | "
                f"error={repr(e)}"
            )

            raise

    return "\n".join(all_transcriptions)


# ---------------------------------------------------------
# EXTRACT FACULTY TOPICS
# ---------------------------------------------------------

async def extract_faculty_topics(
    faculty_text: str,
) -> List[Dict[str, Any]]:

    prompt = f"""
You are analyzing faculty learning material.

The faculty material is the PRIMARY reference.

Extract the important academic topics from the material.

For each topic return:

- topic
- description
- important_concepts
- formulas
- exam_relevance

Do NOT invent information.

Only use information explicitly supported by the faculty material.

Return valid JSON.

Faculty material:

{faculty_text}
"""

    response = client.chat.completions.create(

        model=GROQ_TEXT_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured academic topics "
                    "from faculty material."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        temperature=0.1,

        max_completion_tokens=4096,

        response_format={"type": "json_object"},

        stream=False,
    )

    content = response.choices[0].message.content

    return normalize_topic_list(
        parse_json_response(content, "FACULTY TOPICS")
    )


# ---------------------------------------------------------
# EXTRACT STUDENT TOPICS
# ---------------------------------------------------------

async def extract_student_topics(
    student_text: str,
) -> List[Dict[str, Any]]:

    prompt = f"""
You are analyzing student notes.

Extract the topics and concepts that the student has
actually demonstrated knowledge of.

Do not assume knowledge merely because a topic name
appears.

For each topic return:

- topic
- covered_concepts
- formulas
- examples
- confidence

Use only the student's notes.

Return valid JSON.

Student notes:

{student_text}
"""

    response = client.chat.completions.create(

        model=GROQ_TEXT_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You analyze student notes and identify "
                    "demonstrated knowledge."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        temperature=0.1,

        max_completion_tokens=4096,

        response_format={"type": "json_object"},

        stream=False,
    )

    content = response.choices[0].message.content

    return normalize_topic_list(
        parse_json_response(content, "STUDENT TOPICS")
    )


# ---------------------------------------------------------
# GAP ANALYSIS
# ---------------------------------------------------------

async def perform_gap_analysis(
    faculty_topics: List[Dict[str, Any]],
    student_topics: List[Dict[str, Any]],
) -> Dict[str, Any]:

    prompt = f"""
You are performing an academic knowledge-gap analysis.

The FACULTY MATERIAL is the primary reference.

Compare the faculty topics against the student's
demonstrated knowledge.

Classify each faculty topic as exactly one of:

MISSING
PARTIAL
MASTERED

Definitions:

MISSING:
The student has not demonstrated knowledge of the topic.

PARTIAL:
The student has demonstrated some knowledge, but important
faculty material is missing.

MASTERED:
The student has demonstrated sufficient coverage of the
faculty material.

Do not assume knowledge.

For every topic provide:

- topic
- status
- summary: a short faculty-grounded definition or description of the topic, plus the key gap identified
- why_needed
- student_knowledge
- missing_information

The summary must be based on the faculty topic information. Do not invent a definition that is not supported by the faculty material.

Return valid JSON.

FACULTY TOPICS:

{json.dumps(faculty_topics, indent=2)}

STUDENT TOPICS:

{json.dumps(student_topics, indent=2)}
"""

    response = client.chat.completions.create(

        model=GROQ_TEXT_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic knowledge-gap "
                    "analysis system."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        temperature=0.1,

        max_completion_tokens=8192,

        stream=False,
    )

    content = response.choices[0].message.content

    result = parse_json_response(content, "GAP ANALYSIS")
    if isinstance(result, list):
        return {"topics": result}
    if not isinstance(result, dict):
        raise ValueError("Gap analysis returned an invalid JSON structure.")
    if not isinstance(result.get("topics"), list):
        result["topics"] = []
    return result


# ---------------------------------------------------------
# GENERATE STUDY NOTES
# ---------------------------------------------------------

async def generate_study_notes(
    topic: str,
    status: str,
    why_needed: str,
    student_knowledge: str,
    missing_information: List[str],
    faculty_context: str = "",
) -> Dict[str, Any]:

    prompt = f"""
Create targeted study notes for the following topic.

Topic:
{topic}

Status:
{status}

Why this topic is needed:
{why_needed}

What the student already knows:
{student_knowledge}

Missing information:
{json.dumps(missing_information, indent=2)}

Faculty material context:
{faculty_context}

IMPORTANT RULES:

1. The faculty material is the primary reference.
2. Do not invent faculty-specific information.
3. Do not invent slide numbers or page numbers.
4. Do not claim a formula came from the faculty material
   unless it is actually present there.
5. If the topic is PARTIAL, focus mainly on the missing
   information.
6. Avoid unnecessarily repeating information the student
   already knows.
7. Explain concepts clearly for exam preparation.
8. Include equations when appropriate.
9. Define every variable used in an equation.
10. Include step-by-step procedures when appropriate.
11. Include a small example when the source material supports it.
12. Clearly separate source-supported content from general
    explanation if necessary.

Return JSON in exactly this structure:

{{
    "topic": "...",
    "status": "...",
    "why_needed": "...",
    "student_knowledge": "...",
    "missing_information": [],
    "sections": [
        {{
            "heading": "...",
            "content": "...",
            "equations": []
        }}
    ],
    "exam_points": [],
    "sources": []
}}
"""

    response = client.chat.completions.create(

        model=GROQ_TEXT_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You generate structured, source-grounded "
                    "academic study notes."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        temperature=0.2,

        max_completion_tokens=8192,

        stream=False,
    )

    content = response.choices[0].message.content

    result = parse_json_response(content, "STUDY NOTES")
    if not isinstance(result, dict):
        raise ValueError("Generated study notes returned an invalid JSON structure.")
    return result


# ---------------------------------------------------------
# GENERATE BULK STUDY NOTES
# ---------------------------------------------------------

async def generate_bulk_study_notes(
    gaps: List[Dict[str, Any]],
    faculty_context: str = "",
) -> List[Dict[str, Any]]:

    prompt = f"""
Create targeted study notes for ALL of the academic gaps below.

The faculty material is the PRIMARY reference.

Faculty material context:
{faculty_context}

Gaps:
{json.dumps(gaps, indent=2)}

For every gap, create one study-note object.

IMPORTANT RULES:

1. Use the faculty material as the primary reference.
2. Do not invent faculty-specific information.
3. Do not invent slide numbers or page numbers.
4. If a topic is PARTIAL, focus mainly on the missing information.
5. Avoid unnecessarily repeating information the student already knows.
6. Explain concepts clearly for exam preparation.
7. Include equations when appropriate.
8. Define every variable used in an equation.
9. Include step-by-step procedures when appropriate.
10. Include a small example when the source material supports it.

Return ONLY valid JSON in exactly this structure:

{{
    "notes": [
        {{
            "topic": "...",
            "status": "...",
            "why_needed": "...",
            "student_knowledge": "...",
            "missing_information": [],
            "sections": [
                {{
                    "heading": "...",
                    "content": "...",
                    "equations": []
                }}
            ],
            "exam_points": [],
            "sources": []
        }}
    ]
}}
"""

    response = client.chat.completions.create(

        model=GROQ_TEXT_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You generate structured, source-grounded "
                    "academic study notes for multiple topics."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        temperature=0.2,

        max_completion_tokens=8192,

        response_format={"type": "json_object"},

        stream=False,
    )

    content = response.choices[0].message.content

    result = parse_json_response(content, "BULK STUDY NOTES")

    if isinstance(result, dict):
        notes = result.get("notes", [])
        if isinstance(notes, list):
            return [
                note for note in notes
                if isinstance(note, dict)
            ]

    if isinstance(result, list):
        return [
            note for note in result
            if isinstance(note, dict)
        ]

    raise ValueError(
        "Bulk study notes returned an invalid JSON structure."
    )


# ---------------------------------------------------------
# CHAT WITH GENERATED NOTES
# ---------------------------------------------------------

async def chat_with_notes(
    notes: str,
    question: str,
) -> str:

    prompt = f"""
You are a study assistant.

Answer the student's question using the provided study notes.

Study notes:

{notes}

Student question:

{question}

Rules:

- Stay grounded in the supplied notes.
- Explain clearly.
- If the answer is not present in the notes, say so.
- Do not invent faculty-specific information.
- Use equations when useful.
"""

    response = client.chat.completions.create(

        model=GROQ_TEXT_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful academic study assistant."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        temperature=0.2,

        max_completion_tokens=4096,

        stream=False,
    )

    return response.choices[0].message.content