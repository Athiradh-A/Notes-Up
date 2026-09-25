<div align="center">

# 🎓 AI Study Gap Analyzer

### Faculty Material → Student Notes → AI Gap Analysis → Personalized Study Notes

<p>
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white" />
  <img src="https://img.shields.io/badge/React-000000?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/TypeScript-000000?style=for-the-badge&logo=typescript&logoColor=3178C6" />
  <img src="https://img.shields.io/badge/Python-000000?style=for-the-badge&logo=python&logoColor=FFD43B" />
  <img src="https://img.shields.io/badge/FastAPI-000000?style=for-the-badge&logo=fastapi&logoColor=00C853" />
</p>

<p>
  <img src="https://img.shields.io/badge/Groq-000000?style=for-the-badge&logo=groq&logoColor=white" />
  <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemma-000000?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/GitHub-000000?style=for-the-badge&logo=github&logoColor=white" />
</p>

<p>
  <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" />
  <img src="https://img.shields.io/badge/Render-000000?style=for-the-badge&logo=render&logoColor=white" />
  <img src="https://img.shields.io/badge/REST%20API-000000?style=for-the-badge&logo=fastapi&logoColor=00C853" />
</p>

<br>

**An AI-powered personalized learning platform that compares faculty-provided
academic material with student notes, identifies knowledge gaps, and generates
targeted, exam-oriented study notes.**

<br>

**Developed with assistance from a locally running AI model using Ollama.**

</div>

---

# 📌 Overview

The **AI Study Gap Analyzer** is an AI-powered academic assistance platform designed to determine what a student has covered, what they have partially covered, and what they are still missing when compared against faculty-provided learning material.

Students often maintain their own notes throughout a semester, but these notes may not contain every topic, definition, formula, derivation, algorithm, example, or important concept included in the official course material.

The application addresses this problem by comparing two sources:

```text
Faculty Material
       +
Student Notes
       ↓
AI-Powered Comparison
       ↓
Knowledge Gap Detection
       ↓
MISSING / PARTIAL / MASTERED
       ↓
Targeted Study Notes
```

The system can process both **digital academic material** and **handwritten student notes**.

For identified gaps, students can request AI-generated study notes focused specifically on the missing content.

---

# 🎯 Problem Statement

A student may have several pages of notes for a subject while still missing important concepts from the faculty's material.

For example, a faculty module may contain:

```text
• Markov Decision Processes
• Bellman Equation
• Policy Evaluation
• Policy Iteration
• Value Iteration
• Q-Learning
```

while the student's notes may only contain:

```text
• Markov Decision Processes
• Bellman Equation
• Policy Evaluation
```

Traditional note-taking systems do not automatically identify this difference.

The AI Study Gap Analyzer attempts to answer:

> **"What topics from the required learning material are missing or incomplete in my notes?"**

Once the gaps are identified, the system can answer the next question:

> **"What should I study to complete those gaps?"**

---

# 💡 Core Concept

The central idea of the system is:

```text
Faculty Material
      │
      │ Defines expected coverage
      ▼
Expected Topics
      │
      │ Compare
      ▼
Student Notes
      │
      │ Provides existing evidence
      ▼
Coverage Analysis
      │
      ├──────────────┬──────────────┐
      ▼              ▼              ▼
   MISSING         PARTIAL       MASTERED
      │              │
      └───────┬──────┘
              ▼
       AI Note Generation
              │
              ▼
    Personalized Study Material
```

Faculty material acts as the primary academic reference.

Student notes are treated as evidence of what the student has documented.

The system then determines the coverage status of each relevant topic.

---

# 🧠 Knowledge Coverage Categories

## MISSING

A topic exists in the faculty material but there is little or no corresponding information in the student's notes.

Example:

```text
Faculty:
Q-Learning

Student Notes:
No Q-Learning content found

Result:
MISSING
```

---

## PARTIALLY COVERED

The student's notes contain some information about the topic, but important portions are absent.

Example:

