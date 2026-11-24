"""
One-Command Launcher for the Parametric Overhead Crane Drawing Generator.
Usage:
    python run.py
"""
import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 72)
    print(" MODERN CRANE CO. - PARAMETRIC OVERHEAD CRANE GENERATOR ")
    print("=" * 72)
    print(" Starting local server at: http://localhost:8000")
    print(" API Documentation:       http://localhost:8000/docs")
    print(" Database:                SQLite (crane_designs.db)")
    print(" Press Ctrl+C to stop.")
    print("=" * 72)

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
