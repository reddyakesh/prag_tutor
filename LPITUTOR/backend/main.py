import os
import sys
import json
import time
import random
import glob
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Body, Form, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add root project directory to sys.path to access core backend modules
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

# Import existing working backend logic (DO NOT REWRITE)
import pragtutor_backend
from student_database import get_student

app = FastAPI(title="PragTutor API Adapter", version="2.0.0")

from fastapi.staticfiles import StaticFiles

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGES_DIR = os.path.join(ROOT_DIR, "images")
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

DATA_DIR = os.path.join(ROOT_DIR, "data")
SUBJECTS_FILE = os.path.join(DATA_DIR, "subjects.json")
MANIFEST_FILE = os.path.join(DATA_DIR, "pdf_manifest.json")
OTP_LOGS_FILE = os.path.join(DATA_DIR, "otp_logs.txt")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Admin Credentials
ADMIN_EMAIL = "vundhyalaakeshreddy@gmail.com"
ADMIN_PASSWORD = "reddy@123"

# PragTutor Dedicated Sender Account
PRAGTUTOR_SENDER_EMAIL = "pragtutor.ai@gmail.com"

# Persistent User Database
TEACHERS_DB: List[Dict[str, Any]] = []
STUDENTS_DB: List[Dict[str, Any]] = []
USERS_DB: Dict[str, Dict[str, Any]] = {}
PENDING_OTPS: Dict[str, Dict[str, Any]] = {}

SUBJECT_ID_MAP = {
    "os": "operating_systems",
    "operating_systems": "operating_systems",
    "cn": "computer_networks",
    "computer_networks": "computer_networks",
    "ds": "data_structures",
    "data_structures": "data_structures",
    "dbms": "dbms",
    "se": "software_engineering",
    "software_engineering": "software_engineering"
}

SUBJECT_NAMES = {
    "operating_systems": "Operating Systems",
    "computer_networks": "Computer Networks",
    "data_structures": "Data Structures",
    "dbms": "Database Management Systems",
    "software_engineering": "Software Engineering"
}

def normalize_subject_id(sub: str) -> str:
    if not sub:
        return ""
    s = sub.lower().strip()
    return SUBJECT_ID_MAP.get(s, s)

def load_users():
    global USERS_DB, TEACHERS_DB, STUDENTS_DB
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                USERS_DB = data.get("users", {})
                TEACHERS_DB = data.get("teachers", [])
                STUDENTS_DB = data.get("students", [])
                return
        except Exception as e:
            print(f"Error loading users.json: {e}")
    save_users()

def save_users():
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "users": USERS_DB,
                "teachers": TEACHERS_DB,
                "students": STUDENTS_DB
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving users.json: {e}")

load_users()

ACTIVITY_LOGS: List[Dict[str, Any]] = [
    {"id": 1, "timestamp": time.strftime("%Y-%m-%d %H:%M"), "user": "System Admin", "role": "ADMIN", "action": "PragTutor platform initialized cleanly."}
]

BUILD_STATUSES: Dict[str, Dict[str, Any]] = {}

def load_subjects():
    if os.path.exists(SUBJECTS_FILE):
        try:
            with open(SUBJECTS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and "subjects" in data:
                    return data["subjects"]
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def load_pdf_manifest():
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_pdf_manifest(manifest):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)

def scan_uploaded_pdfs():
    """Scans data/ directory and manifest for uploaded PDF course materials."""
    pdf_files = []
    manifest = load_pdf_manifest()

    if os.path.exists(DATA_DIR):
        files = glob.glob(os.path.join(DATA_DIR, "*.pdf"))
        for filepath in sorted(files):
            filename = os.path.basename(filepath)
            size_bytes = os.path.getsize(filepath)
            size_mb = round(size_bytes / (1024 * 1024), 2)
            mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(filepath)))
            
            subject_id = "operating_systems"
            found_in_manifest = False
            for sub_key, flist in manifest.items():
                if any(p.get("filename") == filename for p in flist):
                    subject_id = sub_key
                    found_in_manifest = True
                    break
            
            if not found_in_manifest:
                fn_lower = filename.lower()
                if "net" in fn_lower:
                    subject_id = "computer_networks"
                elif "data" in fn_lower or "ds" in fn_lower:
                    subject_id = "data_structures"
                elif "db" in fn_lower:
                    subject_id = "dbms"
                elif "soft" in fn_lower or "se" in fn_lower:
                    subject_id = "software_engineering"

            pdf_files.append({
                "filename": filename,
                "size_mb": size_mb,
                "size_bytes": size_bytes,
                "mtime": mtime,
                "subject_id": subject_id
            })
    return pdf_files

