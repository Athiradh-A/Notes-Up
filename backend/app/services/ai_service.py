import json
import base64
from app.core.config import client, GROQ_TEXT_MODEL, GROQ_VISION_MODEL
from app.schemas.analysis import AnalysisResponse, Topic, FacultyTopic, StudentTopic

def encode_image(file_bytes):
    return base64.b64encode(file_bytes).decode('utf-8')

async def transcribe_images(student_images):
    if not client:
        raise Exception("GROQ_API_KEY is missing or invalid. Configure the backend environment before running analysis.")

    transcribed_notes = ""
    for i, img_file in enumerate(student_images):
        img_bytes = await img_file.read()
        base64_image = encode_image(img_bytes)
        try:
            vision_response = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"You are an expert handwriting transcriber. Please transcribe the following image (Note {i+1}) into clear, structured text. Maintain the original meaning and structure. If the text is illegible, mark it as [illegible]. Return only the transcription."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ],
                    }
                ],
                model=GROQ_VISION_MODEL,
            )
            transcribed_notes += f"--- Note {i+1} ---\n{vision_response.choices[0].message.content}\n\n"
        except Exception as e:
            print(f"Error transcribing image {img_file.filename}: {e}")
            raise e
    
    return transcribed_notes if transcribed_notes else "No transcription available."

async def extract_faculty_topics(faculty_data):
    if not client:
        raise Exception("GROQ_API_KEY is missing or invalid. Configure the backend environment before running analysis.")

    faculty_context = ""
    for entry in faculty_data:
        faculty_context += f"[Page/Slide {entry['page']}]: {entry['content']}\n\n"

    topic_prompt = f"""
    You are an expert curriculum designer. Analyze the following faculty materials and extract a structured knowledge map.
    
    FACULTY MATERIALS:
    {faculty_context[:6000]}
    
    TASK:
    Identify the core concepts, key formulas, and critical learning objectives. 
    For each topic, determine its importance (High/Medium/Low) and note the page/slide number.
    
    FORMAT:
    Return a JSON object strictly following this schema:
    {{ 
      "faculty_knowledge_map": [
        {{ 
          "topic": "Concept Name", 
          "description": "What the student needs to understand", 
          "importance": "High", 
          "page_reference": "Page 2" 
        }}
      ] 
    }}
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": topic_prompt}],
        model=GROQ_TEXT_MODEL,
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    return data.get("faculty_knowledge_map", [])

async def extract_student_topics(transcribed_notes):
    if not client:
        raise Exception("GROQ_API_KEY is missing or invalid. Configure the backend environment before running analysis.")

    student_prompt = f"""
    You are an expert academic analyst. Analyze the following student's handwritten notes.
    
    STUDENT NOTES:
    {transcribed_notes}
    
    TASK:
    Identify the core concepts, formulas, and topics the student has actually written down.
    For each topic, provide a brief piece of evidence (quote or summary) from their notes and an assessment of whether the coverage seems complete or just a mention.
    
    FORMAT:
    Return a JSON object strictly following this schema:
    {{ 
      "student_knowledge_map": [
        {{ 
          "topic": "Concept Name", 
          "evidence": "Quote from notes", 
          "completeness": "Complete/Incomplete" 
        }}
      ] 
    }}
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": student_prompt}],
        model=GROQ_TEXT_MODEL,
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    return data.get("student_knowledge_map", [])

