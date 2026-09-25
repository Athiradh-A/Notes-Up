import multiprocessing
import time
import requests
import os
from app.main import app
import uvicorn

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == "__main__":
    p = multiprocessing.Process(target=run_server)
    p.start()
    time.sleep(3)
    
    try:
        print("--- API Validation Phase 10 ---")
        
        # 1. Root check
        r = requests.get("http://127.0.0.1:8000/")
        print(f"Root: {r.status_code} - OK")
        
        # 2. Analysis pipeline check
        with open("test_faculty.pdf", "wb") as f: f.write(b"%PDF-1.4 dummy")
        with open("test_note.jpg", "wb") as f: f.write(b"\xff\xd8 dummy")

        files = [
            ("faculty_file", ("test_faculty.pdf", open("test_faculty.pdf", "rb"), "application/pdf")),
            ("student_images", ("test_note.jpg", open("test_note.jpg", "rb"), "image/jpeg")),
        ]
        
        print("Testing /analyze pipeline...")
        r_analyze = requests.post("http://127.0.0.1:8000/analyze", files=files)
        
        if r_analyze.status_code == 200:
            data = r_analyze.json()
            print("✅ Analysis endpoint returned 200")
            print(f"Found Missing: {len(data.get('missing_topics', []))}")
            print(f"Found Partially Covered: {len(data.get('partially_covered_topics', []))}")
            print(f"Found Covered: {len(data.get('covered_topics', []))}")
            print(f"Knowledge Map Size: {len(data.get('faculty_knowledge_map', []))}")
        else:
            print(f"❌ Analysis endpoint failed: {r_analyze.status_code} - {r_analyze.text}")

    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        p.terminate()
        time.sleep(1)
        try:
            if os.path.exists("test_faculty.pdf"): os.remove("test_faculty.pdf")
            if os.path.exists("test_note.jpg"): os.remove("test_note.jpg")
        except: pass
