from fastapi import FastAPI
from app.api.v1.endpoints.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints.diagnoses import router as diagnoses_router

#from app.database import engine, Base
#from app.models import User, Farmer, Admin, DiseaseDictionary, Diagnosis, PasswordReset

# إنشاء الجداول المطابقة للمخطط في PostgreSQL
#Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ghusn API Backend")
origins = [
    "http://localhost:5173",
    #"https://ghusn-frontend-production.up.railway.app"
    "https:// ghusn-frontend-production-9543.up.railway.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(diagnoses_router)

@app.get("/")
def read_root():
    return {"message": "Ghusn Database Models Initialized Perfectly!"}
