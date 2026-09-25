from typing import List

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
)

from app.services.doc_service import extract_text

from app.services.ai_service import (
    transcribe_images,
    extract_faculty_topics,
    extract_student_topics,
    perform_gap_analysis,
    generate_study_notes,
    chat_with_notes,
)

from app.schemas.analysis import (
    NoteGenerationRequest,
    ChatRequest,
)


router = APIRouter()


# =========================================================
# ANALYZE
# =========================================================

@router.post("/analyze")
async def analyze(
    faculty_file: UploadFile = File(...),
    student_images: List[UploadFile] = File(...),
):
    try:
        print(
            f"ANALYZE START | "
            f"faculty={faculty_file.filename} | "
            f"student_images={len(student_images)}"
        )

        # -------------------------------------------------
        # STEP 1: FACULTY DOCUMENT
        # -------------------------------------------------

        faculty_text = await extract_text(
            faculty_file
        )

        print(
            "FACULTY TEXT EXTRACTED | "
            f"characters={len(faculty_text)}"
        )

        # -------------------------------------------------
        # STEP 2: STUDENT HANDWRITTEN NOTES
        # -------------------------------------------------

        student_text = await transcribe_images(
            student_images
        )

        print(
            "STUDENT NOTES TRANSCRIBED | "
            f"characters={len(student_text)}"
        )

        # -------------------------------------------------
        # STEP 3: FACULTY TOPICS
        # -------------------------------------------------

        faculty_topics = await extract_faculty_topics(
            faculty_text
        )

        print(
            "FACULTY TOPICS EXTRACTED | "
            f"count={len(faculty_topics)}"
        )

        # -------------------------------------------------
        # STEP 4: STUDENT TOPICS
        # -------------------------------------------------

        student_topics = await extract_student_topics(
            student_text
        )

        print(
            "STUDENT TOPICS EXTRACTED | "
            f"count={len(student_topics)}"
        )

        # -------------------------------------------------
        # STEP 5: GAP ANALYSIS
        # -------------------------------------------------

        result = await perform_gap_analysis(
            faculty_topics,
            student_topics,
        )

        print(
            "GAP ANALYSIS COMPLETE"
        )

        return result

    except Exception as e:
        print(
            f"ANALYSIS ERROR | "
            f"type={type(e).__name__} | "
            f"error={repr(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis pipeline failed: "
                f"{str(e)}"
            ),
        )


# =========================================================
# GENERATE STUDY NOTES
# =========================================================

@router.post("/generate-notes")
async def generate_notes(
    request: NoteGenerationRequest,
):
    try:
        result = await generate_study_notes(
            topic=request.topic,
            status=request.status,
            why_needed=request.why_needed,
            student_knowledge=request.student_knowledge,
            missing_information=request.missing_information,
            faculty_context=getattr(
                request,
                "faculty_context",
                "",
            ),
        )

        return result

    except Exception as e:
        print(
            f"NOTE GENERATION ERROR | "
            f"type={type(e).__name__} | "
            f"error={repr(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Study note generation failed: "
                f"{str(e)}"
            ),
        )


# =========================================================
# CHAT
# =========================================================

@router.post("/chat")
async def chat(
    request: ChatRequest,
):
    try:
        answer = await chat_with_notes(
            notes=request.notes,
            question=request.question,
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
            ),
        )