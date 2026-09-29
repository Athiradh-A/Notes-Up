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
# OPENROUTER API KEY
# ---------------------------------------------------------
# Optional locally so the app can still run with Gemini + Groq.
# Render should have this key configured for the free-model fallbacks.

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# ---------------------------------------------------------
# GEMINI MODEL
# ---------------------------------------------------------

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
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
# OPENROUTER FREE MODELS
# ---------------------------------------------------------
# These are explicitly the :free variants so the fallback
# does not accidentally select the paid Qwen endpoint.

OPENROUTER_VISION_MODEL = os.getenv(
    "OPENROUTER_VISION_MODEL",
    "qwen/qwen3.8-27b:free",
)

OPENROUTER_VISION_FALLBACK_MODEL = os.getenv(
    "OPENROUTER_VISION_FALLBACK_MODEL",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
)

OPENROUTER_TEXT_MODEL = os.getenv(
    "OPENROUTER_TEXT_MODEL",
    "qwen/qwen3.8-27b:free",
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

print(
    f"OpenRouter Vision Model: {OPENROUTER_VISION_MODEL}"
)

print(
    f"OpenRouter Vision Fallback: {OPENROUTER_VISION_FALLBACK_MODEL}"
)

print(
    f"OpenRouter Text Model: {OPENROUTER_TEXT_MODEL}"
)

print(
    f"OpenRouter API Key Configured: {bool(OPENROUTER_API_KEY)}"
)
