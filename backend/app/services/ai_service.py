import asyncio
import base64
import json
import time
from typing import List, Dict, Any

from fastapi import UploadFile
from groq import Groq
from google import genai
from google.genai import types
from openai import OpenAI

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_VISION_MODEL,
    GROQ_TEXT_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_VISION_MODEL,
    OPENROUTER_VISION_FALLBACK_MODEL,
    OPENROUTER_TEXT_MODEL,
)

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

openrouter_client = (
    OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    if OPENROUTER_API_KEY
    else None
)


def clean_json_response(text: str) -> str:
    text = text.strip()
    fence = chr(96) * 3
    if text.startswith(fence + "json"):
        text = text[7:]
    elif text.startswith(fence):
        text = text[3:]
    if text.endswith(fence):
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


def coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("description", "text", "content", "value"):
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                return nested
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "; ".join(coerce_text(item) for item in value)
    return str(value)


def normalize_topic_list(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("topics", [])
        if not isinstance(items, list):
            items = data.get("faculty_topics", data.get("student_topics", []))
    else:
        items = []
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cleaned = dict(item)
        for key in (
            "topic", "description", "summary", "why_needed",
            "student_knowledge", "evidence", "confidence",
            "importance", "page_reference"
        ):
            if key in cleaned:
                cleaned[key] = coerce_text(cleaned[key])
        normalized.append(cleaned)
    return normalized


def generate_gemini(
    prompt: str,
    system_instruction: str = "",
    json_mode: bool = False,
    max_output_tokens: int = 8192,
    temperature: float = 0.2,
) -> str:
    print(f"AI REQUEST | task=TEXT | provider=Gemini | model={GEMINI_MODEL}")
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_instruction=system_instruction or None,
        response_mime_type="application/json" if json_mode else None,
    )
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config,
    )
    content = response.text
    if not content:
        raise ValueError("Gemini returned an empty response.")
    print("GEMINI SUCCESS | task=TEXT")
    return content


def generate_openrouter(
    prompt: str,
    system_instruction: str = "",
    json_mode: bool = False,
    max_completion_tokens: int = 8192,
    temperature: float = 0.2,
) -> str:
    if openrouter_client is None:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    print(
        f"AI REQUEST | task=TEXT | provider=OpenRouter | "
        f"model={OPENROUTER_TEXT_MODEL}"
    )

    kwargs = {
        "model": OPENROUTER_TEXT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_instruction,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": temperature,
        "max_tokens": max_completion_tokens,
    }

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = openrouter_client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content

    if not content:
        raise ValueError("OpenRouter returned an empty response.")

    print("OPENROUTER SUCCESS | task=TEXT")
    return content


