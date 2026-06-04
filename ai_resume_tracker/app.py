from flask import Flask, render_template, request, redirect
import sqlite3
import os
import pdfplumber
import os
from openai import OpenAI


client = OpenAI(api_key="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")


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- DATABASE SETUP ----------------

def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT,
    role TEXT,
    status TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- SKILL DETECTION ----------------

def extract_skills(text):

    skills_list = [
    "python","java","sql","machine learning","deep learning",
    "data analysis","pandas","numpy","power bi","tableau",
    "html","css","javascript","react","nodejs",
    "docker","aws","flask","django","linux",
    "c","c++","embedded systems","electronics"
    ]

    found = []

    for skill in skills_list:
        if skill in text.lower():
            found.append(skill)

    return found


# ---------------- JOB RECOMMENDATION ----------------

def recommend_jobs(skills):

    jobs=[]

    if "python" in skills:
        jobs.append("Python Developer")

    if "machine learning" in skills:
        jobs.append("Machine Learning Engineer")

    if "sql" in skills:
        jobs.append("Data Analyst")

    if "javascript" in skills:
        jobs.append("Frontend Developer")

    if "html" in skills or "css" in skills:
        jobs.append("Web Developer")

    if "docker" in skills or "aws" in skills:
        jobs.append("DevOps Engineer")

    if len(jobs)==0:
        jobs.append("Software Developer")
        jobs.append("IT Support Engineer")

    return jobs


# ---------------- RESUME SCORE ----------------

def calculate_resume_score(skills):

    score = len(skills) * 15

    if score > 100:
        score = 100

    return score


# ---------------- JOB MATCHING ----------------

def calculate_match(resume_skills, job_text):

    job_text = job_text.lower()

    job_skills = [
        "python","java","sql","machine learning",
        "data analysis","html","css","javascript",
        "docker","aws","flask","react","node","mongodb"
    ]

    required = []

    for skill in job_skills:
        if skill in job_text:
            required.append(skill)

    matched = []

    for skill in required:
        if skill in resume_skills:
            matched.append(skill)

    if len(required) == 0:
        return 0, [], []

    match_rate = int((len(matched) / len(required)) * 100)

    missing = list(set(required) - set(matched))

    return match_rate, matched, missing


# ---------------- HOME DASHBOARD ----------------

@app.route("/")
def home():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM resumes")
    resume_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs")
    job_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status='Applied'")
    applied = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status='Interview'")
    interview = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status='Offer'")
    offer = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status='Rejected'")
    rejected = cursor.fetchone()[0]

    conn.close()

    return redirect("/resumes")


# ---------------- UPLOAD PAGE ----------------

@app.route("/upload")
def upload_page():
    return render_template("upload.html")


# ---------------- UPLOAD RESUME ----------------

@app.route("/upload_resume", methods=["POST"])
def upload_resume():

    file = request.files["resume"]

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    text = ""

    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text()
    except:
        text = ""

    skills = extract_skills(text)
    recommended = recommend_jobs(skills)
    score = calculate_resume_score(skills)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO resumes(filename) VALUES(?)",
        (file.filename,)
    )

    conn.commit()
    conn.close()

    return render_template(
        "resumes.html",
        skills=skills,
        jobs=recommended,
        score=score
    )


# ---------------- MATCH RESUME WITH JOB ----------------

@app.route("/match_resume", methods=["POST"])
def match_resume():

    jobdesc = request.form["jobdesc"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT filename FROM resumes ORDER BY id DESC LIMIT 1")
    file = cursor.fetchone()[0]

    conn.close()

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file)

    text = ""

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text()

    # Extract skills from resume
    resume_skills = extract_skills(text)

    # Extract skills from job description
    job_skills = extract_skills(jobdesc)

    matched = []
    missing = []

    for skill in job_skills:
        if skill in resume_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    if len(job_skills) == 0:
        match_rate = 0
    else:
        match_rate = int((len(matched) / len(job_skills)) * 100)

    # ----------- AI TIPS (THINK → DECIDE → ACT) -----------

    thought = ""
    strategy = ""
    tips = []

    # ---------------- THINK ----------------
    # Analyze situation

    if match_rate < 40:
        thought = "The resume has low similarity with the job description"

    elif match_rate < 70:
        thought = "The resume partially matches the job requirements"

    else:
        thought = "The resume strongly matches the job requirements"


    # ---------------- DECIDE ----------------
    # Decide strategy based on analysis

    if match_rate < 40:
        strategy = "Focus on adding missing core technical skills"

    elif match_rate < 70:
        strategy = "Improve existing skills and include missing ones"

    else:
        strategy = "Optimize resume formatting and apply for the job"


    # ---------------- ACT ----------------
    # Generate actionable tips

    if match_rate < 40:
        tips.append("Your resume has low alignment with this job role.")
        tips.append("Add important technical skills mentioned in the job description.")
        tips.append("Include relevant projects to strengthen your profile.")

    elif match_rate < 70:
        tips.append("Your resume partially matches this job.")
        tips.append("Improve by adding missing skills and enhancing experience.")
        tips.append("Highlight your strongest relevant skills clearly.")

    else:
        tips.append("Great! Your resume is well aligned with this job.")
        tips.append("Focus on formatting and clarity to stand out.")

    # Add missing skill suggestions
    if missing:
        tips.append("Missing skills: " + ", ".join(missing))

    # Skill-specific improvements
    if "python" in missing:
        tips.append("Add Python projects or certifications.")

    if "sql" in missing:
        tips.append("Include database experience using SQL.")

    if "aws" in missing:
        tips.append("Add cloud experience like AWS.")

    if "machine learning" in missing:
        tips.append("Include Machine Learning projects.")

    if "data analysis" in missing:
        tips.append("Add data analysis skills like Pandas or Excel.")

    # Edge case
    if not missing:
        tips.append("No major skill gaps found. Improve presentation and formatting.")
    return render_template(
        "match.html",
        match=match_rate,
        matched=matched,
        missing=missing,
        resume_skills=resume_skills,
        job_skills=job_skills,
        tips=tips
    )

# ---------------- SHOW RESUMES ----------------

@app.route("/resumes")
def resumes():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT filename FROM resumes ORDER BY id DESC LIMIT 1")
    file = cursor.fetchone()

    conn.close()

    if not file:
        return render_template("resumes.html", skills=[], jobs=[], score=0)

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file[0])

    text = ""

    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text()
    except:
        text = ""

    skills = extract_skills(text)
    jobs = recommend_jobs(skills)
    score = calculate_resume_score(skills)

    return render_template(
        "resumes.html",
        skills=skills,
        jobs=jobs,
        score=score
    )

# ---------------- JOB TRACKER ----------------

@app.route("/jobs")
def jobs():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs")
    data = cursor.fetchall()

    conn.close()

    return render_template("jobtracker.html", jobs=data)


# ---------------- ADD JOB ----------------

@app.route("/add_job", methods=["POST"])
def add_job():

    company = request.form["company"]
    role = request.form["role"]
    status = request.form["status"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO jobs(company,role,status) VALUES(?,?,?)",
        (company, role, status)
    )

    conn.commit()
    conn.close()

    return redirect("/jobs")


# ---------------- DELETE JOB ----------------

@app.route("/delete_job/<int:id>")
def delete_job(id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM jobs WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/jobs")


# ---------------- FRESHER JOBS ----------------

@app.route("/fresher_jobs")
def fresher_jobs():

    fresher_list = [
        ("Infosys", "Software Engineer"),
        ("TCS", "Ninja Developer"),
        ("Wipro", "Project Engineer"),
        ("Cognizant", "Programmer Analyst"),
        ("Accenture", "Associate Software Engineer")
    ]

    return render_template("fresher_jobs.html", jobs=fresher_list)


# ---------------- EXPERIENCED JOBS ----------------

@app.route("/experienced_jobs")
def experienced_jobs():

    experienced_list = [
        ("Google", "Senior Software Engineer"),
        ("Amazon", "Backend Developer"),
        ("Microsoft", "Cloud Engineer"),
        ("IBM", "Data Scientist"),
        ("Oracle", "DevOps Engineer")
    ]

    return render_template("experienced_jobs.html", jobs=experienced_list)


# ---------------- COMPANY DETAILS ----------------

@app.route("/company/<name>")
def company(name):

    companies = {

        "infosys": {
            "logo": "infosys.png",
            "about": "Infosys is a global IT services company headquartered in India.",
            "role": "Software Engineer",
            "skills": "Java, Python, SQL",
            "salary": "₹4 LPA - ₹8 LPA"
        },

        "tcs": {
            "logo": "tcs.png",
            "about": "TCS is one of the largest IT consulting companies in the world.",
            "role": "Ninja Developer",
            "skills": "Programming, Aptitude, Communication",
            "salary": "₹3.5 LPA - ₹7 LPA"
        },

        "wipro": {
            "logo": "wipro.png",
            "about": "Wipro is a global IT consulting company.",
            "role": "Project Engineer",
            "skills": "Java, Cloud, Testing",
            "salary": "₹3.5 LPA - ₹6 LPA"
        },

        "google": {
            "logo": "google.png",
            "about": "Google is a global technology leader in AI and internet services.",
            "role": "Software Engineer",
            "skills": "Data Structures, Algorithms, Machine Learning",
            "salary": "₹25 LPA - ₹60 LPA"
        },

        "amazon": {
            "logo": "amazon.png",
            "about": "Amazon is a global e-commerce and cloud computing company.",
            "role": "Software Development Engineer",
            "skills": "Java, System Design, Problem Solving",
            "salary": "₹20 LPA - ₹45 LPA"
        }

    }

    data = companies.get(name)

    return render_template(
        "company.html",
        company=data,
        name=name.capitalize()
    )


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)