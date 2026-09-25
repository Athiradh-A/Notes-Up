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
                        topic
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
                detail=(
                    "Faculty data is required "
                    "for note generation."
                )
            )


        # -------------------------------------------------
        # CONVERT FACULTY DATA TO TEXT
        # -------------------------------------------------

        if isinstance(
            faculty_data,
            list
        ):

            faculty_context = "\n\n".join(
                str(
                    page.get(
                        "content",
                        ""
                    )
                )
                for page in faculty_data
                if isinstance(page, dict)
            )

        else:

            faculty_context = str(
                faculty_data
            )


        # -------------------------------------------------
        # GENERATE NOTES FOR ALL GAPS
        # -------------------------------------------------

        if topic == "all":

            all_notes = []


            for gap in all_gaps:

                try:

                    await asyncio.sleep(
                        0.5
                    )


                    if isinstance(
                        gap,
                        dict
                    ):

                        gap_info = gap

                    else:

                        gap_info = {
                            "topic": str(
                                gap
                            ),
                            "status": "missing",
                            "why_needed": "",
                            "student_knowledge": "",
                            "missing_information": []
                        }


                    gap_topic = gap_info.get(
                        "topic",
                        "Unknown"
                    )

                    gap_status = gap_info.get(
                        "status",
                        "missing"
                    )

                    gap_why_needed = gap_info.get(
                        "why_needed",
                        ""
                    )

                    gap_student_knowledge = gap_info.get(
                        "student_knowledge",
                        ""
                    )

                    gap_missing_information = gap_info.get(
                        "missing_information",
                        []
                    )


                    note = await generate_study_notes(

                        gap_topic,

                        gap_status,

                        gap_why_needed,

                        gap_student_knowledge,

                        gap_missing_information,

                        faculty_context
                    )


                    all_notes.append(
                        note
                    )


                except Exception as e:

                    print(
                        f"Error generating note "
                        f"for {gap_info.get('topic')}: "
                        f"{str(e)}"
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
                                        "Failed to generate "
                                        "notes for this topic. "
                                        "Please try generating "
                                        "it individually."
                                    )
                                }
                            ]
                        }
                    )


            return all_notes


        # -------------------------------------------------
        # GENERATE NOTES FOR ONE TOPIC
        # -------------------------------------------------

        if not topic:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Topic data is required "
                    "for note generation."
                )
            )


        # Frontend sends the complete topic object
        if isinstance(
            topic,
            dict
        ):

            topic_name = topic.get(
                "topic",
                "Unknown"
            )

            status = topic.get(
                "status",
                "missing"
            )

            why_needed = topic.get(
                "why_needed",
                ""
            )

            student_knowledge = topic.get(
                "student_knowledge",
                student_evidence
            )

            missing_information = topic.get(
                "missing_information",
                []
            )

        else:

            topic_name = str(
                topic
            )

            status = "missing"

            why_needed = ""

            student_knowledge = (
                student_evidence
            )

            missing_information = []


        note = await generate_study_notes(

            topic_name,

            status,

            why_needed,

            student_knowledge,

            missing_information,

            faculty_context
        )


        return note


    except HTTPException:
        raise


    except Exception as e:

        print(
            f"Notes Generation Error: "
            f"{str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate study notes: "
                f"{str(e)}"
            )
        )


# =========================================================
# CHAT
# =========================================================

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


        if not message.strip():

            raise HTTPException(
                status_code=400,
                detail=(
                    "Message cannot be empty."
                )
            )


        # The current AI service expects:
        #
        # chat_with_notes(
        #     notes,
        #     question
        # )
        #
        # The frontend currently sends the
        # analysis result as "context".
        #
        # Convert that context into text.

        if isinstance(
            context,
            str
        ):

            notes_context = context

        else:

            notes_context = json.dumps(
                context,
                indent=2
            )


        response = await chat_with_notes(

            notes_context,

            message
        )


        return {
            "response": response
        }


    except HTTPException:
        raise


    except Exception as e:

        print(
            f"Chat Error: "
            f"{str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Chat failed: {str(e)}"
            )
        )