```text
Faculty:
Value Iteration
├── Definition
├── Bellman Optimality Equation
├── Algorithm
└── Example

Student:
├── Definition
└── Basic concept

Result:
PARTIALLY COVERED
```

For a partial topic, generated notes should focus primarily on the missing portion rather than repeating everything already present.

---

## MASTERED

The student's notes contain sufficient information corresponding to the identified topic.

```text
Faculty:
Bellman Equation
├── Definition
├── Equation
└── Explanation

Student:
├── Definition
├── Equation
└── Explanation

Result:
MASTERED
```

`MASTERED` represents sufficient documented coverage in the student's notes. It is not intended to be a formal measurement of the student's actual knowledge or examination performance.

---

# 🧩 Main Features

## 1. Faculty Material Analysis

Faculty-provided material forms the primary reference for the system.

The material can contain:

- Course topics
- Definitions
- Mathematical equations
- Algorithms
- Procedures
- Examples
- Important concepts
- Supporting explanations

The system extracts relevant academic information before performing the comparison.

---

## 2. Student Note Analysis

The student can provide their existing study material.

Possible inputs include:

- Typed notes
- PDF notes
- Scanned notes
- Notebook photographs
- Handwritten notes
- Screenshots

The extracted information becomes the student-side evidence used during gap analysis.

---

## 3. Handwritten Note Understanding

Handwritten notes cannot always be processed like ordinary text documents.

The system therefore uses a vision-capable AI model to interpret image-based notes.

```text
Handwritten Image
       │
       ▼
Vision Model
       │
       ▼
Extracted Content
       │
       ▼
Academic Information
       │
       ▼
Topic Mapping
       │
       ▼
Gap Analysis
```

This allows handwritten notes to participate in the same knowledge-gap workflow as digital notes.

---

# 📄 Document Processing

Faculty material is processed before AI comparison.

A simplified document pipeline is:

```text
PDF / Academic Document
          │
          ▼
     Text Extraction
          │
          ▼
    Content Cleaning
          │
          ▼
   Academic Information
          │
          ▼
    Topic Identification
```

The extracted content is then supplied to the AI analysis stage.

---

# 👁️ Vision Processing Pipeline

For image-based student notes:

```text
Student Note Image
        │
        ▼
Image Input
        │
        ▼
Vision-Capable Model
        │
        ▼
Text / Concept Extraction
        │
        ▼
Student Knowledge Representation
        │
        ▼
Gap Analysis
```

This allows the system to handle information that exists only visually.

---

# 🔍 Knowledge Gap Analysis

After processing the faculty material and student notes, the system compares the two sources.

The conceptual input is:

```text
Faculty Topic
      +
Student Evidence
      +
Existing Coverage
      +
Missing Information
      ↓
Topic Classification
```

The output contains topic-level information.

Example:

```text
Machine Learning

Linear Regression       → MASTERED
Logistic Regression     → PARTIAL
Support Vector Machine  → MISSING
Decision Trees          → PARTIAL
Random Forest           → MASTERED
```

---

# 📊 Analysis Result Structure

A topic-level analysis can contain:

```text
Topic
Status
Why the topic is required
Existing student knowledge
Missing information
Relevant source information
```

Example:

```json
{
  "topic": "Kalman Filter Equations",
  "status": "missing",
  "why_needed": "Required concept identified in faculty material.",
  "student_knowledge": "",
  "missing_information": [
    "Prediction equation",
    "Measurement update equation",
    "Covariance update"
  ]
}
```

---

# 📚 AI-Generated Study Notes

The second major component of the application is targeted note generation.

Instead of asking an LLM:

```text
"Explain Machine Learning."
```

the application provides specific academic context:

```text
Faculty Material
      +
Student Notes
      +
Detected Topic
      +
Detected Gap
      ↓
AI Note Generation
```

This allows the generated material to focus on the actual learning gap.

---

# ✍️ Personalized Note Generation

The note-generation system handles the two main gap types differently.

## Missing Topic

For a missing topic:

