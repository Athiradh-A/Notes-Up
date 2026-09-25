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
        print("Testing root endpoint...")
        r = requests.get("http://127.0.0.1:8000/")
        print(f"Root Response: {r.json()}")
        
        print("\nTesting /analyze endpoint...")
        # Create dummy files
        with open("test_faculty.pdf", "wb") as f: f.write(b"%PDF-1.4 dummy")
        with open("test_note.jpg", "wb") as f: f.write(b"\xff\xd8 dummy")

        # CORRECT format for FastAPI list[UploadFile]
        files = [
            ("faculty_file", ("test_faculty.pdf", open("test_faculty.pdf", "rb"), "application/pdf")),
            ("student_images", ("test_note.jpg", open("test_note.jpg", "rb"), "image/jpeg")),
        ]
        
        r_analyze = requests.post("http://127.0.0.1:8000/analyze", files=files)
        print(f"Status: {r_analyze.status_code}")
        print(f"Analysis Response: {r_analyze.json()}")
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        p.terminate()
        # Close files before removing
        # In a real script we should use 'with' or .close(), but for this quick test we'll just try to delete them if the process ended.
        time.sleep(1)
        try:
            if os.path.exists("test_faculty.pdf"): os.remove("test_faculty.pdf")
            if os.path.exists("test_note.jpg"): os.remove("test_note.jpg")
        except: pass
