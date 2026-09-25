import os
from dotenv import load_dotenv
from groq import Groq

# Path to .env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
print(f"DEBUG: Looking for .env at: {env_path}")

# 1. Try standard load_dotenv
load_dotenv(dotenv_path=env_path)

# 2. Manual fallback parsing with extreme debugging
if not os.getenv("GROQ_API_KEY"):
    if os.path.exists(env_path):
        print("DEBUG: load_dotenv failed. Attempting manual parse...")
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                print(f"DEBUG: Read {len(lines)} lines from .env")
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("'").strip('"')
                        print(f"DEBUG: Found key: {key}")
                        os.environ[key] = value
        except Exception as e:
            print(f"DEBUG: Manual parse error: {e}")
    else:
        print(f"DEBUG: .env file NOT FOUND at {env_path}")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "openai/gpt-oss-120b")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")

# Initialize client
client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq Client successfully initialized.")
    except Exception as e:
        print(f"❌ Groq Client Initialization Error: {e}")
else:
    print("❌ CRITICAL: GROQ_API_KEY not found in environment.")
