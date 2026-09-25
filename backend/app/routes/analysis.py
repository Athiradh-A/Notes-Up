import asyncio
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Body

from app.services.doc_service import extract_text

from app.services.ai_service import (
    transcribe_images,
    extract_faculty_topics,
    perform_gap_analysis,
    generate_topic_notes,
    get_chat_response,
)

router = APIRouter()


@router.post("/analyze")
async def analyze_notes(
    faculty_file: UploadFile = File(...),
    student_images: List[UploadFile] = File(...),
):
    try:
        print(
            f"ANALYZE START | "
            f"faculty={faculty_file.filename} | "
            f"student_images={len(student_images)}"
        )

        faculty_data = await extract_text(faculty_file)

        print(
            f"FACULTY EXTRACTION COMPLETE | "
            f"pages={len(faculty_data)}"
        )

        if not faculty_data:
            raise HTTPException(
                status_code=400,
                detail="No readable content found in faculty material."
            )

        transcribed_notes = await transcribe_images(
            student_images
        )

        print(
            f"STUDENT NOTES TRANSCRIBED | "
            f"characters={len(transcribed_notes)}"
        )

        try:
            faculty_map = await extract_faculty_topics(
                faculty_data
            )

            print(
                f"FACULTY KNOWLEDGE MAP | "
                f"topics={len(faculty_map)}"
            )

        except Exception as e:
            print(
                f"FACULTY KNOWLEDGE MAP ERROR | "
                f"type={type(e).__name__} | "
                f"error={repr(e)}"
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to extract the faculty knowledge map: "
                    f"{str(e)}"
                )
            )

        if not faculty_map:
            raise HTTPException(
                status_code=500,
                detail="Faculty knowledge map is empty."
            )

        result = await perform_gap_analysis(
            faculty_data,
            transcribed_notes,
            faculty_map,
        )

        response_dict = result.dict()

        response_dict["_faculty_raw"] = faculty_data

        response_dict.setdefault(
            "faculty_knowledge_map",
            faculty_map
        )

        response_dict.setdefault(
            "missing_topics",
            []
        )

        response_dict.setdefault(
            "partially_covered_topics",
            []
        )

        response_dict.setdefault(
            "covered_topics",
            []
        )

        print(
            "GAP ANALYSIS COMPLETE | "
            f"faculty_topics={len(response_dict.get('faculty_knowledge_map', []))} | "
            f"missing={len(response_dict.get('missing_topics', []))} | "
            f"partial={len(response_dict.get('partially_covered_topics', []))} | "
            f"covered={len(response_dict.get('covered_topics', []))}"
        )

        return response_dict

    except HTTPException:
        raise

    except Exception as e:
        print(
            f"ANALYSIS PIPELINE ERROR | "
            f"type={type(e).__name__} | "
            f"error={repr(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis pipeline failed: "
                f"{str(e)}"
            )
        )


@router.post("/generate-notes")
async def generate_notes(
    payload: dict = Body(...)
):
    try:
        faculty_data = payload.get(
            "faculty_data"
        )

        topic = payload.get(
            "topic"
        )

        student_evidence = payload.get(
            "student_evidence",
            ""
        )

        all_gaps = payload.get(
            "all_gaps",
            []
        )

        if not faculty_data:
            raise HTTPException(
                status_code=400,
                detail="Faculty data is required for note generation."
            )

        if topic == "all":
            all_notes = []

            for gap in all_gaps:
                try:
                    await asyncio.sleep(0.5)

                    gap_info = (
                        gap
                        if isinstance(gap, dict)
                        else {
                            "topic": getattr(
                                gap,
                                "topic",
                                "Unknown"
                            ),
                            "summary": getattr(
                                gap,
                                "summary",
                                ""
                            ),
                        }
                    )

                    note = await generate_topic_notes(
                        gap_info,
                        faculty_data,
                        gap_info.get(
                            "summary",
                            ""
                        ),
                    )

                    all_notes.append(
                        note
                    )

                except Exception as e:
                    print(
                        f"NOTE ERROR | "
                        f"topic={gap_info.get('topic')} | "
                        f"error={repr(e)}"
                    )

                    all_notes.append(
                        {
                            "topic": gap_info.get(
                                "topic",
                                "Unknown"
                            ),
                            "status": "error",
                            "sections": [
                                {
                                    "heading": "Error",
                                    "content": (
                                        "Failed to generate notes "
                                        "for this topic."
                                    ),
                                }
                            ],
                        }
                    )

            return all_notes

        if not topic:
            raise HTTPException(
                status_code=400,
                detail="Topic data is required for note generation."
            )

        return await generate_topic_notes(
            topic,
            faculty_data,
            student_evidence,
        )

    except HTTPException:
        raise

    except Exception as e:
        print(
            f"NOTE GENERATION ERROR | "
            f"type={type(e).__name__} | "
            f"error={repr(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate study notes: "
                f"{str(e)}"
            )
        )


@router.post("/chat")
async def chat(
    payload: dict = Body(...)
):
    try:
        notes = payload.get(
            "notes",
            ""
        )

        question = payload.get(
            "question",
            ""
        )

        answer = await get_chat_response(
            message=question,
            context={
                "notes": notes
            },
            history=[],
        )

        return {
            "answer": answer
        }

    except Exception as e:
        print(
            f"CHAT ERROR | "
            f"type={type(e).__name__} | "
            f"error={repr(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Chat failed: "
                f"{str(e)}"
            )
        )