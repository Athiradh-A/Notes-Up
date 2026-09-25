# 📚 Study Sanctuary: AI Student Notes Gap Analyzer

Study Sanctuary is a professional, full-stack web application designed to help students identify exactly what they are missing from their study notes compared to faculty-provided materials.

## 🌟 Core Product Promise
**Compare what you are expected to know with what your notes actually contain.**

## ✨ Key Features
- **Faculty Material Analysis:** Upload PDF or PPTX files. The AI extracts content and creates a structured **Course Knowledge Map**.
- **Handwriting Transcription:** Upload JPG/PNG notes. Uses Vision AI to transcribe handwritten text into structured digital data.
- **Conceptual Gap Analysis:** Instead of simple text matching, the AI identifies **conceptual gaps**, categorizing topics as:
    - 🔴 **Missing:** Entirely absent from notes.
    - 🟡 **Partially Covered:** Mentioned, but lacking depth or key formulas.
    - 🟢 **Mastered:** Fully covered.
- **Contextual Chat:** A dedicated AI assistant that helps you bridge the gaps based on the specific analysis of your files.
- **Session Persistence:** Analysis results and chat history are saved locally in the browser.

## 🛠️ Tech Stack
- **Frontend:** Next.js 14+, TypeScript, Tailwind CSS, Framer Motion, Lucide Icons.
- **Backend:** FastAPI (Python), Pydantic (Validation), Python-dotenv.
- **AI Orchestration:** Groq API (Llama 3.2 Vision, Llama 3.1/3.3).
- **Document Processing:** PyPDF, python-pptx.

## 🚀 Getting Started

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the `backend` folder:
   ```text
   GROQ_API_KEY=your_groq_api_key_here
   ```
4. Run the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open `http://localhost:3000` in your browser.

## 📐 Project Architecture
The backend follows a professional modular structure:
- `app/core/`: Configuration and client initialization.
- `app/schemas/`: Pydantic data contracts.
- `app/services/`: Business logic (AI and Document processing).
- `app/routes/`: API endpoint definitions.

## 🛡️ Security & Reliability
- **Input Sanitization:** Filenames are sanitized to prevent injection attacks.
- **Structured Output:** All AI responses are validated through Pydantic schemas.
- **Secret Management:** Keys are kept in `.env` and excluded from version control via `.gitignore`.