```text
MISSING
   ↓
Relevant Faculty Content
   ↓
Generate Complete Study Notes
```

The generated notes cover the important information required for that topic.

---

## Partial Topic

For a partially covered topic:

```text
PARTIAL
   ↓
Identify Existing Coverage
   ↓
Identify Missing Information
   ↓
Generate Completion Notes
```

The goal is to minimize unnecessary repetition.

For example:

```text
Student already knows:
• Definition
• Basic concept

Missing:
• Formula
• Algorithm
• Example

Generated notes:
• Formula
• Algorithm
• Example
```

---

# 📝 Generated Note Format

The generated notes are designed to follow a structured academic format.

```text
Topic
│
├── Definition
│
├── Core Concept
│
├── Important Terms
│
├── Formula / Equation
│
├── Variable Definitions
│
├── Step-by-Step Procedure
│
├── Example
│
├── Important Points
│
└── Exam Points
```

This structure is intended to make the output easier to revise.

---

# 🧮 Mathematical Content

Mathematical subjects require more than plain-language explanations.

The note-generation pipeline is designed to preserve relevant mathematical content from the source material.

For example:

```text
x̂ₖ⁻ = Fₖx̂ₖ₋₁ + Bₖuₖ
```

can be presented together with variable definitions:

```text
x̂ₖ⁻  → predicted state
Fₖ    → state transition matrix
x̂ₖ₋₁ → previous state estimate
Bₖ    → control-input matrix
uₖ    → control input
```

Generated notes can therefore contain:

- Equations
- Variables
- Definitions
- Algorithms
- Derivations
- Procedures
- Worked examples

---

# 📖 Exam-Oriented Notes

The generated notes are structured around revision.

The intended sequence is:

```text
CONCEPT
    ↓
DEFINITION
    ↓
FORMULA
    ↓
VARIABLES
    ↓
PROCEDURE
    ↓
EXAMPLE
    ↓
IMPORTANT POINTS
    ↓
EXAM REVISION
```

This allows a student to move from understanding a concept to quickly reviewing it before an examination.

---

# 🏗️ System Architecture

```text
┌──────────────────────────────────────────────┐
│                  FRONTEND                    │
│                                              │
│              Next.js + React                 │
│                 TypeScript                   │
└──────────────────────┬───────────────────────┘
                       │
                       │ HTTP / REST
                       ▼
┌──────────────────────────────────────────────┐
│                  BACKEND                     │
│                                              │
│                  FastAPI                     │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ File Validation                        │  │
│  │ Document Processing                    │  │
│  │ Image Processing                       │  │
│  │ Topic Analysis                         │  │
│  │ Gap Detection                          │  │
│  │ Note Generation                        │  │
│  └────────────────────────────────────────┘  │
│                       │                      │
└───────────────────────┼──────────────────────┘
                        │
                        ▼
              ┌───────────────────┐
              │      Groq API     │
              │                   │
              │ Vision + Text LLM │
              └───────────────────┘
```

---

# 🔄 Complete Processing Pipeline

## Stage 1 — Upload

The user provides:

```text
Faculty Material
        +
Student Notes
        +
Handwritten Note Images
```

## Stage 2 — Frontend Request

The Next.js frontend packages the files and sends them to the backend.

```http
POST /analyze
```

## Stage 3 — Backend Validation

FastAPI receives the request and validates the uploaded content.

## Stage 4 — Faculty Content Extraction

The backend extracts usable academic information from the faculty material.

```text
Faculty PDF / Document
          ↓
Text Extraction
          ↓
Clean Content
```

## Stage 5 — Student Content Extraction

Digital student notes are processed as text.

Images are sent through the vision-processing pipeline.

```text
Digital Notes ──────────┐
                        │
                        ▼
                  Student Content
                        ▲
                        │
Handwritten Images ─────┘
```

## Stage 6 — Topic Identification

The AI identifies the topics represented in the faculty material.

## Stage 7 — Coverage Comparison

Each expected topic is compared against student evidence.

```text
Expected Topic
      │
      ▼
Student Evidence
      │
      ▼
Coverage Analysis
      │
      ▼
Status
```

## Stage 8 — Gap Classification

```text
                TOPIC
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
    MISSING    PARTIAL    MASTERED
```

## Stage 9 — User Selection

The user can select an identified gap.

```text
MISSING
[ GENERATE NOTES ]

PARTIAL
[ COMPLETE NOTES ]
```

## Stage 10 — Note Generation

The selected topic is sent to:

```http
POST /generate-notes
```

The backend combines:

```text
Faculty Context
+
Student Context
+
Detected Gap
```

and sends the relevant context to the text LLM.

## Stage 11 — Structured Output

The LLM produces structured study notes.

```text
Topic
 ↓
Definition
 ↓
Explanation
 ↓
Formula
 ↓
Procedure
 ↓
Example
 ↓
Exam Points
```

---

# 🔌 API Architecture

## `POST /analyze`

The primary analysis endpoint.

### Purpose

Processes uploaded faculty and student material and identifies topic-level knowledge gaps.

### Input

```text
Faculty files
Student files
Handwritten images
```

### Processing

```text
Upload
 ↓
Validation
 ↓
Extraction
 ↓
Vision Processing
 ↓
Topic Analysis
 ↓
Gap Analysis
```

### Output

```text
Topics
Statuses
Student Evidence
Missing Information
```

---

# 📖 `POST /generate-notes`

A separate endpoint for AI-generated study material.

### Purpose

Generate notes for a selected `MISSING` or `PARTIAL` topic.

### Input

```text
Topic
Faculty Context
Student Context
Detected Gap
```

### Output

```text
Structured Study Notes
```

The separation between `/analyze` and `/generate-notes` keeps the analysis workflow independent from note generation.

---

# 🤖 AI Architecture

The system uses AI for several different tasks.

| AI Stage | Purpose |
|:---|:---|
| Vision Model | Interpret handwritten/image-based notes |
| Text LLM | Analyze academic content |
| Text LLM | Compare faculty and student coverage |
| Text LLM | Identify missing information |
| Text LLM | Generate structured study notes |
| Local Gemma | Development and coding assistance |

The cloud inference pipeline uses Groq.

Ollama + Gemma are used locally during development.

---

# 🧠 Why Separate Vision and Text Processing?

Different input formats require different processing methods.

```text
                 INPUT
                   │
          ┌────────┴────────┐
          │                 │
      Documents           Images
          │                 │
          ▼                 ▼
   Text Extraction      Vision Model
          │                 │
          └────────┬────────┘
                   ▼
            Unified Content
                   │
                   ▼
               Text LLM
                   │
                   ▼
             Gap Analysis
```

This creates a unified representation before the actual comparison stage.

---

# 🛠️ Technology Stack

| Technology | Role |
|:---|:---|
| Next.js | Frontend framework |
| React | UI components |
| TypeScript | Type-safe frontend development |
| Python | Backend and AI processing |
| FastAPI | REST API backend |
| PyPDF2 | PDF text extraction |
| Groq | Cloud AI inference |
| Ollama | Local AI runtime |
| Gemma | Local development model |
| Git | Version control |
| GitHub | Source repository |
| Vercel | Frontend deployment |
| Render | Backend deployment |

---

# 💻 Development Environment

The project uses a local AI-assisted development workflow.

```text
Developer
    │
    ▼
Local PC
    │
    ├── Next.js
    ├── React
    ├── TypeScript
    └── FastAPI
            │
            ▼
        Ollama
            │
            ▼
          Gemma
```

The local Gemma model assists with:

- Code generation
- Debugging
- Refactoring
- Understanding project structure
- Implementing features
- API development
- Troubleshooting

It is not required for production inference.

Production inference is handled through Groq.

---

# 📂 Project Structure

```text
AI-Study-Gap-Analyzer/
│
├── frontend/
│   │
│   ├── app/
│   ├── components/
│   ├── public/
│   ├── styles/
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   │
│   ├── main.py
│   ├── requirements.txt
│   └── ...
│
├── README.md
├── .gitignore
└── .env
```

The exact structure can evolve as additional features are introduced.

---

# ⚙️ Local Installation

## Clone Repository

```bash
git clone <repository-url>
cd AI-Study-Gap-Analyzer
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Backend

Create a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run FastAPI:

```bash
uvicorn main:app --reload
```

---

# 🔐 Environment Variables

Example backend configuration:

```env
GROQ_API_KEY=your_groq_api_key

GROQ_VISION_MODEL=qwen/qwen3.8-27b
GROQ_TEXT_MODEL=openai/gpt-oss-120b
```

Sensitive credentials should never be committed to GitHub.

Recommended `.gitignore` entries:

```text
.env
.env.local
venv/
__pycache__/
node_modules/
.next/
```

---

# 🔀 Git Workflow

The development workflow follows:

```text
Local Development
       │
       ▼
Git
       │
       ▼
GitHub
       │
       ├───────────────┐
       ▼               ▼
    Vercel           Render
       │               │
   Frontend          Backend
```

A typical update cycle is:

```bash
git add .
git commit -m "Update study gap analysis"
git push
```

The connected deployment services can then build the updated application.

---

# ☁️ Deployment Architecture

The production architecture separates the frontend and backend.

```text
                         INTERNET
                            │
                            ▼
                  ┌─────────────────┐
                  │     Vercel      │
                  │                 │
                  │ Next.js         │
                  │ Frontend        │
                  └────────┬────────┘
                           │
                           │ REST API
                           ▼
                  ┌─────────────────┐
                  │     Render      │
                  │                 │
                  │ FastAPI Backend │
                  └────────┬────────┘
                           │
                           │ AI Request
                           ▼
                  ┌─────────────────┐
                  │      Groq       │
                  │                 │
                  │ AI Inference    │
                  └─────────────────┘
```

---

# 🚀 Production Request Flow

```text
User
 │
 ▼
Vercel
 │
 │ POST /analyze
 ▼
Render
 │
 ├── Validate files
 │
 ├── Extract documents
 │
 ├── Process images
 │
 ├── Identify topics
 │
 └── Analyze coverage
 │
 ▼
Groq
 │
 ▼
Structured Analysis
 │
 ▼
Render
 │
 ▼
Vercel
 │
 ▼
User
```

For note generation:

```text
User selects topic
        │
        ▼
POST /generate-notes
        │
        ▼
Render
        │
        ▼
Groq Text LLM
        │
        ▼
Structured Notes
        │
        ▼
Frontend
```

---

# 🔗 Complete Deployment Pipeline

```text
                    DEVELOPMENT
                         │
                         ▼
                 Local Computer
                         │
                    Ollama
                         │
                      Gemma
                         │
                         ▼
                    Git / GitHub
                         │
                 ┌───────┴───────┐
                 │               │
                 ▼               ▼
              Vercel           Render
                 │               │
              Frontend         Backend
                                 │
                                 ▼
                               Groq
                                 │
                                 ▼
                            AI Inference
```

---

# 📊 Data Flow

```text
┌──────────────────────┐
│ Faculty Material     │
│ PDF / Documents      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Content Extraction   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Expected Topics      │
└──────────┬───────────┘
           │
           │ Compare
           │
           ▼
┌──────────────────────┐
│ Student Notes        │
│ Text / Images        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Student Evidence     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Knowledge Gap        │
│ Analysis             │
└──────────┬───────────┘
           │
      ┌────┼────┐
      ▼    ▼    ▼
   MISSING PARTIAL MASTERED
      │    │
      └────┼────┘
           ▼
┌──────────────────────┐
│ Note Generation      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Personalized Notes   │
└──────────────────────┘
```

---

# 🔎 Source-Grounded Generation

Faculty material acts as the primary academic reference.

The generation process should avoid fabricating:

- Faculty-specific definitions
- Unsupported equations
- Fake examples
- Nonexistent slide numbers
- Fabricated page numbers
- Unsupported syllabus topics

Where source information is available, the generated notes should remain consistent with it.

This is particularly important for academic topics containing equations, algorithms, terminology, and course-specific explanations.

---

# 🧱 Design Principles

## Source First

Faculty material establishes the expected academic coverage.

## Gap Focused

The system focuses on missing or incomplete content.

## Structured Output

Generated notes follow predictable academic sections.

## User Controlled

Note generation is triggered by the student.

## Modular

Analysis and generation are separate backend operations.

## Lightweight

The initial system avoids unnecessary infrastructure.

## Extensible

The architecture can later support retrieval, progress tracking, quizzes, and personalization.

---

# 🔒 Privacy and Data Handling

The core workflow does not require a permanent database.

The basic process is:

```text
Upload
   ↓
Process
   ↓
Analyze
   ↓
Generate
   ↓
Return
```

A future version may introduce persistent storage, authentication, and student profiles if required.

The current architecture keeps the core application focused on processing and analysis.

---

# 🧪 Testing Workflow

A basic test can follow this sequence:

```text
1. Start frontend
        ↓
2. Start backend
        ↓
3. Upload faculty material
        ↓
4. Upload student notes
        ↓
5. Run analysis
        ↓
6. Inspect detected topics
        ↓
7. Verify MISSING / PARTIAL / MASTERED
        ↓
8. Select a gap
        ↓
9. Generate notes
        ↓
10. Verify generated content
```

---

# 📈 Example Use Case

Consider a Reinforcement Learning course.

Faculty material:

```text
Markov Decision Processes
Bellman Equation
Policy Evaluation
Policy Iteration
Value Iteration
Q-Learning
```

Student notes:

```text
✓ Markov Decision Processes
✓ Bellman Equation
✓ Policy Evaluation
✗ Policy Iteration
! Value Iteration
✗ Q-Learning
```

Analysis:

```text
Markov Decision Processes    → MASTERED
Bellman Equation             → MASTERED
Policy Evaluation            → MASTERED
Policy Iteration             → MISSING
Value Iteration              → PARTIAL
Q-Learning                   → MISSING
```

The student can then request:

```text
Policy Iteration
Value Iteration
Q-Learning
```

The system generates targeted notes instead of regenerating the entire subject.

---

# 📝 Example Generated Notes

Example structure:

```text
## Policy Iteration

### Definition

Policy Iteration is an iterative method used to find an
optimal policy in a Markov Decision Process.

### Main Steps

1. Initialize a policy.
2. Perform policy evaluation.
3. Improve the policy.
4. Repeat until the policy is stable.

### Policy Evaluation

Evaluate the value function for the current policy.

### Policy Improvement

Choose the action that provides the highest expected return.

### Important Points

• Policy evaluation estimates the value of the current policy.
• Policy improvement updates the policy.
• The process terminates when the policy becomes stable.

### Exam Points

• Know the two main stages.
• Understand the difference between evaluation and improvement.
• Be able to explain the iteration process.
```

---

# ⚠️ Current Limitations

The system's output depends on the quality and completeness of its input.

Potential limitations include:

- Poor-quality handwritten images
- Difficult handwriting
- Missing pages
- Incomplete faculty documents
- Ambiguous academic terminology
- Difficult mathematical notation
- Very large documents
- Context limitations
- AI interpretation errors

Generated material should therefore be checked against the original academic material.

---

# 🔮 Future Development

## 1. Retrieval-Augmented Generation

A future version could introduce a RAG architecture for larger document collections.

```text
Documents
    ↓
Document Chunking
    ↓
Embeddings
    ↓
Vector Store
    ↓
Relevant Context Retrieval
    ↓
LLM
    ↓
Grounded Study Notes
```

This could allow the system to retrieve only the relevant sections of a large course document when generating notes.

---

## 2. Student Progress Tracking

A future dashboard could maintain topic progress:

```text
Subject
│
├── Topic 1 ✓
├── Topic 2 ✓
├── Topic 3 !
├── Topic 4 ✗
└── Topic 5 ✓
```

---

## 3. Automated Quizzes

After generating notes, the system could generate:

- Multiple-choice questions
- Short-answer questions
- Numerical problems
- Conceptual questions
- Previous-exam-style questions

---

## 4. Flashcards

The generated notes could be transformed into:

```text
Question
   ↓
Answer
```

for rapid revision.

---

## 5. Personalized Revision

Future versions could generate:

- Topic revision plans
- Formula sheets
- Quick revision summaries
- Practice sets
- Topic-specific quizzes
- Exam preparation material

---

## 6. Improved Mathematical Understanding

Future improvements could focus on:

- Handwritten equations
- Mathematical symbols
- Diagrams
- Graphs
- Tables
- Algorithm flowcharts

---

## 7. Multi-Course Support

The application could eventually organize multiple subjects:

```text
Student
│
├── Machine Learning
├── Reinforcement Learning
├── Cloud Computing
├── Big Data Analytics
├── Fuzzy Logic
└── Computer Vision
```

---

# 📌 Project Status

## Current Implementation

- [x] Faculty material upload
- [x] Student notes upload
- [x] Document processing
- [x] Handwritten note processing
- [x] Vision-based content extraction
- [x] Topic identification
- [x] Knowledge-gap analysis
- [x] MISSING classification
- [x] PARTIAL classification
- [x] MASTERED classification
- [x] AI-generated study notes
- [x] Separate `/generate-notes` workflow
- [x] Local AI-assisted development
- [x] GitHub source control
- [x] Cloud deployment architecture

## Future Work

- [ ] Retrieval-Augmented Generation
- [ ] Persistent student progress
- [ ] Topic history
- [ ] Automated quizzes
- [ ] Flashcard generation
- [ ] Advanced mathematical OCR
- [ ] Multi-course dashboards
- [ ] Personalized revision scheduling

---

# 🧭 End-to-End System

The complete application can be summarized as:

```text
                     STUDENT
                        │
                        ▼
              Upload Learning Material
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
     Faculty Material         Student Notes
            │                       │
            ▼                       ▼
      Content Extraction      Content Extraction
            │                       │
            └───────────┬───────────┘
                        ▼
                 Topic Analysis
                        │
                        ▼
                Coverage Analysis
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
         MISSING      PARTIAL    MASTERED
            │           │
            └─────┬─────┘
                  ▼
          User Selects Topic
                  │
                  ▼
           Generate Notes
                  │
                  ▼
             Groq LLM
                  │
                  ▼
        Structured Study Notes
                  │
                  ▼
                STUDY
```

---

# 🌐 Project Vision

The long-term goal of the AI Study Gap Analyzer is to move beyond simply generating educational content.

The system focuses on the complete learning loop:

```text
UNDERSTAND
    ↓
COMPARE
    ↓
IDENTIFY
    ↓
FILL THE GAP
    ↓
STUDY
    ↓
REVISE
```

The core idea is simple:

> **Don't generate more notes blindly. First understand what the student is missing.**

---

# 👨‍💻 Development

This project combines several areas of software and AI engineering:

```text
Frontend Development
        +
Backend Development
        +
REST APIs
        +
Document Processing
        +
Computer Vision
        +
Large Language Models
        +
Prompt Engineering
        +
Cloud Deployment
        +
AI-Assisted Development
```

The application demonstrates how these technologies can be combined into a practical educational system.

---

# 🙏 Acknowledgements

This project makes use of:

- Next.js
- React
- TypeScript
- Python
- FastAPI
- PyPDF2
- Groq
- Ollama
- Gemma
- Git
- GitHub
- Vercel
- Render

---

# 📜 License

Add the project's selected license here.

For example:

```text
MIT License
```

if the repository is released under the MIT License.

---

# 🎓 AI Study Gap Analyzer

**From scattered notes to structured learning.**

**Understand what you have.**

**Identify what is missing.**

**Generate what you need.**

---
