import uvicorn

if __name__ == "__main__":
    print("==================================================")
    print("  BHILAI_TV // TERMINAL MOVIE EXPLORER")
    print("  Starting FastAPI server on http://127.0.0.1:8000")
    print("==================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
