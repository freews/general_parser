import sqlite3
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="SSD ENG Library")

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "library.db"

# ... (omitted)

# Mount static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Mount current directory (to serve section_images)
# Images are in ./section_images/
app.mount("/section_images", StaticFiles(directory="section_images"), name="section_images")



if __name__ == "__main__":
    print("Starting SSD ENG Library Server...")
    print("Go to http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
