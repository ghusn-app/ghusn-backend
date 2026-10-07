#  Ghusn Backend

Ghusn is an agricultural platform that helps olive farmers detect olive leaf diseases using Artificial Intelligence and provides access to agricultural expert consultations.

This repository contains the Backend API for the Ghusn platform.


## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT Authentication
- Supabase Storage
- REST API
- AI Model Integration



##  Features

### Authentication
- User registration and login
- JWT access and refresh tokens
- Password reset
- Google authentication
- Role-based authorization

### AI Disease Diagnosis
- Upload olive leaf images
- Send images to the AI classification service
- Receive disease prediction and confidence score
- Validate prediction confidence
- Store successful diagnoses

### Plant Management
- Add and manage olive trees
- Link diagnoses to plants
- View diagnosis history

### Expert Consultations
- Request agricultural consultations
- Farmer–expert messaging
- Image attachments
- Consultation status management
- Question limits
- Notifications

### Payments
- Consultation payment management
- Payment status tracking


##  Diagnosis Workflow

Farmer uploads image
        ↓
Backend validates image
        ↓
AI model analyzes image
        ↓
Disease + confidence returned
        ↓
Backend retrieves disease information
        ↓
Diagnosis saved in PostgreSQL
        ↓
Result returned to farmer



##  Project Structure

app/
├── api/
│   └── v1/
│       └── endpoints/
├── models/
├── schemas/
├── services/
├── config.py
└── main.py

alembic/
requirements.txt



##  Installation

Clone the repository:

git clone <repository-url>

Create a virtual environment:

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Run database migrations:

alembic upgrade head

Start the server:

uvicorn app.main:app --reload

API documentation:

http://127.0.0.1:8000/docs


##  Team

Ghusn is a collaborative project developed by a team working across:

- Backend Development
- Frontend Development
- AI / Machine Learning
- Flutter
- UI/UX
- Markting



## Backend Contribution

The backend work includes:

- FastAPI REST API development
- PostgreSQL database integration
- Authentication and authorization
- AI model integration
- Diagnosis management
- Plant management
- Supabase image storage
- Expert consultation system
- Payment workflow
- Frontend API integration



##  Project Status

Under development.
