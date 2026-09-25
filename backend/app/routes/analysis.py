import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Body

from app.services.doc_service import extract_text
from app.services.ai_service import (
    transcribe_images,
    perform_gap_analysis,
    chat_with_notes,
    extract_faculty_topics,
    generate_study_notes,
)

router = APIRouter()


@router.post("/analyze")
async def analyze_notes(
    faculty_file: UploadFile = File(...),
    student_images: list[UploadFile] = File(...)
):
    try:
        # 1. Extract faculty material
        faculty_data = await extract_text(faculty_file)

        if not faculty_data:
            raise HTTPException(
                status_code=400,
                detail="No readable content found in faculty materials."
            )

        print(
            f"FACULTY TEXT EXTRACTED | pages={len(faculty_data)}"
        )

        # 2. Transcribe student handwritten notes
        transcribed_notes = await transcribe_images(student_images)

        print(
            f"STUDENT NOTES TRANSCRIBED | characters={len(transcribed_notes)}"
        )

        # 3. Extract faculty knowledge map
        try:
            knowledge_map = await extract_faculty_topics(
                faculty_data
            )
        except Exception as e:
            print(
                f"Knowledge Map Error: {str(e)}"
            )
            knowledge_map = []

        # 4. Perform gap analysis
        result = await perform_gap_analysis(
            faculty_data,
            transcribed_notes,
            knowledge_map
        )

        print(
            "GAP ANALYSIS COMPLETE"
        )

        # 5. Convert response to dictionary
        if hasattr(result, "model_dump"):
            response_dict = result.model_dump()
        elif hasattr(result, "dict"):
            response_dict = result.dict()
        else:
            response_dict = result

        # Keep the extracted faculty material available
        # for later note generation.
        response_dict["_faculty_raw"] = faculty_data

        return response_dict

    except HTTPException:
        raise

    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )

    except Exception as e:
        print(
            f"Critical Pipeline Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Analysis pipeline failed: {str(e)}"
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

        # Generate notes for all missing/partial topics
        if topic == "all":

            all_notes = []

            for gap in all_gaps:

                try:
                    await asyncio.sleep(0.5)

                    if isinstance(gap, dict):
                        gap_info = gap
                    else:
                        gap_info = {
                            "topic": getattr(
                                gap,
                                "topic",
                                "Unknown"
                            ),
                            "summary": getattr(
                                gap,
                                "summary",
                                ""
                            )
                        }

                    note = await generate_study_notes(
                        gap_info,
                        faculty_data,
                        gap_info.get(
                            "summary",
                            ""
                        )
                    )

                    all_notes.append(
                        note
                    )

                except Exception as e:

                    print(
                        f"Error generating note for "
                        f"{gap_info.get('topic')}: {str(e)}"
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
                                        "for this topic. Please try "
                                        "generating it individually."
                                    )
                                }
                            ]
                        }
                    )

            return all_notes

        if not topic:
            raise HTTPException(
                status_code=400,
                detail="Topic data is required for note generation."
            )

        # Generate notes for one topic
        note = await generate_study_notes(
            topic,
            faculty_data,
            student_evidence
        )

        return note

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"Notes Generation Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to generate study notes: "
                f"{str(e)}"
            )
        )


@router.post("/chat")
async def chat(
    payload: dict = Body(...)
):
    try:
        message = payload.get(
            "message",
            ""
        )

        context = payload.get(
            "context",
            {}
        )

        history = payload.get(
            "history",
            []
        )

        if not message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty."
            )

        response = await chat_with_notes(
            message,
            context,
            history
        )

        return {
            "response": response
        }

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"Chat Error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )