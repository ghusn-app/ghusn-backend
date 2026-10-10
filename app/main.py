from fastapi import FastAPI
from app.api.v1.endpoints.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints.diagnoses import router as diagnoses_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.plants import router as plants_router
from app.api.v1.endpoints.farmers import router as farmers_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.expert import router as experts_router
from app.api.v1.endpoints.consultations import router as consultations_router
from app.api.v1.endpoints.payments import router as payments_router
from app.api.v1.endpoints.consultation_messages import router as consultation_messages_router






#from app.database import engine, Base
#from app.models import User, Farmer, Admin, DiseaseDictionary, Diagnosis, PasswordReset

# إنشاء الجداول المطابقة للمخطط في PostgreSQL
#Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ghusn API Backend")
origins = [
    "http://localhost:5173",
   "https://ghusn-frontend-production.up.railway.app",
    "https://ghusn-frontend-production-9543.up.railway.app",
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
app.include_router(users_router)
app.include_router(plants_router)
app.include_router(farmers_router)
app.include_router(admin_router)
app.include_router(experts_router)
app.include_router(consultations_router)
app.include_router(payments_router)
app.include_router(consultation_messages_router)



@app.get("/")
def read_root():
    return {"message": "Ghusn Database Models Initialized Perfectly!"}