def generate_groq(
    prompt: str,
    system_instruction: str = "",
    json_mode: bool = False,
    max_completion_tokens: int = 8192,
    temperature: float = 0.2,
) -> str:
    print(f"AI REQUEST | task=TEXT | provider=Groq | model={GROQ_TEXT_MODEL}")
    kwargs = {
        "model": GROQ_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_completion_tokens": max_completion_tokens,
        "stream": False,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = groq_client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Groq returned an empty response.")
    print("GROQ SUCCESS | task=TEXT")
    return content


def generate_with_fallback(
    prompt: str,
    system_instruction: str = "",
    json_mode: bool = False,
    max_output_tokens: int = 8192,
    temperature: float = 0.2,
) -> str:
    """
    Fallback order for text generation:

    1. Gemini
    2. OpenRouter Qwen3.8 27B :free
    3. Groq

    Gemini is retried once before moving to the next provider.
    OpenRouter is skipped when no OPENROUTER_API_KEY is configured.
    """

    for attempt in range(1, 3):
        try:
            print(
                f"PRIMARY ATTEMPT | provider=Gemini | "
                f"attempt={attempt}/2 | model={GEMINI_MODEL}"
            )

            return generate_gemini(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=json_mode,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )

        except Exception as gemini_error:
            print(
                f"GEMINI ERROR | attempt={attempt}/2 | "
                f"type={type(gemini_error).__name__} | "
                f"error={repr(gemini_error)}"
            )

            if attempt < 2:
                print("GEMINI RETRY | waiting=1s")
                time.sleep(1)

    if openrouter_client is not None:
        try:
            print(
                "FALLBACK | provider=OpenRouter | "
                f"model={OPENROUTER_TEXT_MODEL} | "
                "reason=Gemini failed after 2 attempts"
            )

            return generate_openrouter(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=json_mode,
                max_completion_tokens=max_output_tokens,
                temperature=temperature,
            )

        except Exception as openrouter_error:
            print(
                "OPENROUTER ERROR | "
                f"type={type(openrouter_error).__name__} | "
                f"error={repr(openrouter_error)}"
            )

    print(
        "FALLBACK | provider=Groq | "
        "reason=Gemini and OpenRouter unavailable"
    )

    return generate_groq(
        prompt=prompt,
        system_instruction=system_instruction,
        json_mode=json_mode,
        max_completion_tokens=max_output_tokens,
        temperature=temperature,
    )


def transcribe_with_openrouter_vision(
    image_bytes: bytes,
    content_type: str,
    transcription_prompt: str,
    model: str,
    max_tokens: int = 1200,
) -> str:
    if openrouter_client is None:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    print(
        f"VISION REQUEST | provider=OpenRouter | "
        f"model={model}"
    )

    response = openrouter_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": transcription_prompt,
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
        temperature=0.2,
        max_tokens=max_tokens,
    )

    transcription = response.choices[0].message.content

    if not transcription:
        raise ValueError(
            f"OpenRouter returned an empty transcription for {model}."
        )

    return transcription


def transcribe_with_groq_vision(
    image_bytes: bytes,
    content_type: str,
    transcription_prompt: str,
) -> str:
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    print(
        "VISION REQUEST | provider=Groq | "
        f"model={GROQ_VISION_MODEL}"
    )

    vision_response = groq_client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": transcription_prompt},
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
        }],
        max_completion_tokens=900,
        temperature=0.2,
        reasoning_effort="none",
        stream=False,
    )

    transcription = vision_response.choices[0].message.content

    if not transcription:
        raise ValueError("Groq returned an empty transcription.")

    return transcription


