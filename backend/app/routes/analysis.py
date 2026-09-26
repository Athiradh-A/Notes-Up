import asyncio
import json

from fastapi import APIRouter, UploadFile, File, HTTPException, Body

from app.services.doc_service import extract_text

from app.services.ai_service import (
    transcribe_images,
    extract_faculty_topics,
    extract_student_topics,
    perform_gap_analysis,
    generate_study_notes,
    chat_with_notes,
)


router = APIRouter()


# =========================================================
# ANALYZE
# =========================================================

@router.post("/analyze")
async def analyze_notes(
    faculty_file: UploadFile = File(...),
    student_images: list[UploadFile] = File(...)
):
    try:

        # -------------------------------------------------
        # 1. EXTRACT FACULTY MATERIAL
        # -------------------------------------------------

        faculty_data = await extract_text(
            faculty_file
        )

        if not faculty_data:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable content found "
                    "in faculty materials."
                )
            )

        print(
            f"FACULTY TEXT EXTRACTED | "
            f"pages={len(faculty_data)}"
        )


        # Convert page/slide objects into one text string
        faculty_text = "\n\n".join(
            str(page.get("content", ""))
            for page in faculty_data
        )


        # -------------------------------------------------
        # 2. TRANSCRIBE STUDENT HANDWRITTEN NOTES
        # -------------------------------------------------

        transcribed_notes = await transcribe_images(
            student_images
        )

        print(
            f"STUDENT NOTES TRANSCRIBED | "
            f"characters={len(transcribed_notes)}"
        )


        # -------------------------------------------------
        # 3. EXTRACT FACULTY TOPICS
        # -------------------------------------------------

        faculty_topics = await extract_faculty_topics(
            faculty_text
        )

        print(
            f"FACULTY TOPICS EXTRACTED | "
            f"count={len(faculty_topics)}"
        )


        # -------------------------------------------------
        # 4. EXTRACT STUDENT TOPICS
        # -------------------------------------------------

        student_topics = await extract_student_topics(
            transcribed_notes
        )

        print(
            f"STUDENT TOPICS EXTRACTED | "
            f"count={len(student_topics)}"
        )


        # -------------------------------------------------
        # 5. PERFORM GAP ANALYSIS
        # -------------------------------------------------

        result = await perform_gap_analysis(
            faculty_topics,
            student_topics
        )

        print(
            "GAP ANALYSIS COMPLETE"
        )


        # -------------------------------------------------
        # 6. CONVERT RESULT TO DICTIONARY
        # -------------------------------------------------

        if hasattr(result, "model_dump"):

            response_dict = result.model_dump()

        elif hasattr(result, "dict"):

            response_dict = result.dict()

        elif isinstance(result, dict):

            response_dict = result

        else:

            response_dict = {
                "result": result
            }


        # -------------------------------------------------
        # 7. ADD KNOWLEDGE MAPS
        # -------------------------------------------------

        response_dict[
            "faculty_knowledge_map"
        ] = faculty_topics

        response_dict[
            "student_knowledge_map"
        ] = student_topics


        # -------------------------------------------------
        # 8. CREATE STANDARD GAP ARRAYS
        # -------------------------------------------------

        missing_topics = []
        partially_covered_topics = []
        covered_topics = []


        # The AI response may return topics directly
        # or inside a "topics" field.

        analyzed_topics = response_dict.get(
            "topics",
            []
        )

        if isinstance(analyzed_topics, list):

            for topic in analyzed_topics:

                if not isinstance(topic, dict):
                    continue

                status = str(
                    topic.get(
                        "status",
                        ""
                    )
                ).lower().replace(
                    "_",
                    ""
                ).replace(
                    " ",
                    ""
                )

                if status == "missing":

                    missing_topics.append(
                        topic
                    )

                elif status in [
                    "partial",
                    "partiallycovered",
                    "partially_covered"
                ]:

                    partially_covered_topics.append(
                        topic
                    )

                elif status in [
                    "mastered",
                    "covered"
                ]:

                    covered_topics.append(
                        topic.get("topic", "Unknown")
                    )


        response_dict[
            "missing_topics"
        ] = missing_topics

        response_dict[
            "partially_covered_topics"
        ] = partially_covered_topics

        response_dict[
            "covered_topics"
        ] = covered_topics


        # -------------------------------------------------
        # 9. KEEP RAW FACULTY DATA
        # -------------------------------------------------

        response_dict[
            "_faculty_raw"
        ] = faculty_data


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
            f"Critical Pipeline Error: "
            f"{str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis pipeline failed: "
                f"{str(e)}"
            )
        )


# =========================================================
# GENERATE STUDY NOTES
# =========================================================

@router.post("/generate-notes")
async def generate_notes(payload: dict = Body(...)):
    try:
        topic = payload.get("topic")
        status = payload.get("status", "missing")
        why_needed = payload.get("why_needed", "")
        student_knowledge = payload.get("student_knowledge", "")
        missing_information = payload.get("missing_information", [])
        faculty_context = payload.get("faculty_context", "")

        # Backward-compatible support for older clients.
        if not faculty_context and payload.get("faculty_data"):
            faculty_data = payload.get("faculty_data")
            if isinstance(faculty_data, list):
                faculty_context = "\n\n".join(
                    str(page.get("content", ""))
                    for page in faculty_data
                    if isinstance(page, dict)
                )
            else:
                faculty_context = str(faculty_data)

        if isinstance(missing_information, str):
            missing_information = [missing_information]
        if not isinstance(missing_information, list):
            missing_information = []

        if not topic:
            raise HTTPException(
                status_code=400,
                detail="Topic data is required for note generation."
            )

        # Generate one combined guide when the frontend requests all gaps.
        if str(topic).strip().lower() in {
            "all",
            "all missing and partially covered topics",
            "all missing and partially covered topics"
        }:
            all_gaps = payload.get("all_gaps", [])
            if not all_gaps:
                all_gaps = [
                    {
                        "topic": line.split(":", 1)[0],
                        "status": "missing",
                        "why_needed": "",
                        "student_knowledge": "",
                        "missing_information": [line],
                    }
                    for line in missing_information
                    if isinstance(line, str) and line.strip()
                ]

            notes = []
            for gap in all_gaps:
                gap = gap if isinstance(gap, dict) else {"topic": str(gap)}
                notes.append(await generate_study_notes(
                    gap.get("topic", "Unknown"),
                    gap.get("status", "missing"),
                    gap.get("why_needed", ""),
                    gap.get("student_knowledge", ""),
                    gap.get("missing_information", []) if isinstance(gap.get("missing_information", []), list) else [],
                    faculty_context,
                ))
            return notes

        return await generate_study_notes(
            str(topic),
            str(status),
            str(why_needed),
            str(student_knowledge),
            missing_information,
            str(faculty_context),
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Notes Generation Error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate study notes: {str(e)}"
        )


# =========================================================
# CHAT
# =========================================================

@router.post("/chat")
async def chat(payload: dict = Body(...)):
    try:
        # Current frontend contract: {notes, question}.
        # Also accept the previous {context, message} contract.
        question = payload.get("question") or payload.get("message") or ""
        notes = payload.get("notes", payload.get("context", {}))

        if not str(question).strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty."
            )

        if isinstance(notes, str):
            notes_context = notes
        else:
            notes_context = json.dumps(notes, indent=2)

        answer = await chat_with_notes(notes_context, str(question))

        return {"answer": answer}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat Error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )
