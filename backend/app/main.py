from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import analysis

# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Study Sanctuary API",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",

        # Vercel domain will be added here later.
        # Example:
        # "https://notes-up.vercel.app",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================================
# ROUTES
# =========================================================

app.include_router(
    analysis.router
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Study Sanctuary API is running"
    }