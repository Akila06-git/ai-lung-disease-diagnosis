## Artificial Intelligence in Medical Imaging: A Smart Approach to Lung Disease Diagnosis

This project is an AI-assisted chest X-ray triage system that predicts 8 distinct lung diseases using a custom-built DenseNet121 Deep Learning model.


## screenshots


## Project Structure
- **Backend**: Django API, Celery (for async model inference), TensorFlow/Keras
- **Frontend**: React + Vite + TailwindCSS

---

## Prerequisites
Before you begin, ensure you have the following installed on your machine:
1. **Python 3.10+**
2. **Node.js (v18+)** and **npm**
3. **Redis Server** (Required for Celery task queuing)
   - *Windows users*: You can install [Memurai](https://www.memurai.com/) (a Windows-native Redis port) or run Redis via WSL (Windows Subsystem for Linux).

---

## Getting Started: Step-by-Step

### 1. Clone the Repository
Open your terminal or command prompt and run:
```bash
git clone https://github.com/SivaAbirami/lung-disease-detector.git
cd lung-disease-detector
```

### 2. Backend Setup & Environment
Navigate to the backend folder:

```bash
cd backend
```

**Create and activate a virtual environment:**
```bash
# On Windows:
python -m venv venv
.\venv\Scripts\activate



**Install requirements:**
```bash
pip install -r requirements.txt
```

**Configure Environment Variables:**
Create a `.env` file in the `backend/` directory.

#### Default Setup (Easiest)
Uses local SQLite and synchronous processing (No Redis/Postgres needed).
```env
create .env file and copy paste from the .env.example file
```


**Run Migrations & Create Admin:**
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 3. Start the Backend

You only need one terminal for the backend:
```bash
python manage.py runserver
```

### 4. Frontend Setup (React/Vite)
Open a **new terminal window** and navigate to the frontend folder:
```bash
cd frontend
```

**Install Node dependencies:**
```bash
npm install
```

**Start the Vite development server:**
```bash
npm run dev
```

---

## Accessing the Application

- **Web Application**: Open your browser and go to `http://localhost:5173/`
- **Django Admin Panel**: Open your browser and go to `http://localhost:8000/admin/` (Login with the superuser account you created).

### Usage Notes:
- Non-admin users can register normally via the web interface.
- Only users marked as `is_superuser` (like the one created via `createsuperuser`) will see the **Dashboard** link in the navigation bar to view full system analytics and retraining controls.
- Upload an X-Ray image (PNG/JPG) on the main page to test the AI prediction engine!