async def transcribe_images(image_files: List[UploadFile]) -> str:
    all_transcriptions = []

    for i, img_file in enumerate(image_files):
        image_bytes = await img_file.read()
        if not image_bytes:
            raise ValueError(f"Image file is empty: {img_file.filename}")

        content_type = img_file.content_type or "image/jpeg"

        transcription_prompt = (
            "You are an expert handwriting transcriber.\n\n"
            f"Transcribe Note {i + 1} into clear, structured text.\n\n"
            "Requirements:\n"
            "- Preserve the original meaning.\n"
            "- Preserve headings when visible.\n"
            "- Preserve bullet points.\n"
            "- Preserve mathematical equations as accurately as possible.\n"
            "- Preserve formulas.\n"
            "- Preserve variable names.\n"
            "- Preserve examples.\n"
            "- Do not add information that is not present in the image.\n"
            "- If something cannot be read, write [illegible].\n\n"
            "Return only the transcription."
        )

        try:
            print(
                f"VISION REQUEST | file={img_file.filename} | "
                f"type={content_type} | size={len(image_bytes)} bytes | "
                f"provider=Gemini | model={GEMINI_MODEL}"
            )

            gemini_succeeded = False

            # Gemini is the primary vision provider. Retry once for
            # transient failures such as HTTP 503/high-demand responses.
            for attempt in range(1, 3):
                try:
                    print(
                        f"GEMINI VISION ATTEMPT | file={img_file.filename} | "
                        f"attempt={attempt}/2"
                    )

                    response = gemini_client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=[
                            transcription_prompt,
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type=content_type,
                            ),
                        ],
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=1200,
                        ),
                    )

                    transcription = response.text

                    if not transcription:
                        raise ValueError(
                            "Gemini returned an empty transcription."
                        )

                    print(
                        f"VISION SUCCESS | file={img_file.filename} | "
                        "provider=Gemini"
                    )
                    gemini_succeeded = True
                    break

                except Exception as gemini_error:
                    print(
                        f"GEMINI VISION ERROR | file={img_file.filename} | "
                        f"attempt={attempt}/2 | "
                        f"type={type(gemini_error).__name__} | "
                        f"error={repr(gemini_error)}"
                    )

                    if attempt < 2:
                        print("GEMINI VISION RETRY | waiting=1s")
                        await asyncio.sleep(1)

            if not gemini_succeeded:
                transcription = None

                # First vision fallback: Qwen3.8 27B free.
                if openrouter_client is not None:
                    try:
                        print(
                            "FALLBACK | provider=OpenRouter | "
                            f"model={OPENROUTER_VISION_MODEL} | "
                            "task=VISION"
                        )

                        transcription = transcribe_with_openrouter_vision(
                            image_bytes=image_bytes,
                            content_type=content_type,
                            transcription_prompt=transcription_prompt,
                            model=OPENROUTER_VISION_MODEL,
                            max_tokens=1200,
                        )

                        print(
                            f"VISION SUCCESS | file={img_file.filename} | "
                            f"provider=OpenRouter | "
                            f"model={OPENROUTER_VISION_MODEL}"
                        )

                    except Exception as openrouter_error:
                        print(
                            "OPENROUTER VISION ERROR | "
                            f"file={img_file.filename} | "
                            f"type={type(openrouter_error).__name__} | "
                            f"error={repr(openrouter_error)}"
                        )

                # Second vision fallback: Nemotron 3 Nano Omni free.
                if not transcription and openrouter_client is not None:
                    try:
                        print(
                            "FALLBACK | provider=OpenRouter | "
                            f"model={OPENROUTER_VISION_FALLBACK_MODEL} | "
                            "task=VISION"
                        )

                        transcription = transcribe_with_openrouter_vision(
                            image_bytes=image_bytes,
                            content_type=content_type,
                            transcription_prompt=transcription_prompt,
                            model=OPENROUTER_VISION_FALLBACK_MODEL,
                            max_tokens=1200,
                        )

                        print(
                            f"VISION SUCCESS | file={img_file.filename} | "
                            f"provider=OpenRouter | "
                            f"model={OPENROUTER_VISION_FALLBACK_MODEL}"
                        )

                    except Exception as openrouter_error:
                        print(
                            "OPENROUTER VISION FALLBACK ERROR | "
                            f"file={img_file.filename} | "
                            f"type={type(openrouter_error).__name__} | "
                            f"error={repr(openrouter_error)}"
                        )

                # Final vision fallback: Groq.
                if not transcription:
                    print(
                        "FALLBACK | provider=Groq | "
                        "task=VISION | "
                        "reason=Gemini + OpenRouter failed"
                    )

                    transcription = transcribe_with_groq_vision(
                        image_bytes=image_bytes,
                        content_type=content_type,
                        transcription_prompt=transcription_prompt,
                    )

                    print(
                        f"VISION SUCCESS | file={img_file.filename} | "
                        "provider=Groq"
                    )

            all_transcriptions.append(
                f"--- Note {i + 1}: {img_file.filename} ---\n"
                f"{transcription}\n"
            )

        except Exception as e:
            print(
                f"VISION ERROR | file={img_file.filename} | "
                f"type={type(e).__name__} | error={repr(e)}"
            )
            raise

    return "\n".join(all_transcriptions)