def get_knowledge_base_monitors():
    subjects = load_subjects()
    kb_monitors = []
    
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.path.join(ROOT_DIR, "chroma_db"))
    except Exception:
        client = None

    uploaded_pdfs = scan_uploaded_pdfs()

    for sub in subjects:
        sub_id = sub.get("id")
        sub_name = sub.get("name")
        col_name = f"{sub_id}_knowledge_base"
        vector_count = 0
        
        if client:
            try:
                col = client.get_collection(col_name)
                vector_count = col.count()
            except Exception:
                if sub_id == "operating_systems":
                    try:
                        col = client.get_collection("os_knowledge_base")
                        vector_count = col.count()
                    except Exception:
                        vector_count = 0
                else:
                    vector_count = 0

        pdf_count = len([p for p in uploaded_pdfs if p["subject_id"] == sub_id])
        
        b_info = BUILD_STATUSES.get(sub_id, {})
        status = b_info.get("status")
        if not status:
            status = "ready" if vector_count > 0 else "not_created"
        
        stage = b_info.get("stage")
        if not stage:
            stage = "ChromaDB Collection Indexed & Ready" if vector_count > 0 else "No Knowledge Base Created"

        kb_monitors.append({
            "subject_id": sub_id,
            "subject_name": sub_name,
            "collection_name": col_name,
            "pdf_count": pdf_count,
            "vector_chunks": vector_count,
            "status": status,
            "stage": stage
        })
    return kb_monitors

def send_otp_email(to_email: str, otp_code: str):
    """Dispatches verification OTP email from pragtutor.ai@gmail.com and records entry in data/otp_logs.txt."""
    log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] From: {PRAGTUTOR_SENDER_EMAIL} | To: {to_email} | OTP Code: {otp_code}\n"
    print("=" * 65)
    print(f"📧 [PRAGTUTOR EMAIL SENDER] From: {PRAGTUTOR_SENDER_EMAIL} -> To: {to_email}")
    print(f"🔐 Verification OTP Code: {otp_code}")
    print("=" * 65)

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(OTP_LOGS_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"OTP Log Error: {e}")

    # SMTP transmission attempt if environment SMTP credentials configured
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SMTP_EMAIL", PRAGTUTOR_SENDER_EMAIL)
    sender_password = os.environ.get("SMTP_PASSWORD", "")
    if sender_password:
        try:
            msg = MIMEText(f"Hello!\n\nYour PragTutor verification OTP code is: {otp_code}\n\nPlease enter this code to complete your signup.\n\nRegards,\nPragTutor Team")
            msg['Subject'] = "PragTutor Account Signup Verification OTP"
            msg['From'] = f"PragTutor AI <{sender_email}>"
            msg['To'] = to_email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [to_email], msg.as_string())
        except Exception as e:
            print(f"SMTP Transmission Note: {e}")

# ------------------------------------------------------------------
# Request Schemas
# ------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str
    portal: Optional[str] = "student"
    role: Optional[str] = "student"

class OTPRequest(BaseModel):
    email: str
    name: str
    role: str = "student"
    department: Optional[str] = None
    subjects: Optional[List[str]] = []

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str
    password: str

class QueryRequest(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None
    images: Optional[List[str]] = None
    student_id: str = "STU001"
    subject: str = "operating_systems"
    level: Optional[str] = "beginner"

class TeacherAccessUpdate(BaseModel):
    access_granted: bool

class TeacherStatusUpdate(BaseModel):
    status: str

class TeacherSubjectsUpdate(BaseModel):
    subjects: List[str]

# ------------------------------------------------------------------
# Health Check Endpoint
# ------------------------------------------------------------------
@app.get("/")
@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "PragTutor FastAPI Adapter",
        "version": "2.0.0",
        "admin_email": ADMIN_EMAIL,
        "sender_email": PRAGTUTOR_SENDER_EMAIL,
        "backend_engine": "pragtutor_backend.py (Active)",
        "capabilities": ["topic_identification", "prerequisite_engine", "chromadb_rag", "llm_tutor"]
    }

# ------------------------------------------------------------------
# Authentication & OTP Signup Routes
# ------------------------------------------------------------------
@app.post("/api/auth/request-otp")
def request_otp(req: OTPRequest):
    email = req.email.lower().strip()
    if email == ADMIN_EMAIL.lower():
        raise HTTPException(status_code=400, detail="Admin account is pre-configured. Please log in through Admin portal.")
    
    if email in USERS_DB:
        raise HTTPException(status_code=400, detail="An account with this email already exists. Please log in.")

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    norm_subs = [normalize_subject_id(s) for s in (req.subjects or [])]
    PENDING_OTPS[email] = {
        "otp": otp,
        "name": req.name,
        "role": req.role.lower(),
        "department": req.department or ("Computer Science & Engineering" if req.role.lower() == "teacher" else None),
        "subjects": norm_subs,
        "timestamp": time.time()
    }

    # Dispatch OTP via email service
    send_otp_email(email, otp)

    ACTIVITY_LOGS.insert(0, {
        "id": len(ACTIVITY_LOGS) + 1,
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "user": req.name,
        "role": req.role.upper(),
        "action": f"Requested signup OTP code sent from {PRAGTUTOR_SENDER_EMAIL} to {email}"
    })

    return {
        "status": "success",
        "message": f"Verification OTP code sent from {PRAGTUTOR_SENDER_EMAIL} to {email}.",
        "sender_email": PRAGTUTOR_SENDER_EMAIL,
        "otp_debug": otp
    }

@app.post("/api/auth/verify-otp-register")
def verify_otp_register(req: OTPVerifyRequest):
    email = req.email.lower().strip()
    if email not in PENDING_OTPS:
        raise HTTPException(status_code=400, detail="No pending signup request found for this email.")
    
    pending = PENDING_OTPS[email]
    if pending["otp"] != req.otp.strip():
        raise HTTPException(status_code=400, detail="Invalid OTP verification code. Please check your email and try again.")
    
    role = pending["role"]
    name = pending["name"]
    dept = pending["department"]
    user_id = f"{'TCH' if role == 'teacher' else 'STU'}{len(USERS_DB) + 1:03d}"

    raw_subs = pending.get("subjects", [])
    if role == "teacher" and not raw_subs:
        raw_subs = ["operating_systems"]
    assigned_subs = [normalize_subject_id(s) for s in raw_subs]

    user_obj = {
        "id": user_id,
        "name": name,
        "email": email,
        "password": req.password,
        "role": role,
        "department": dept,
        "subjects": assigned_subs,
        "assigned_subjects": assigned_subs,
        "access_granted": True,
        "status": "active",
        "joined_date": time.strftime("%Y-%m-%d")
    }

    USERS_DB[email] = user_obj

    if role == "teacher":
        TEACHERS_DB.append(user_obj)
    else:
        STUDENTS_DB.append(user_obj)

    save_users()
    del PENDING_OTPS[email]

    ACTIVITY_LOGS.insert(0, {
        "id": len(ACTIVITY_LOGS) + 1,
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "user": name,
        "role": role.upper(),
        "action": f"Verified OTP and registered new {role} account ({email}) with subjects {assigned_subs}"
    })

    return {
        "status": "success",
        "message": "Account created successfully! You can now log in.",
        "token": f"token-{user_id}",
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "role": role,
            "subjects": assigned_subs,
            "assigned_subjects": assigned_subs,
            "access_granted": True
        }
    }

@app.post("/api/auth/login")
def login(req: LoginRequest):
    email = req.email.lower().strip()
    password = req.password
    portal = (req.portal or req.role or "student").lower()

    if portal == "admin":
        if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
            all_subs = ["operating_systems", "computer_networks", "data_structures", "dbms", "software_engineering"]
            return {
                "status": "success",
                "token": "token-ADM001",
                "user": {
                    "id": "ADM001",
                    "name": "Vundhyala Akesh Reddy",
                    "email": ADMIN_EMAIL,
                    "role": "admin",
                    "subjects": all_subs,
                    "assigned_subjects": all_subs,
                    "access_granted": True
                }
            }
        raise HTTPException(status_code=401, detail="Invalid Admin email or password. Please check your credentials.")

    if portal == "teacher":
        if email in USERS_DB:
            user = USERS_DB[email]
            if user["role"] == "teacher" and user["password"] == password:
                subs = user.get("subjects", user.get("assigned_subjects", []))
                return {
                    "status": "success",
                    "token": f"token-{user['id']}",
                    "user": {
                        "id": user["id"],
                        "name": user["name"],
                        "email": user["email"],
                        "role": "teacher",
                        "subjects": subs,
                        "assigned_subjects": subs,
                        "access_granted": user.get("access_granted", True)
                    }
                }
        raise HTTPException(status_code=401, detail="Invalid Teacher email or password. Please sign up or check your credentials.")

    if portal == "student":
        if email in USERS_DB:
            user = USERS_DB[email]
            if user["role"] == "student" and user["password"] == password:
                return {
                    "status": "success",
                    "token": f"token-{user['id']}",
                    "user": {
                        "id": user["id"],
                        "name": user["name"],
                        "email": user["email"],
                        "role": "student",
                        "access_granted": user.get("access_granted", True)
                    }
                }
        raise HTTPException(status_code=401, detail="Invalid Student email or password. Please sign up or check your credentials.")

    raise HTTPException(status_code=401, detail="Invalid login portal or credentials.")

@app.get("/api/auth/me")
def get_me(role: str = "student"):
    return {
        "id": "ADM001" if role == "admin" else "STU001",
        "name": "Vundhyala Akesh Reddy" if role == "admin" else "Alex Mercer",
        "role": role,
        "email": ADMIN_EMAIL if role == "admin" else f"{role}@pragtutor.edu"
    }

# ------------------------------------------------------------------
# Admin Routes (100% Real Backend Metrics & Dynamic Controls)
# ------------------------------------------------------------------
@app.get("/api/admin/dashboard")
def get_admin_dashboard():
    subjects = load_subjects()
    uploaded_pdfs = scan_uploaded_pdfs()
    kb_monitors = get_knowledge_base_monitors()

    registered_students = len(STUDENTS_DB)
    registered_teachers = len(TEACHERS_DB)
    active_teachers = sum(1 for t in TEACHERS_DB if t.get("status") == "active")
    inactive_teachers = sum(1 for t in TEACHERS_DB if t.get("status") == "inactive")
    access_granted_teachers = sum(1 for t in TEACHERS_DB if t.get("access_granted"))

    return {
        "metrics": {
            "registered_students": registered_students,
            "registered_teachers": registered_teachers,
            "active_teachers": active_teachers,
            "inactive_teachers": inactive_teachers,
            "access_granted_teachers": access_granted_teachers,
            "total_uploaded_pdfs": len(uploaded_pdfs),
            "active_knowledge_bases": len(subjects),
            "system_health": "100% Operational"
        },
        "subjects": subjects,
        "teachers": TEACHERS_DB,
        "uploaded_pdfs": uploaded_pdfs,
        "knowledge_bases": kb_monitors,
        "recent_activity": ACTIVITY_LOGS[:10]
    }

@app.get("/api/admin/teachers")
def get_admin_teachers():
    return {"teachers": TEACHERS_DB}

@app.patch("/api/admin/teachers/{teacher_id}/access")
def toggle_teacher_access(teacher_id: str, update: TeacherAccessUpdate):
    for t in TEACHERS_DB:
        if t["id"] == teacher_id:
            t["access_granted"] = update.access_granted
            if t["email"] in USERS_DB:
                USERS_DB[t["email"]]["access_granted"] = update.access_granted
            action = "granted access to" if update.access_granted else "revoked access from"
            ACTIVITY_LOGS.insert(0, {
                "id": len(ACTIVITY_LOGS) + 1,
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                "user": "Admin Vundhyala Akesh Reddy",
                "role": "ADMIN",
                "action": f"Admin {action} teacher {t['name']}"
            })
            return {"status": "success", "teacher": t}
    raise HTTPException(status_code=404, detail="Teacher not found")

@app.patch("/api/admin/teachers/{teacher_id}/status")
def toggle_teacher_status(teacher_id: str, update: TeacherStatusUpdate):
    for t in TEACHERS_DB:
        if t["id"] == teacher_id:
            t["status"] = update.status
            if t["email"] in USERS_DB:
                USERS_DB[t["email"]]["status"] = update.status
            ACTIVITY_LOGS.insert(0, {
                "id": len(ACTIVITY_LOGS) + 1,
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                "user": "Admin Vundhyala Akesh Reddy",
                "role": "ADMIN",
                "action": f"Admin set account status of teacher {t['name']} to {update.status.upper()}"
            })
            return {"status": "success", "teacher": t}
    raise HTTPException(status_code=404, detail="Teacher not found")

@app.patch("/api/admin/teachers/{teacher_id}/subjects")
def update_teacher_subjects(teacher_id: str, update: TeacherSubjectsUpdate):
    for t in TEACHERS_DB:
        if t["id"] == teacher_id:
            norm_subs = [normalize_subject_id(s) for s in update.subjects]
            t["subjects"] = norm_subs
            t["assigned_subjects"] = norm_subs
            if t["email"] in USERS_DB:
                USERS_DB[t["email"]]["subjects"] = norm_subs
                USERS_DB[t["email"]]["assigned_subjects"] = norm_subs
            save_users()
            ACTIVITY_LOGS.insert(0, {
                "id": len(ACTIVITY_LOGS) + 1,
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                "user": "Admin Vundhyala Akesh Reddy",
                "role": "ADMIN",
                "action": f"Admin updated subject access for teacher {t['name']} to {norm_subs}"
            })
            return {"status": "success", "teacher": t}
    raise HTTPException(status_code=404, detail="Teacher not found")

@app.delete("/api/admin/clear_all")
@app.post("/api/admin/clear_all")
def clear_all_knowledge_bases_and_pdfs():
    all_subs = ["operating_systems", "computer_networks", "data_structures", "dbms", "software_engineering"]
    results = {}
    for sub in all_subs:
        results[sub] = clear_subject_knowledge_base_and_pdfs(sub)
    return {
        "status": "success",
        "message": "Successfully cleared all Knowledge Bases, vector collections, and PDF materials across all subjects.",
        "results": results
    }

@app.delete("/api/admin/subjects/{subject_id}/clear")
@app.post("/api/admin/subjects/{subject_id}/clear")
def clear_subject_knowledge_base_and_pdfs(subject_id: str):
    norm_sub = normalize_subject_id(subject_id)
    sub_name = SUBJECT_NAMES.get(norm_sub, subject_id)

    # 1. Clear files from pdf_manifest.json and disk
    manifest = load_pdf_manifest()
    deleted_files = []

    for sid in [norm_sub, subject_id]:
        if sid in manifest:
            for item in manifest[sid]:
                filename = item.get("filename")
                if filename:
                    for folder in [DATA_DIR, os.path.join(ROOT_DIR, "uploads"), os.path.join(ROOT_DIR, "data")]:
                        filepath = os.path.join(folder, filename)
                        if os.path.exists(filepath):
                            try:
                                os.remove(filepath)
                                if filename not in deleted_files:
                                    deleted_files.append(filename)
                            except Exception as e:
                                print(f"Error removing {filename}: {e}")
            del manifest[sid]
    save_pdf_manifest(manifest)

    # Delete any subject-specific JSON prerequisite or topic files
    for folder in [DATA_DIR, os.path.join(ROOT_DIR, "data")]:
        for fname in [f"prerequisites_{norm_sub}.json", f"course_topics_{norm_sub}.json"]:
            fpath = os.path.join(folder, fname)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception as e:
                    print(f"Error removing {fpath}: {e}")

    # Also check any orphan files associated with this subject
    all_files = scan_uploaded_pdfs()
    for fitem in all_files:
        if fitem.get("subject_id") == norm_sub or fitem.get("subject_id") == subject_id:
            filename = fitem.get("filename")
            for folder in [DATA_DIR, os.path.join(ROOT_DIR, "uploads"), os.path.join(ROOT_DIR, "data")]:
                filepath = os.path.join(folder, filename)
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        if filename not in deleted_files:
                            deleted_files.append(filename)
                    except Exception as e:
                        print(f"Error removing orphan file {filename}: {e}")

    # 2. Reset/Delete ChromaDB Collection
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.path.join(ROOT_DIR, "chroma_db"))
        col_names = [f"{norm_sub}_knowledge_base", f"{subject_id}_knowledge_base"]
        if norm_sub == "operating_systems":
            col_names.append("os_knowledge_base")
            
        for cname in set(col_names):
            try:
                client.delete_collection(cname)
            except Exception:
                pass
    except Exception as e:
        print(f"ChromaDB deletion note: {e}")

    # 3. Update kb_status.json on disk to reset status
    kb_data = load_kb_status()
    reset_meta = {
        "subject_id": norm_sub,
        "subject_name": sub_name,
        "status": "not_available",
        "kb_status": "NOT_AVAILABLE",
        "pdf_uploaded": False,
        "prerequisites_available": False,
        "vector_chunks": 0,
        "pdf_count": 0,
        "kb_version": "1.0",
        "last_prepared": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    kb_data[norm_sub] = reset_meta
    if subject_id in kb_data:
        kb_data[subject_id] = reset_meta
    save_kb_status(kb_data)

    # 4. Reset build status & topic caches
    if norm_sub in BUILD_STATUSES:
        del BUILD_STATUSES[norm_sub]
    if subject_id in BUILD_STATUSES:
        del BUILD_STATUSES[subject_id]

    try:
        import topic_identifier
        topic_identifier.TOPIC_CACHE.pop(norm_sub, None)
        topic_identifier.TOPIC_CACHE.pop(subject_id, None)
    except Exception:
        pass

    # 5. Record Activity Log
    ACTIVITY_LOGS.insert(0, {
        "id": len(ACTIVITY_LOGS) + 1,
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "user": "System Admin",
        "role": "ADMIN",
        "action": f"Admin cleared Knowledge Base vectors & deleted uploaded PDFs for {sub_name}"
    })

    return {
        "status": "success",
        "message": f"Successfully cleared Knowledge Base vectors and deleted PDF materials for {sub_name}.",
        "deleted_files_count": len(deleted_files),
        "deleted_filenames": deleted_files,
        "subject_id": norm_sub
    }

@app.get("/api/admin/activity")
def get_activity_stream():
    return {"activity": ACTIVITY_LOGS}

import threading

def check_teacher_authorization(subject_id: str, authorization: Optional[str] = Header(None)):
    norm_req = normalize_subject_id(subject_id)
    sub_display_name = SUBJECT_NAMES.get(norm_req, subject_id)

    if not authorization:
        return None

    token = authorization.replace("Bearer ", "").strip() if authorization.startswith("Bearer ") else authorization.strip()
    if token == "token-ADM001":
        return None  # Admin access

    found_user = None
    for email, user in USERS_DB.items():
        if f"token-{user.get('id')}" == token or user.get("id") == token or email == token:
            found_user = user
            break

    if found_user and found_user.get("role") == "teacher":
        assigned_subs = found_user.get("subjects") or found_user.get("assigned_subjects") or []
        norm_assigned = [normalize_subject_id(s) for s in assigned_subs]
        if norm_req not in norm_assigned:
            raise HTTPException(
                status_code=403,
                detail=f"Teacher does not have access to {sub_display_name}."
            )
    return found_user

# ------------------------------------------------------------------
# Teacher Routes
# ------------------------------------------------------------------
@app.get("/api/teacher/subjects")
def get_teacher_subjects(authorization: Optional[str] = Header(None)):
    subjects = load_subjects()
    monitors = {m["subject_id"]: m for m in get_knowledge_base_monitors()}

    user = None
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        for email, u in USERS_DB.items():
            if f"token-{u.get('id')}" == token or u.get("id") == token or email == token:
                user = u
                break

    allowed_subs = None
    if user and user.get("role") == "teacher":
        allowed_subs = set(normalize_subject_id(s) for s in (user.get("subjects") or user.get("assigned_subjects") or []))

    enriched = []
    for sub in subjects:
        sub_id = sub.get("id")
        norm_id = normalize_subject_id(sub_id)
        if allowed_subs is not None and norm_id not in allowed_subs:
            continue  # Do NOT include non-assigned subjects for this teacher!

        m = monitors.get(sub_id, {})
        enriched.append({
            **sub,
            "doc_count": m.get("pdf_count", 0),
            "total_chunks": m.get("vector_chunks", 0),
            "status": m.get("status", "not_created"),
            "stage": m.get("stage", "No Knowledge Base Created")
        })
    return {"subjects": enriched}

@app.post("/api/teacher/subjects/{subject_id}/upload")
async def upload_subject_pdf(
    subject_id: str,
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    authorization: Optional[str] = Header(None)
):
    check_teacher_authorization(subject_id, authorization)

    upload_list = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)
    
    if not upload_list:
        raise HTTPException(status_code=400, detail="No PDF files uploaded.")

    manifest = load_pdf_manifest()
    if subject_id not in manifest:
        manifest[subject_id] = []

    uploaded_items = []
    for fitem in upload_list:
        filename = fitem.filename
        content = await fitem.read()
        save_path = os.path.join(DATA_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(content)
        
        meta = {
            "filename": filename,
            "size_bytes": len(content),
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M")
        }
        manifest[subject_id] = [p for p in manifest[subject_id] if p.get("filename") != filename]
        manifest[subject_id].append(meta)
        uploaded_items.append(filename)

        ACTIVITY_LOGS.insert(0, {
            "id": len(ACTIVITY_LOGS) + 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "user": "Teacher",
            "role": "TEACHER",
            "action": f"Uploaded PDF {filename} for subject {subject_id}"
        })

    save_pdf_manifest(manifest)

    return {
        "status": "success",
        "message": f"Successfully uploaded {len(uploaded_items)} file(s)",
        "filenames": uploaded_items,
        "subject_id": subject_id
    }

@app.post("/api/teacher/subjects/{subject_id}/prerequisites")
async def upload_subject_prerequisites(
    subject_id: str,
    file: Optional[UploadFile] = File(None),
    body: Optional[Dict[str, Any]] = Body(None),
    authorization: Optional[str] = Header(None)
):
    check_teacher_authorization(subject_id, authorization)
    norm_sub = normalize_subject_id(subject_id)
    prereq_data = None

    if file:
        content = await file.read()
        try:
            prereq_data = json.loads(content.decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}")
    elif body:
        prereq_data = body

    if not prereq_data or not isinstance(prereq_data, dict):
        raise HTTPException(status_code=400, detail="Invalid prerequisite configuration format. Must be a JSON object mapping topics to prerequisites.")

    save_path = os.path.join(DATA_DIR, f"prerequisites_{norm_sub}.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(prereq_data, f, indent=2)

    # Sync into global prerequisites.json for seamless engine lookup
    try:
        global_path = os.path.join(ROOT_DIR, "prerequisites.json")
        if os.path.exists(global_path):
            with open(global_path, "r", encoding="utf-8") as f:
                glob_data = json.load(f)
            if "topics" in glob_data:
                for top, prereqs in prereq_data.items():
                    if isinstance(prereqs, list):
                        glob_data["topics"][top] = {
                            "unit": 1,
                            "prerequisites": prereqs,
                            "next_topics": []
                        }
                with open(global_path, "w", encoding="utf-8") as f:
                    json.dump(glob_data, f, indent=2)
    except Exception as e:
        print(f"Error syncing global prerequisites: {e}")

    sub_display = SUBJECT_NAMES.get(norm_sub, subject_id)
    ACTIVITY_LOGS.insert(0, {
        "id": len(ACTIVITY_LOGS) + 1,
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "user": "Teacher",
        "role": "TEACHER",
        "action": f"Uploaded prerequisite configuration for {sub_display}"
    })

    return {
        "status": "success",
        "message": f"Successfully updated prerequisite configuration for {sub_display}.",
        "subject_id": subject_id,
        "prerequisites": prereq_data
    }

KB_STATUS_FILE = os.path.join(DATA_DIR, "kb_status.json")

def load_kb_status():
    if os.path.exists(KB_STATUS_FILE):
        try:
            with open(KB_STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_kb_status(status_dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(KB_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_dict, f, indent=2)
    except Exception as e:
        print(f"Error saving kb_status.json: {e}")

def update_subject_kb_metadata(subject_id: str, status: str = "ready", vector_chunks: int = 0):
    norm_sub = normalize_subject_id(subject_id)
    kb_data = load_kb_status()
    manifest = load_pdf_manifest()

    pdf_count = len(manifest.get(norm_sub, []))
    has_pdfs = pdf_count > 0 or len([p for p in scan_uploaded_pdfs() if p["subject_id"] == norm_sub]) > 0
    has_prereqs = os.path.exists(os.path.join(DATA_DIR, f"prerequisites_{norm_sub}.json")) or os.path.exists(os.path.join(ROOT_DIR, "prerequisites.json"))

    kb_data[norm_sub] = {
        "subject_id": norm_sub,
        "subject_name": SUBJECT_NAMES.get(norm_sub, subject_id),
        "status": status,
        "kb_status": status.upper(),
        "pdf_uploaded": has_pdfs,
        "prerequisites_available": has_prereqs,
        "vector_chunks": vector_chunks,
        "pdf_count": pdf_count,
        "kb_version": "1.0",
        "last_prepared": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_kb_status(kb_data)

def _bg_build_kb(subject_id: str):
    norm_sub = normalize_subject_id(subject_id)
    def update_cb(stage: str, progress_pct: int):
        BUILD_STATUSES[norm_sub] = {
            "status": "building" if progress_pct < 100 else "ready",
            "stage": stage,
            "progress_pct": progress_pct,
            "timestamp": time.time()
        }

    try:
        # Clear previous ChromaDB collection to prevent mixing old and new chunks
        try:
            import chromadb
            client = chromadb.PersistentClient(path=os.path.join(ROOT_DIR, "chroma_db"))
            col_names = [f"{norm_sub}_knowledge_base", f"{subject_id}_knowledge_base"]
            if norm_sub in ["operating_systems", "os"]:
                col_names.append("os_knowledge_base")
            for cname in set(col_names):
                try:
                    client.delete_collection(cname)
                except Exception:
                    pass
        except Exception as e_col:
            print(f"Collection reset note: {e_col}")

        from build_knowledge_base import prepare_knowledge_base as build_kb
        res = build_kb(norm_sub, status_callback=update_cb)
        
        # Persist KB metadata
        update_subject_kb_metadata(norm_sub, status="ready", vector_chunks=res.get('vector_chunks', 0))

        BUILD_STATUSES[norm_sub] = {
            "status": "ready",
            "stage": f"ChromaDB Collection Indexed ({res.get('vector_chunks', 0)} chunks)",
            "progress_pct": 100,
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"Error building KB for {subject_id}: {e}")
        update_subject_kb_metadata(norm_sub, status="error", vector_chunks=0)
        BUILD_STATUSES[norm_sub] = {
            "status": "error",
            "stage": f"Build Error: {str(e)}",
            "progress_pct": 0,
            "timestamp": time.time()
        }

@app.post("/api/teacher/subjects/{subject_id}/prepare")
def prepare_knowledge_base(subject_id: str, authorization: Optional[str] = Header(None)):
    check_teacher_authorization(subject_id, authorization)
    norm_sub = normalize_subject_id(subject_id)
    BUILD_STATUSES[norm_sub] = {
        "status": "building",
        "stage": "Initializing background knowledge base builder...",
        "progress_pct": 5,
        "timestamp": time.time()
    }

    t = threading.Thread(target=_bg_build_kb, args=(norm_sub,), daemon=True)
    t.start()

    return {
        "status": "building",
        "message": f"Knowledge base preparation started for {norm_sub}",
        "build": BUILD_STATUSES[norm_sub]
    }

@app.get("/api/teacher/subjects/{subject_id}/status")
def get_build_status(subject_id: str):
    norm_sub = normalize_subject_id(subject_id)
    if norm_sub in BUILD_STATUSES:
        return BUILD_STATUSES[norm_sub]

    monitors = {m["subject_id"]: m for m in get_knowledge_base_monitors()}
    m = monitors.get(norm_sub, {})
    return {
        "status": m.get("status", "not_created"),
        "stage": m.get("stage", "No Knowledge Base Created"),
        "progress_pct": 100 if m.get("status") == "ready" else 0
    }

# ------------------------------------------------------------------
# Student & AI Tutor Routes (Direct Integration to pragtutor_backend.py)
# ------------------------------------------------------------------
class MarkLearnedRequest(BaseModel):
    student_id: str = "STU001"
    subject: str = "operating_systems"
    topic: str

@app.post("/api/student/mark_learned")
@app.post("/api/student/complete_topic")
def mark_student_topic_learned(req: MarkLearnedRequest):
    from student_database import mark_topic_as_learned
    updated_student = mark_topic_as_learned(req.student_id, req.topic)
    
    ACTIVITY_LOGS.insert(0, {
        "id": len(ACTIVITY_LOGS) + 1,
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "user": f"Student {req.student_id}",
        "role": "STUDENT",
        "action": f"Confirmed learning for topic: {req.topic} ({req.subject})"
    })

    return {
        "status": "success",
        "message": f"Successfully marked '{req.topic}' as learned.",
        "student_id": req.student_id,
        "completed_topics": updated_student.get("completed_topics", [])
    }

@app.get("/api/student/subjects")
def get_student_subjects():
    subjects = load_subjects()
    kb_data = load_kb_status()
    monitors = {m["subject_id"]: m for m in get_knowledge_base_monitors()}

    enriched = []
    for sub in subjects:
        sub_id = sub.get("id")
        norm_id = normalize_subject_id(sub_id)
        m = monitors.get(norm_id, {})
        status_info = kb_data.get(norm_id, {})
        
        status = status_info.get("status") or m.get("status", "not_created")
        
        enriched.append({
            **sub,
            "kb_status": "READY" if status == "ready" else "NOT_AVAILABLE",
            "pdf_uploaded": status_info.get("pdf_uploaded", m.get("pdf_count", 0) > 0),
            "last_prepared": status_info.get("last_prepared", "Not Prepared"),
            "status": status
        })
    return {"subjects": enriched}

@app.post("/api/student/query")
@app.post("/api/process_query")
@app.post("/api/tutor")
def process_student_query(req: QueryRequest):
    user_query = req.query or req.question
    if not user_query and not req.images:
        raise HTTPException(status_code=400, detail="Either 'query' or 'images' must be provided.")

    try:
        result = pragtutor_backend.process_query(
            query=user_query,
            images=req.images,
            student_id=req.student_id,
            subject=req.subject,
            level=req.level or "beginner"
        )

        ACTIVITY_LOGS.insert(0, {
            "id": len(ACTIVITY_LOGS) + 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "user": f"Student {req.student_id}",
            "role": "STUDENT",
            "action": f"Asked PragTutor [{req.level or 'beginner'}]: {user_query[:50]}..."
        })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/answer")
def chat_answer(req: QueryRequest):
    result = process_student_query(req)
    return {
        "answer": result.get("llm_response") or result.get("message") or "No response generated.",
        "topic_id": result.get("topic") or "general",
        "topic_name": (result.get("topic") or "General").replace("_", " ").title(),
        "topic_confidence": result.get("topic_confidence", 0.0),
        "level": result.get("level") or req.level or "beginner",
        "all_prerequisites": result.get("all_prerequisites", []),
        "student_completed": result.get("student_completed", []),
        "missing_prerequisites": result.get("missing_prerequisites", []),
        "learning_path": result.get("learning_path", []),
        "sources": result.get("retrieved_content") or [],
        "images": result.get("retrieved_images") or [],
        "status": result.get("status", "success"),
        "message": result.get("message")
    }

@app.get("/api/student/history")
def get_student_history(student_id: str = "STU001"):
    data = get_student(student_id)
    return {
        "student_id": student_id,
        "completed_topics": data.get("completed_topics", []),
        "recent_queries": []
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
