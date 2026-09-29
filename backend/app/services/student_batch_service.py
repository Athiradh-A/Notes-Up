import asyncio
import base64
from typing import List, Dict, Any

from fastapi import UploadFile
from google.genai import types

from app.services.ai_service import (
    gemini_client,
    openrouter_client,
    groq_client,
    GEMINI_MODEL,
    OPENROUTER_VISION_MODEL,
    OPENROUTER_VISION_FALLBACK_MODEL,
    GROQ_VISION_MODEL,
    parse_json_response,
    normalize_topic_list,
)


async def analyze_student_image_batch(
    image_files: List[UploadFile],
    batch_number: int,
) -> List[Dict[str, Any]]:
    """Extract demonstrated student knowledge from a small image batch."""
    gemini_parts = []
    openrouter_parts = []
    groq_parts = []

    for image in image_files:
        data = await image.read()
        if not data:
            raise ValueError(f"Image file is empty: {image.filename}")

        mime = image.content_type or "image/png"
        gemini_parts.append(types.Part.from_bytes(data=data, mime_type=mime))

        encoded = base64.b64encode(data).decode("utf-8")
        image_url = f"data:{mime};base64,{encoded}"
        openrouter_parts.append({
            "type": "image_url",
            "image_url": {"url": image_url},
        })
        groq_parts.append({
            "type": "image_url",
            "image_url": {"url": image_url},
        })

    prompt = f"""
Analyze handwritten student notes from batch {batch_number}.

Identify ONLY knowledge actually demonstrated in the attached pages.
Do not infer knowledge merely because a topic name appears.

Return ONLY valid JSON:
{{
  "student_knowledge_map": [
    {{
      "topic": "...",
      "covered_concepts": [],
      "formulas": [],
      "examples": [],
      "confidence": "high|medium|low",
      "evidence": "..."
    }}
  ]
}}

Keep the response concise. Do not perform gap analysis or generate study notes.
Inspect every attached page.
"""

    system = (
        "You are Note'sUp's handwritten-note extraction engine. "
        "Extract only demonstrated student knowledge and return valid JSON."
    )

    try:
        print(
            f"STUDENT BATCH | batch={batch_number} | "
            f"provider=Gemini | model={GEMINI_MODEL} | images={len(image_files)}"
        )
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt, *gemini_parts],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2500,
                system_instruction=system,
                response_mime_type="application/json",
            ),
        )
        if response.text:
            result = parse_json_response(
                response.text, f"STUDENT BATCH {batch_number}"
            )
            return normalize_topic_list(
                result.get("student_knowledge_map", [])
                if isinstance(result, dict) else result
            )
    except Exception as error:
        print(
            f"STUDENT BATCH GEMINI ERROR | batch={batch_number} | "
            f"{type(error).__name__}: {error}"
        )

    if openrouter_client is not None:
        for model in (
            OPENROUTER_VISION_MODEL,
            OPENROUTER_VISION_FALLBACK_MODEL,
        ):
            try:
                response = openrouter_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                *openrouter_parts,
                            ],
                        },
                    ],
                    temperature=0.1,
                    max_tokens=2500,
                    response_format={"type": "json_object"},
                )
                if response.choices[0].message.content:
                    result = parse_json_response(
                        response.choices[0].message.content,
                        f"STUDENT BATCH {batch_number}",
                    )
                    return normalize_topic_list(
                        result.get("student_knowledge_map", [])
                        if isinstance(result, dict) else result
                    )
            except Exception as error:
                print(
                    f"STUDENT BATCH OPENROUTER ERROR | batch={batch_number} | "
                    f"model={model} | {type(error).__name__}: {error}"
                )

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *groq_parts,
                    ],
                },
            ],
            temperature=0.1,
            max_completion_tokens=900,
            reasoning_effort="none",
            response_format={"type": "json_object"},
            stream=False,
        )
        if response.choices[0].message.content:
            result = parse_json_response(
                response.choices[0].message.content,
                f"STUDENT BATCH {batch_number}",
            )
            return normalize_topic_list(
                result.get("student_knowledge_map", [])
                if isinstance(result, dict) else result
            )
    except Exception as error:
        print(
            f"STUDENT BATCH GROQ ERROR | batch={batch_number} | "
            f"{type(error).__name__}: {error}"
        )

    raise RuntimeError(
        f"All vision providers failed for student batch {batch_number}."
    )


async def analyze_student_batches(
    image_files: List[UploadFile],
    batch_size: int = 6,
    max_concurrency: int = 3,
) -> List[Dict[str, Any]]:
    """Analyze small groups of pages, with limited parallelism."""
    batches = [
        image_files[i:i + batch_size]
        for i in range(0, len(image_files), batch_size)
    ]

    print(
        f"STUDENT BATCHING | pages={len(image_files)} | "
        f"batch_size={batch_size} | batches={len(batches)} | "
        f"concurrency={max_concurrency}"
    )

    all_topics = []

    for start in range(0, len(batches), max_concurrency):
        window = batches[start:start + max_concurrency]
        numbers = list(range(start + 1, start + len(window) + 1))

        results = await asyncio.gather(
            *[
                analyze_student_image_batch(batch, number)
                for batch, number in zip(window, numbers)
            ],
            return_exceptions=True,
        )

        for number, result in zip(numbers, results):
            if isinstance(result, Exception):
                raise RuntimeError(f"Student batch {number} failed: {result}")
            all_topics.extend(result)

    return all_topics