async def perform_gap_analysis(faculty_data, transcribed_notes, faculty_map):
    if not client:
        raise Exception("GROQ_API_KEY is missing or invalid. Configure the backend environment before running analysis.")

    student_map = await extract_student_topics(transcribed_notes)

    faculty_context = ""
    for entry in faculty_data:
        faculty_context += f"[Page/Slide {entry['page']}]: {entry['content']}\n\n"

    analysis_prompt = f"""
    You are a world-class study assistant.
    
    EXPECTED KNOWLEDGE MAP (The curriculum):
    {json.dumps(faculty_map, indent=2)}
    
    STUDENT KNOWLEDGE MAP (What was FOUND in notes):
    {json.dumps(student_map, indent=2)}
    
    RAW FACULTY TEXT (For detail):
    {faculty_context[:5000]}
    
    TASK:
    Compare the Student Map against the Faculty Map.
    1. COVERED: Topic is in both maps and student evidence is "Complete".
    2. PARTIALLY COVERED: Topic is in both maps but student evidence is "Incomplete" or missing key details.
    3. MISSING: Topic is in Faculty Map but entirely absent from Student Map.
    
    FORMAT:
    Return a JSON object strictly following this schema:
    {{ 
      "missing_topics": [{{ "topic": "Name", "summary": "Detailed gap + Page ref", "status": "missing" }}], 
      "partially_covered_topics": [{{ "topic": "Name", "summary": "What is missing from the mention", "status": "partially_covered" }}], 
      "covered_topics": ["Topic A", "Topic B"] 
    }}
    """
    
    analysis_response = client.chat.completions.create(
        messages=[{"role": "user", "content": analysis_prompt}],
        model=GROQ_TEXT_MODEL,
        response_format={"type": "json_object"}
    )
    
    result_data = json.loads(analysis_response.choices[0].message.content)
    
    return AnalysisResponse(
        missing_topics=[Topic(**t) for t in result_data.get("missing_topics", [])],
        partially_covered_topics=[Topic(**t) for t in result_data.get("partially_covered_topics", [])],
        covered_topics=result_data.get("covered_topics", []),
        faculty_knowledge_map=faculty_map,
        student_knowledge_map=student_map
    )

async def generate_topic_notes(topic_data, faculty_data, student_evidence):
    if not client:
        raise Exception("GROQ_API_KEY is missing or invalid.")

    faculty_context = ""
    for entry in faculty_data:
        faculty_context += f"[Page {entry['page']}]: {entry['content']}\n\n"

    status = topic_data.get("status", "missing")
    topic_name = topic_data.get("topic", "Unknown Topic")
    gap_summary = topic_data.get("summary", "No specific gap identified.")

    notes_prompt = f"""
    You are a world-class academic tutor creating structured exam-preparation notes.
    
    TOPIC: {topic_name}
    STATUS: {status}
    IDENTIFIED GAP: {gap_summary}
    STUDENT EVIDENCE: {student_evidence}
    
    FACULTY MATERIAL (Authoritative Source):
    {faculty_context[:6000]}
    
    TASK:
    {'Generate a complete but concise set of study notes for this missing topic.' if status == 'missing' else 'Generate targeted notes ONLY for the missing portions of this partially covered topic. Avoid repeating material the student already knows.'}
    
    GUIDELINES:
    - PRIMARY SOURCE: Use ONLY the provided faculty material. Do not invent definitions or equations.
    - STYLE: Structured, clear, concise, and exam-focused. No conversational filler.
    - MATH: Use LaTeX for equations (e.g., $$E=mc^2$$). Explain variables immediately below.
    - STRUCTURE: Use headings, subheadings, numbered steps, and bullet points.
    
    EXPECTED SECTIONS (Include only if applicable):
    - Definition / Meaning
    - Core Concept
    - Components
    - Formula / Mathematical Representation
    - Working / Steps
    - Example
    - Important/Exam Points
    
    FORMAT:
    Return a JSON object strictly following this schema:
    {{
      "topic": "{topic_name}",
      "status": "{status}",
      "why_needed": "Short explanation of why this is critical",
      "missing_information": ["point 1", "point 2"],
      "sections": [
        {{
          "heading": "Section Title",
          "content": "Detailed but concise explanation",
          "equations": ["LaTeX equation 1", "LaTeX equation 2"]
        }}
      ],
      "exam_points": ["Key point 1", "Key point 2"],
      "sources": ["Page X", "Slide Y"]
    }}
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": notes_prompt}],
        model=GROQ_TEXT_MODEL,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

async def get_chat_response(message, context, history):
    if not client:
        raise Exception("GROQ_API_KEY is missing or invalid. Configure the backend environment before running analysis.")

    system_prompt = f"""
    You are a specialized study assistant. You are helping a student bridge the gap between their notes and faculty materials.
    
    Current Analysis Context:
    - Missing Topics: {json.dumps(context.get('missing_topics', []))}
    - Covered Topics: {json.dumps(context.get('covered_topics', []))}
    
    Your goal is to provide specific, actionable study advice based on the missing topics. Be encouraging and academic.
    """

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        messages=messages,
        model=GROQ_TEXT_MODEL,
    )

    return response.choices[0].message.content
