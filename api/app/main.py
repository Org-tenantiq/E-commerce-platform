from fastapi import FastAPI
from api.app.db import Base, create_db_engine
from api.app.routers import auth

app = FastAPI()

# Initialize database
engine = create_db_engine()
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