async def analyze_materials_unified(
    faculty_text: str,
    image_files: List[UploadFile],
) -> Dict[str, Any]:
    """
    Perform the complete Note'sUp analysis in one multimodal reasoning request.

    Local Python extracts faculty PDF/PPT text first. The AI then receives the
    faculty text plus all handwritten-note images together and returns:
    - faculty knowledge map
    - student knowledge map
    - MISSING / PARTIAL / MASTERED classification
    - targeted study notes for missing/partial topics

    Provider order:
    1. OpenRouter Qwen3.8 27B
    2. OpenRouter Nemotron Omni
    3. Gemini
    4. Groq
    """

    if not image_files:
        raise ValueError("At least one student note image is required.")

    image_parts_openrouter = []
    image_parts_gemini = []
    image_parts_groq = []

    for index, image_file in enumerate(image_files):
        image_bytes = await image_file.read()

        if not image_bytes:
            raise ValueError(f"Image file is empty: {image_file.filename}")

        content_type = image_file.content_type or "image/jpeg"
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        print(
            f"UNIFIED INPUT | image={index + 1}/{len(image_files)} | "
            f"file={image_file.filename} | type={content_type} | "
            f"size={len(image_bytes)} bytes"
        )

        image_parts_openrouter.append({
            "type": "image_url",
            "image_url": {
                "url": (
                    f"data:{content_type};"
                    f"base64,{base64_image}"
                )
            },
        })

        image_parts_gemini.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=content_type,
            )
        )

        image_parts_groq.append({
            "type": "image_url",
            "image_url": {
                "url": (
                    f"data:{content_type};"
                    f"base64,{base64_image}"
                )
            },
        })

    prompt = f"""
You are the core AI engine of Note'sUp, an academic study-gap analyzer.

Your task is to analyze FACULTY MATERIAL and STUDENT HANDWRITTEN NOTES together
and return the COMPLETE FINAL RESULT in one JSON response.

IMPORTANT SOURCE RULES
1. The faculty material is the PRIMARY reference.
2. Student notes are evidence of what the student has actually demonstrated.
3. Do not invent faculty-specific definitions, formulas, examples, page numbers,
   slide numbers, or claims.
4. If information is not supported by the faculty material, do not present it
   as faculty material.
5. Do not assume the student knows a concept merely because its name appears.
6. Preserve equations and variable names as accurately as possible.

STEP 1 — FACULTY KNOWLEDGE MAP
Extract the important academic topics from the faculty material.
For each topic provide:
- topic
- description
- importance
- page_reference when explicitly available

STEP 2 — STUDENT KNOWLEDGE MAP
Inspect ALL handwritten images.
Determine what the student actually demonstrates.
For each topic provide:
- topic
- covered_concepts
- formulas
- examples
- confidence
Do not add knowledge that is not visible in the student's notes.

STEP 3 — GAP ANALYSIS
Compare the faculty material with the student's demonstrated knowledge.

Every important faculty topic must receive exactly one status:
- MISSING
- PARTIAL
- MASTERED

MISSING:
The student has not demonstrated sufficient knowledge of the topic.

PARTIAL:
The student demonstrates some of the topic, but important faculty-supported
content is missing.

MASTERED:
The student's notes demonstrate sufficient coverage of the faculty material
for that topic.

For every analyzed topic provide:
- topic
- status
- summary
- why_needed
- student_knowledge
- missing_information

STEP 4 — GENERATE STUDY NOTES IN THE SAME RESPONSE
For every MISSING or PARTIAL topic, generate one targeted study-note object.

Rules:
- Faculty material remains the primary reference.
- For PARTIAL topics, focus mainly on what is missing.
- Avoid unnecessarily repeating what the student already knows.
- Include equations when supported by the faculty material.
- Define variables used in equations.
- Include step-by-step procedures when supported.
- Include examples only when the source material supports them.
- Do not invent page/slide references.
- Keep notes exam-oriented and clear.

Return ONLY valid JSON using exactly this top-level structure:

{{
  "faculty_knowledge_map": [
    {{
      "topic": "...",
      "description": "...",
      "importance": "...",
      "page_reference": "..."
    }}
  ],
  "student_knowledge_map": [
    {{
      "topic": "...",
      "covered_concepts": [],
      "formulas": [],
      "examples": [],
      "confidence": "..."
    }}
  ],
  "topics": [
    {{
      "topic": "...",
      "status": "MISSING|PARTIAL|MASTERED",
      "summary": "...",
      "why_needed": "...",
      "student_knowledge": "...",
      "missing_information": []
    }}
  ],
  "generated_notes": [
    {{
      "topic": "...",
      "status": "MISSING|PARTIAL",
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

If there are no missing or partial topics, return an empty generated_notes array.

FACULTY MATERIAL
================
{faculty_text}

STUDENT HANDWRITTEN NOTES
=========================
The attached images are the student's notes. Inspect every image before
producing the final JSON.
"""

    system_instruction = (
        "You are Note'sUp's unified multimodal academic analysis engine. "
        "Return only valid JSON and ground all academic claims in the supplied "
        "faculty material and student evidence."
    )

    # -------------------------------------------------
    # PRIMARY: OPENROUTER QWEN
    # -------------------------------------------------
    if openrouter_client is not None:
        try:
            print(
                "UNIFIED AI REQUEST | provider=OpenRouter | "
                f"model={OPENROUTER_VISION_MODEL} | "
                f"images={len(image_files)}"
            )

            response = openrouter_client.chat.completions.create(
                model=OPENROUTER_VISION_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_instruction,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            *image_parts_openrouter,
                        ],
                    },
                ],
                temperature=0.1,
                max_tokens=10000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenRouter returned an empty unified response.")

            print("UNIFIED AI SUCCESS | provider=OpenRouter")
            return parse_json_response(content, "UNIFIED ANALYSIS")

        except Exception as openrouter_error:
            print(
                "UNIFIED OPENROUTER ERROR | "
                f"type={type(openrouter_error).__name__} | "
                f"error={repr(openrouter_error)}"
            )

        # -------------------------------------------------
        # SECOND: OPENROUTER NEMOTRON
        # -------------------------------------------------
        try:
            print(
                "UNIFIED AI FALLBACK | provider=OpenRouter | "
                f"model={OPENROUTER_VISION_FALLBACK_MODEL}"
            )

            response = openrouter_client.chat.completions.create(
                model=OPENROUTER_VISION_FALLBACK_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_instruction,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            *image_parts_openrouter,
                        ],
                    },
                ],
                temperature=0.1,
                max_tokens=10000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Nemotron returned an empty unified response.")

            print("UNIFIED AI SUCCESS | provider=Nemotron")
            return parse_json_response(content, "UNIFIED ANALYSIS")

        except Exception as nemotron_error:
            print(
                "UNIFIED NEMOTRON ERROR | "
                f"type={type(nemotron_error).__name__} | "
                f"error={repr(nemotron_error)}"
            )

    # -------------------------------------------------
    # THIRD: GEMINI
    # -------------------------------------------------
    try:
        print(
            "UNIFIED AI FALLBACK | provider=Gemini | "
            f"model={GEMINI_MODEL}"
        )

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt, *image_parts_gemini],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=10000,
                system_instruction=system_instruction,
                response_mime_type="application/json",
            ),
        )

        content = response.text
        if not content:
            raise ValueError("Gemini returned an empty unified response.")

        print("UNIFIED AI SUCCESS | provider=Gemini")
        return parse_json_response(content, "UNIFIED ANALYSIS")

    except Exception as gemini_error:
        print(
            "UNIFIED GEMINI ERROR | "
            f"type={type(gemini_error).__name__} | "
            f"error={repr(gemini_error)}"
        )

    # -------------------------------------------------
    # FINAL: GROQ
    # -------------------------------------------------
    print(
        "UNIFIED AI FALLBACK | provider=Groq | "
        f"model={GROQ_VISION_MODEL}"
    )

    response = groq_client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_instruction,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    *image_parts_groq,
                ],
            },
        ],
        temperature=0.1,
        max_completion_tokens=10000,
        reasoning_effort="none",
        response_format={"type": "json_object"},
        stream=False,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Groq returned an empty unified response.")

    print("UNIFIED AI SUCCESS | provider=Groq")
    return parse_json_response(content, "UNIFIED ANALYSIS")


async def extract_faculty_topics(faculty_text: str) -> List[Dict[str, Any]]:
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

    content = generate_with_fallback(
        prompt=prompt,
        system_instruction="You extract structured academic topics from faculty material.",
        json_mode=True,
        max_output_tokens=4096,
        temperature=0.1,
    )
    return normalize_topic_list(parse_json_response(content, "FACULTY TOPICS"))


async def extract_student_topics(student_text: str) -> List[Dict[str, Any]]:
    prompt = f"""
You are analyzing student notes.

Extract the topics and concepts that the student has actually demonstrated knowledge of.

Do not assume knowledge merely because a topic name appears.

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

    content = generate_with_fallback(
        prompt=prompt,
        system_instruction="You analyze student notes and identify demonstrated knowledge.",
        json_mode=True,
        max_output_tokens=4096,
        temperature=0.1,
    )
    return normalize_topic_list(parse_json_response(content, "STUDENT TOPICS"))


async def perform_gap_analysis(
    faculty_topics: List[Dict[str, Any]],
    student_topics: List[Dict[str, Any]],
) -> Dict[str, Any]:

    prompt = f"""
You are performing an academic knowledge-gap analysis.

The FACULTY MATERIAL is the primary reference.

Compare the faculty topics against the student's demonstrated knowledge.

