import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from app.schemas.analysis import AnalysisResponse, ChatRequest
from app.services.doc_service import extract_text
from app.services.ai_service import transcribe_images, perform_gap_analysis, get_chat_response, extract_faculty_topics, generate_topic_notes

router = APIRouter()

@router.post("/analyze")
async def analyze_notes(faculty_file: UploadFile = File(...), student_images: list[UploadFile] = File(...)):
    try:
        # 1. Extract raw text with page mapping
        faculty_data = await extract_text(faculty_file)
        if not faculty_data:
            raise HTTPException(status_code=400, detail="No readable content found in faculty materials.")
        
        # 2. Transcribe student notes
        transcribed_notes = await transcribe_images(student_images)
        
        # 3. Extract structured Knowledge Map from faculty materials
        try:
            knowledge_map = await extract_faculty_topics(faculty_data)
        except Exception as e:
            print(f"Knowledge Map Error: {e}")
            knowledge_map = []
        
        # 4. Perform Gap Analysis
        result = await perform_gap_analysis(faculty_data, transcribed_notes, knowledge_map)
        
        # Attach raw faculty data to the response as a hidden field 
        # so the frontend can send it back for note generation.
        response_dict = result.dict()
        response_dict["_faculty_raw"] = faculty_data
        
        return response_dict
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Critical Pipeline Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {str(e)}")

@router.post("/generate-notes")
async def generate_notes(payload: dict = Body(...)):
    try:
        faculty_data = payload.get("faculty_data")
        topic = payload.get("topic")
        student_evidence = payload.get("student_evidence", "")
        all_gaps = payload.get("all_gaps", [])

        if not faculty_data:
            raise HTTPException(status_code=400, detail="Faculty data is required for note generation.")

        if topic == "all":
            all_notes = []
            for gap in all_gaps:
                try:
                    await asyncio.sleep(0.5)
                    # Use the gap object directly, ensuring it has a summary
                    gap_info = gap if isinstance(gap, dict) else {"topic": getattr(gap, 'topic', 'Unknown'), "summary": getattr(gap, 'summary', '')}
                    note = await generate_topic_notes(gap_info, faculty_data, gap_info.get("summary", ""))
                    all_notes.append(note)
                except Exception as e:
                    print(f"Error generating note for {gap_info.get('topic')}: {e}")
                    all_notes.append({
                        "topic": gap_info.get("topic", "Unknown"),
                        "status": "error",
                        "sections": [{"heading": "Error", "content": "Failed to generate notes for this topic. Please try generating it individually."}]
                    })
            return all_notes
        
        if not topic:
            raise HTTPException(status_code=400, detail="Topic data is required for note generation.")
            
        note = await generate_topic_notes(topic, faculty_data, student_evidence)
        return note
        
    except Exception as e:
        print(f"Notes Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate study notes: {str(e)}")

@router.post("/chat")
async def chat_with_analysis(request: ChatRequest):
    try:
        response = await get_chat_response(request.message, request.context, request.history)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
