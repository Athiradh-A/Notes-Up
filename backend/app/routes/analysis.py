import asyncio
import json

from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Response

from app.services.doc_service import extract_text, render_pdf_to_images

from app.services.typst_service import compile_study_guide_pdf

from app.services.ai_service import (
    analyze_materials_unified,
    generate_study_notes,
    generate_bulk_study_notes,
    chat_with_notes,
)


router = APIRouter()


# =========================================================
# ANALYZE
# =========================================================

@router.post("/analyze")
async def analyze_notes(
    faculty_file: UploadFile = File(...),
    student_images: list[UploadFile] | None = File(None),
    student_pdf: UploadFile | None = File(None),
):
    try:
        # -------------------------------------------------
        # 1. PREPARE STUDENT NOTE IMAGES
        # -------------------------------------------------
        student_images = student_images or []

        if student_pdf is not None:
            pdf_images = await render_pdf_to_images(student_pdf)
            student_images.extend(pdf_images)

        if not student_images:
            raise HTTPException(
                status_code=400,
                detail="Please upload handwritten notes as images or a PDF."
            )

        # -------------------------------------------------
        # 2. EXTRACT FACULTY MATERIAL LOCALLY
        # -------------------------------------------------
        # PDF/PPT text extraction does not require an AI request.
        faculty_data = await extract_text(faculty_file)

        if not faculty_data:
            raise HTTPException(
                status_code=400,
                detail="No readable content found in faculty materials."
            )

        faculty_text = "\n\n".join(
            str(page.get("content", ""))
            for page in faculty_data
        )

        print(
            f"FACULTY TEXT EXTRACTED | pages={len(faculty_data)}"
        )

        # -------------------------------------------------
        # 3. ONE UNIFIED MULTIMODAL AI REQUEST
        # -------------------------------------------------
        # The model receives the faculty text and ALL student
        # note images together and returns the complete result:
        # knowledge maps + gap analysis + generated study notes.
        result = await analyze_materials_unified(
            faculty_text=faculty_text,
            image_files=student_images,
        )

        if not isinstance(result, dict):
            raise ValueError(
                "Unified analysis returned an invalid JSON structure."
            )

        response_dict = result

        # Keep the raw faculty extraction for the existing
        # frontend/local-storage contract.
        response_dict["_faculty_raw"] = faculty_data

        faculty_topics = response_dict.get(
            "faculty_knowledge_map",
            []
        )
        student_topics = response_dict.get(
            "student_knowledge_map",
            []
        )
        analyzed_topics = response_dict.get(
            "topics",
            []
        )

        if not isinstance(faculty_topics, list):
            faculty_topics = []
            response_dict["faculty_knowledge_map"] = faculty_topics

        if not isinstance(student_topics, list):
            student_topics = []
            response_dict["student_knowledge_map"] = student_topics

        if not isinstance(analyzed_topics, list):
            analyzed_topics = []
            response_dict["topics"] = analyzed_topics

        # -------------------------------------------------
        # 4. CREATE STANDARD GAP ARRAYS
        # -------------------------------------------------
        missing_topics = []
        partially_covered_topics = []
        covered_topics = []

        faculty_by_topic = {
            str(item.get("topic", "")).strip().lower(): item
            for item in faculty_topics
            if isinstance(item, dict) and item.get("topic")
        }

        for topic in analyzed_topics:
            if not isinstance(topic, dict):
                continue

            if not str(topic.get("summary", "")).strip():
                faculty_item = faculty_by_topic.get(
                    str(topic.get("topic", "")).strip().lower()
                )
                if faculty_item:
                    topic["summary"] = faculty_item.get(
                        "description",
                        ""
                    ) or "This topic is required according to the faculty material."

            if not topic.get("why_needed"):
                topic["why_needed"] = topic.get("summary", "")

            status = (
                str(topic.get("status", ""))
                .lower()
                .replace("_", "")
                .replace(" ", "")
            )

            if status == "missing":
                missing_topics.append(topic)

            elif status in {
                "partial",
                "partiallycovered",
            }:
                partially_covered_topics.append(topic)

            elif status in {
                "mastered",
                "covered",
            }:
                covered_topics.append(
                    topic.get("topic", "Unknown")
                )

        response_dict["missing_topics"] = missing_topics
        response_dict["partially_covered_topics"] = partially_covered_topics
        response_dict["covered_topics"] = covered_topics

        # Ensure generated_notes is always a list so the frontend
        # can use it directly without another AI request.
        generated_notes = response_dict.get(
            "generated_notes",
            []
        )
        if not isinstance(generated_notes, list):
            generated_notes = []

        response_dict["generated_notes"] = [
            note for note in generated_notes
            if isinstance(note, dict)
        ]

        print(
            "UNIFIED ANALYSIS COMPLETE | "
            f"faculty_topics={len(faculty_topics)} | "
            f"student_topics={len(student_topics)} | "
            f"gaps={len(missing_topics) + len(partially_covered_topics)} | "
            f"generated_notes={len(response_dict['generated_notes'])}"
        )

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
            f"Critical Unified Pipeline Error: "
            f"{type(e).__name__}: {str(e)}"
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

            normalized_gaps = []

            for gap in all_gaps:
                gap = (
                    gap
                    if isinstance(gap, dict)
                    else {"topic": str(gap)}
                )

                normalized_gaps.append({
                    "topic": gap.get("topic", "Unknown"),
                    "status": gap.get("status", "missing"),
                    "why_needed": gap.get("why_needed", ""),
                    "student_knowledge": gap.get("student_knowledge", ""),
                    "missing_information": (
                        gap.get("missing_information", [])
                        if isinstance(
                            gap.get("missing_information", []),
                            list
                        )
                        else []
                    ),
                })

            return await generate_bulk_study_notes(
                normalized_gaps,
                faculty_context,
            )

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
# GENERATE PDF
# =========================================================

@router.post("/generate-pdf")
async def generate_pdf(payload: dict = Body(...)):
    try:
        notes = payload.get("notes")

        # Accept the current {notes: ...} contract and a safe fallback
        # for clients that may send the generated content under {content: ...}.
        if notes is None:
            notes = payload.get("content")

        title = str(payload.get("title") or "AI Study Guide")

        print(
            "PDF REQUEST | "
            f"title={title!r} | "
            f"payload_keys={list(payload.keys())} | "
            f"notes_type={type(notes).__name__}"
        )

        if not notes:
            raise HTTPException(
                status_code=400,
                detail="Study notes are required for PDF generation."
            )

        if isinstance(notes, str):
            try:
                notes = json.loads(notes)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid notes JSON: {e}"
                )

        if not isinstance(notes, (dict, list)):
            raise HTTPException(
                status_code=400,
                detail="Study notes must be an object or list of objects."
            )

        pdf_bytes = compile_study_guide_pdf(notes, title)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="notes-up-study-guide.pdf"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"PDF Generation Error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
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
