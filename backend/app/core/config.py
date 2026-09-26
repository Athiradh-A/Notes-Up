import os

from dotenv import load_dotenv


# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# GEMINI API KEY
# ---------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set."
    )


# ---------------------------------------------------------
# GROQ API KEY
# ---------------------------------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set."
    )


# ---------------------------------------------------------
# GEMINI MODEL
# ---------------------------------------------------------

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash",
)


# ---------------------------------------------------------
# GROQ MODELS
# ---------------------------------------------------------

GROQ_VISION_MODEL = os.getenv(
    "GROQ_VISION_MODEL",
    "qwen/qwen3.8-27b",
)

GROQ_TEXT_MODEL = os.getenv(
    "GROQ_TEXT_MODEL",
    "openai/gpt-oss-120b",
)


# ---------------------------------------------------------
# STARTUP LOGGING
# ---------------------------------------------------------

print(
    f"Gemini Model: {GEMINI_MODEL}"
)

print(
    f"Groq Vision Model: {GROQ_VISION_MODEL}"
)

print(
    f"Groq Text Model: {GROQ_TEXT_MODEL}"
)