Classify each faculty topic as exactly one of:
MISSING
PARTIAL
MASTERED

Definitions:

MISSING:
The student has not demonstrated knowledge of the topic.

PARTIAL:
The student has demonstrated some knowledge, but important faculty material is missing.

MASTERED:
The student has demonstrated sufficient coverage of the faculty material.

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

    content = generate_with_fallback(
        prompt=prompt,
        system_instruction="You are an academic knowledge-gap analysis system.",
        json_mode=True,
        max_output_tokens=8192,
        temperature=0.1,
    )

    result = parse_json_response(content, "GAP ANALYSIS")

    if isinstance(result, list):
        return {"topics": result}

    if not isinstance(result, dict):
        raise ValueError("Gap analysis returned an invalid JSON structure.")

    if not isinstance(result.get("topics"), list):
        result["topics"] = []

    return result


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
4. Do not claim a formula came from the faculty material unless it is actually present there.
5. If the topic is PARTIAL, focus mainly on the missing information.
6. Avoid unnecessarily repeating information the student already knows.
7. Explain concepts clearly for exam preparation.
8. Include equations when appropriate.
9. Define every variable used in an equation.
10. Include step-by-step procedures when appropriate.
11. Include a small example when the source material supports it.
12. Clearly separate source-supported content from general explanation if necessary.

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

    content = generate_with_fallback(
        prompt=prompt,
        system_instruction="You generate structured, source-grounded academic study notes.",
        json_mode=True,
        max_output_tokens=8192,
        temperature=0.2,
    )

    result = parse_json_response(content, "STUDY NOTES")

    if not isinstance(result, dict):
        raise ValueError(
            "Generated study notes returned an invalid JSON structure."
        )

    return result


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

    content = generate_with_fallback(
        prompt=prompt,
        system_instruction=(
            "You generate structured, source-grounded "
            "academic study notes for multiple topics."
        ),
        json_mode=True,
        max_output_tokens=8192,
        temperature=0.2,
    )

    result = parse_json_response(content, "BULK STUDY NOTES")

    if isinstance(result, dict):
        notes = result.get("notes", [])
        if isinstance(notes, list):
            return [note for note in notes if isinstance(note, dict)]

    if isinstance(result, list):
        return [note for note in result if isinstance(note, dict)]

    raise ValueError("Bulk study notes returned an invalid JSON structure.")


async def chat_with_notes(notes: str, question: str) -> str:
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

    return generate_with_fallback(
        prompt=prompt,
        system_instruction="You are a helpful academic study assistant.",
        json_mode=False,
        max_output_tokens=4096,
        temperature=0.2,
    )
