from fastapi import FastAPI
from app.api.v1.endpoints.auth import router as auth_router
#from app.database import engine, Base
#from app.models import User, Farmer, Admin, DiseaseDictionary, Diagnosis, PasswordReset

# إنشاء الجداول المطابقة للمخطط في PostgreSQL
#Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ghusn API Backend")
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Ghusn Database Models Initialized Perfectly!"}
