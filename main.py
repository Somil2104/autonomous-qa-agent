from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Autonomous QA Agent Backend is running!"}
