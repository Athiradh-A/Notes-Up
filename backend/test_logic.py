import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Add backend to path
sys.path.append("C:/Users/athir/study-sanctuary/study-sanctuary/backend")

try:
    from app.services.doc_service import sanitize_filename, extract_text
    from app.services.ai_service import perform_gap_analysis, transcribe_images
    from app.schemas.analysis import AnalysisResponse, Topic
    print("Imports successful")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

async def test_logic():
    print("\n--- Testing Sanitization ---")
    dirty_name = "my notes; drop table users.pdf"
    clean_name = sanitize_filename(dirty_name)
    print(f"Input: {dirty_name} -> Output: {clean_name}")
    assert "drop" in clean_name and ";" not in clean_name
    print("Sanitization works")

    print("\n--- Testing AI Logic (Mocked) ---")
    # Correct data format: List of Dicts
    mock_faculty_data = [
        {"page": 1, "content": "Introduction to Atoms"},
        {"page": 2, "content": "The Bohr Model"}
    ]
    res = await perform_gap_analysis(mock_faculty_data, "Student text")
    print(f"Demo Mode Result: {res.missing_topics[0].topic}")
    assert isinstance(res, AnalysisResponse)
    print("Demo mode logic works")

    print("\n--- Testing Transcription (Mocked) ---")
    mock_file = AsyncMock()
    mock_file.filename = "note1.jpg"
    mock_file.read.return_value = b"fake image bytes"
    
    res_trans = await transcribe_images([mock_file])
    print(f"Transcription Result: {res_trans}")
    assert "MOCK" in res_trans or "No transcription" in res_trans
    print("Transcription logic works")

if __name__ == "__main__":
    asyncio.run(test_logic())
