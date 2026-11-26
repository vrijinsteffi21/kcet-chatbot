import streamlit as st
import base64
import json
import re
import uuid
from datetime import date, datetime
from pathlib import Path
from groq import Groq

# ──────────────────────────────────────────────
#  PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="KCET Info Chatbot",
    page_icon="🎓",
    layout="centered"
)

# ──────────────────────────────────────────────
#  CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fb; }
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    .title-block {
        background: linear-gradient(135deg, #1a237e, #1565c0);
        padding: 24px 20px;
        border-radius: 14px;
        text-align: center;
        margin-bottom: 20px;
    }
    .title-block h1 { color: white; font-size: 1.8rem; margin: 0; }
    .title-block p  { color: #bbdefb; font-size: 0.95rem; margin: 6px 0 0 0; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
#  COLLEGE KNOWLEDGE BASE
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """
You are an AI-powered assistant for Kamaraj College of Engineering and Technology (KCET),
located in Virudhunagar, Tamil Nadu, India.
You were built by Vrijin Steffi A, an IT student (2023–2027 batch) at KCET.

Answer questions in a friendly, helpful, and concise way.
Always stay on topic — only answer questions related to KCET or general college/academic queries.
If asked something outside your scope, politely redirect.

Here is the knowledge base about KCET:

GENERAL INFO:
- Full Name: Kamaraj College of Engineering and Technology (KCET)
- Location: Virudhunagar, Tamil Nadu, India
- Established: 1995
- Affiliation: Anna University, Chennai
- Accreditation: NAAC Accredited
- Website: www.kamarajengg.edu.in
- Phone: 04562-235066
- Email: principal@kamarajengg.edu.in

DEPARTMENTS:
- Civil Engineering
- Mechanical Engineering
- Electrical and Electronics Engineering (EEE)
- Electronics and Communication Engineering (ECE)
- Computer Science and Engineering (CSE)
- Information Technology (IT)
- Artificial Intelligence and Data Science (AI&DS)
- Mechanical Engineering (Sandwich)

COURSES OFFERED:
- UG: B.E / B.Tech (4 years) — Civil, Mechanical, EEE, ECE, CSE, IT, AI&DS
- PG: M.E / M.Tech — Selected departments
- MBA: 2-year programme

FACILITIES:
- Central Library with digital resources
- Computer labs with high-speed internet
- AI & Data Science lab
- Sports ground and indoor games
- Canteen and cafeteria
- Boys and Girls Hostel
- Wi-Fi campus
- Active Placement Cell

PLACEMENTS:
- Active placement cell with pre-placement training, mock interviews, resume workshops
- Top Recruiters: TCS, Infosys, Wipro, HCL, Cognizant, Capgemini, Zoho, Amazon, Accenture

EVENTS & FESTS:
- Technovanza – Annual Technical Symposium
- Kalaimagal – Cultural Fest
- Sports Day
- NSS Events
- Workshops and Guest Lectures

IT DEPARTMENT:
- Key Subjects: Programming in C, OOP (Java), Data Structures, DBMS, Computer Networks,
  Artificial Intelligence, Machine Learning, Web Technologies, Cloud Computing, Software Engineering

NOTES PORTAL:
- Students can open the "Notes" page from the sidebar and log in with their roll number
  (username and password) to download notes uploaded for their own year of study.
- Only staff/admin can upload notes.

ABOUT THE BOT:
- Built by: Vrijin Steffi A (IT, 2027 batch)
- This is Phase 2 — an AI-powered upgrade from the original rule-based chatbot
- Phase 1 used Python keyword matching; Phase 2 uses Groq AI API with a Streamlit UI
""".strip()

# Vision-capable Groq model. Check console.groq.com/docs/vision before deploying —
# vision model names/availability change over time.
VISION_MODEL = "qwen/qwen3.8-27b"
TEXT_MODEL = "openai/gpt-oss-120b"

# ──────────────────────────────────────────────
#  NOTES PORTAL — SETTINGS & HELPERS
# ──────────────────────────────────────────────
NOTES_DIR = Path("notes")
INDEX_FILE = NOTES_DIR / "index.json"

# Students see only notes for their year AND their department (or notes tagged "all").
FILTER_BY_DEPT = True

# Department code (the letters in the roll number, e.g. 23UIT112 -> "uit") -> display name.
# Only "uit" is confirmed. CHECK the other codes against real KCET roll numbers and fix them.
DEPARTMENTS = {
    "uit": "Information Technology",
    "ucs": "Computer Science and Engineering",
    "uad": "Artificial Intelligence and Data Science",
    "uec": "Electronics and Communication Engineering",
    "uee": "Electrical and Electronics Engineering",
    "ume": "Mechanical Engineering",
    "uce": "Civil Engineering",
}


def dept_name(code: str) -> str:
    if code == "all":
        return "All Departments"
    return DEPARTMENTS.get(code, code.upper())

YEAR_LABELS = {1: "1st Year", 2: "2nd Year", 3: "3rd Year", 4: "Final Year"}

# Roll number format: 2-digit batch + department letters + 3-digit serial (e.g. 23uit112)
ROLL_PATTERN = re.compile(r"^(\d{2})([a-z]{2,4})(\d{3})$")


def parse_roll(roll_no: str):
    """Return student info from a roll number, or None if invalid / not a current student."""
    roll_no = roll_no.strip().lower()
    match = ROLL_PATTERN.match(roll_no)
    if not match:
        return None

    batch = 2000 + int(match.group(1))   # 23 -> 2023
    dept = match.group(2)                # uit
    today = date.today()
    # Academic year starts in June
    start_year = today.year if today.month >= 6 else today.year - 1
    study_year = start_year - batch + 1  # e.g. 2026 - 2023 + 1 = 4

    if study_year < 1 or study_year > 4:
        return None

    return {
        "roll": roll_no,
        "batch": batch,
        "dept": dept,
        "year": study_year,
        "is_admin": False,
    }


def check_password(roll_no: str, password: str) -> bool:
    # Current rule: password is the roll number itself.
    # Replace this function later with hashed, per-user passwords.
    return password.strip().lower() == roll_no.strip().lower()


def get_admin_password():
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return None


def load_index():
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_index(items):
    NOTES_DIR.mkdir(exist_ok=True)
    INDEX_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def add_note(uploaded, title, subject, year, dept):
    NOTES_DIR.mkdir(exist_ok=True)
    note_id = uuid.uuid4().hex[:8]
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", uploaded.name)
    stored_name = f"{note_id}_{safe_name}"
    (NOTES_DIR / stored_name).write_bytes(uploaded.getvalue())

    items = load_index()
    items.append({
        "id": note_id,
        "title": title.strip() or uploaded.name,
        "subject": subject.strip() or "General",
        "year": int(year),
        "dept": dept.strip().lower() or "all",
        "original_name": uploaded.name,
        "stored_name": stored_name,
        "uploaded_at": datetime.now().strftime("%d %b %Y"),
    })
    save_index(items)


def delete_note(note_id):
    items = load_index()
    keep = []
    for n in items:
        if n["id"] == note_id:
            path = NOTES_DIR / n["stored_name"]
            if path.exists():
                path.unlink()
        else:
            keep.append(n)
    save_index(keep)


def login_form():
    st.subheader("🔐 Notes Login")
    st.caption("Students: username and password are your roll number (e.g. 23uit112).")
    with st.form("login_form"):
        username = st.text_input("Username (Roll number)")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        uname = username.strip().lower()

        # Staff / admin login
        if uname == "admin":
            admin_pw = get_admin_password()
            if admin_pw and password == admin_pw:
                st.session_state.user = {"roll": "admin", "is_admin": True}
                st.rerun()
            else:
                st.error("❌ Wrong admin password.")
            return

        # Student login
        info = parse_roll(uname)
        if info is None:
            st.error("❌ Invalid roll number, or you are not a current student.")
        elif not check_password(uname, password):
            st.error("❌ Wrong password.")
        else:
            st.session_state.user = info
            st.rerun()


def student_view(user):
    st.success(
        f"Logged in as **{user['roll'].upper()}** · {YEAR_LABELS[user['year']]} · {dept_name(user['dept'])}"
    )
    items = [
        n for n in load_index()
        if n["year"] == user["year"]
        and (not FILTER_BY_DEPT or n["dept"] in ("all", user["dept"]))
    ]

    if not items:
        st.info(f"No notes uploaded yet for {YEAR_LABELS[user['year']]}.")
        return

    for subject in sorted({n["subject"] for n in items}):
        st.markdown(f"### 📘 {subject}")
        for n in [x for x in items if x["subject"] == subject]:
            path = NOTES_DIR / n["stored_name"]
            if not path.exists():
                continue
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{n['title']}**")
                st.caption(f"{n['original_name']} · uploaded {n['uploaded_at']}")
            with col2:
                st.download_button(
                    "⬇️ Download",
                    data=path.read_bytes(),
                    file_name=n["original_name"],
                    key=f"dl_{n['id']}",
                    use_container_width=True,
                )
        st.markdown("---")


def admin_view():
    st.success("Logged in as **Admin / Staff**")

    st.subheader("📤 Upload Notes")
    with st.form("upload_form", clear_on_submit=True):
        title = st.text_input("Title", placeholder="e.g. Unit 3 - Normalization")
        subject = st.text_input("Subject", placeholder="e.g. DBMS")
        c1, c2 = st.columns(2)
        with c1:
            year = st.selectbox("For which year?", [1, 2, 3, 4], format_func=lambda y: YEAR_LABELS[y], index=3)
        with c2:
            dept = st.selectbox("Department", ["all"] + list(DEPARTMENTS.keys()), format_func=dept_name)
        file = st.file_uploader("Choose file", type=["pdf", "docx", "pptx", "txt", "zip", "jpg", "png"])
        submitted = st.form_submit_button("Upload", use_container_width=True)

    if submitted:
        if not file:
            st.error("❌ Please choose a file.")
        else:
            add_note(file, title, subject, year, dept)
            st.success(f"✅ Uploaded for {YEAR_LABELS[year]}.")
            st.rerun()

    st.subheader("🗂️ Manage Notes")
    items = load_index()
    if not items:
        st.info("No notes uploaded yet.")
        return

    for n in sorted(items, key=lambda x: (x["year"], x["subject"])):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{n['title']}**")
            st.caption(f"{YEAR_LABELS[n['year']]} · {n['subject']} · {dept_name(n['dept'])} · {n['uploaded_at']}")
        with col2:
            if st.button("🗑️ Delete", key=f"del_{n['id']}", use_container_width=True):
                delete_note(n["id"])
                st.rerun()


def notes_page():
    user = st.session_state.user
    if not user:
        login_form()
        return

    top1, top2 = st.columns([4, 1])
    with top1:
        st.subheader("📚 College Notes")
    with top2:
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    if user["is_admin"]:
        admin_view()
    else:
        student_view(user)


# ──────────────────────────────────────────────
#  SESSION STATE
# ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

if "user" not in st.session_state:
    st.session_state.user = None

# ──────────────────────────────────────────────
#  HEADER
# ──────────────────────────────────────────────
st.markdown("""
<div class="title-block">
  <h1>🎓 KCET College Info Chatbot</h1>
  <p>Kamaraj College of Engineering and Technology · AI-Powered · Built by Vrijin Steffi A</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
#  SIDEBAR
# ──────────────────────────────────────────────
active_image = None

with st.sidebar:
    page = st.radio("Go to", ["💬 Chat", "📚 Notes"], label_visibility="collapsed")
    st.markdown("---")

    st.header("⚙️ Settings")
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = None
        st.warning("⚠️ API key not configured.")

    if page == "💬 Chat":
        st.markdown("---")
        st.markdown("**📸 Attach an Image**")
        img_tab1, img_tab2 = st.tabs(["Upload", "Camera"])
        with img_tab1:
            uploaded_file = st.file_uploader(
                "Upload an image", type=["jpg", "jpeg", "png"], key="uploader"
            )
        with img_tab2:
            camera_file = st.camera_input("Take a photo", key="camera")

        # Prefer a freshly taken photo over a stale upload if both exist
        active_image = camera_file or uploaded_file
        if active_image:
            st.image(active_image, caption="Attached image", use_container_width=True)
            if st.button("❌ Remove image", use_container_width=True):
                active_image = None
                st.session_state.pop("uploader", None)
                st.session_state.pop("camera", None)
                st.rerun()

        st.markdown("---")
        st.markdown("**Quick Topics:**")
        suggestions = [
            "What departments are available?",
            "Tell me about placements",
            "What facilities does the college have?",
            "What events does KCET conduct?",
            "What courses are offered?",
            "Tell me about the IT department",
        ]
        for s in suggestions:
            if st.button(s, use_container_width=True):
                st.session_state.pending_input = s
                st.rerun()

        st.markdown("---")
        st.caption("Phase 2 · Groq AI Powered · Streamlit UI")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_input = None
            st.rerun()

# ──────────────────────────────────────────────
#  NOTES PAGE (stops here so the chat below does not render)
# ──────────────────────────────────────────────
if page == "📚 Notes":
    notes_page()
    st.stop()

# ──────────────────────────────────────────────
#  CHAT HELPERS
# ──────────────────────────────────────────────
def encode_image(file) -> str:
    return base64.b64encode(file.getvalue()).decode("utf-8")


def image_mime(file) -> str:
    # st.file_uploader / st.camera_input give .type; default to jpeg if missing
    return getattr(file, "type", None) or "image/jpeg"

# ──────────────────────────────────────────────
#  DISPLAY CHAT HISTORY
# ──────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🎓"):
        if msg.get("image_preview"):
            st.image(msg["image_preview"], width=220)
        st.markdown(msg["content"])

# ──────────────────────────────────────────────
#  HANDLE INPUT
# ──────────────────────────────────────────────
user_input = st.chat_input("Ask me anything about KCET...")

if st.session_state.pending_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None

if user_input:
    if not api_key:
        st.warning("⚠️ API key is not configured. Add GROQ_API_KEY in Streamlit secrets.")
        st.stop()

    image_for_this_turn = active_image  # snapshot at time of send

    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "image_preview": image_for_this_turn if image_for_this_turn else None,
    })
    with st.chat_message("user", avatar="🧑‍🎓"):
        if image_for_this_turn:
            st.image(image_for_this_turn, width=220)
        st.markdown(user_input)

    # Call Groq API
    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("Thinking..."):
            try:
                client = Groq(api_key=api_key)

                if image_for_this_turn:
                    # Vision call: image + text in a single user message
                    b64 = encode_image(image_for_this_turn)
                    mime = image_mime(image_for_this_turn)

                    vision_messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Please answer this question about the attached image: " + user_input
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{mime};base64,{b64}"}
                                }
                            ]
                        }
                    ]

                    response = client.chat.completions.create(
                        model=VISION_MODEL,
                        messages=vision_messages,
                        max_completion_tokens=1024,
                    )
                else:
                    # Normal text-only call with chat history
                    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                        if not m.get("image_preview")
                    ]

                    response = client.chat.completions.create(
                        model=TEXT_MODEL,
                        messages=api_messages,
                        max_completion_tokens=1024,
                    )

                reply = response.choices[0].message.content
                if not reply:
                    reply = "Sorry, I couldn't generate a response. Please try again."
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

            except Exception as e:
                err = str(e).lower()
                if "401" in err or "authentication" in err or "api key" in err:
                    st.error("❌ Invalid API key. Please check your Groq API key in Streamlit Secrets.")
                elif "429" in err or "rate limit" in err:
                    st.error("⏳ Rate limit reached. Please wait and try again.")
                elif "model" in err or "404" in err:
                    st.error("❌ Model error. Please check the Groq model availability and access.")
                else:
                    st.error(f"❌ Something went wrong: {e}")

    # Clear the used image so it doesn't attach to the next question by accident
    if image_for_this_turn:
        st.session_state.pop("uploader", None)
        st.session_state.pop("camera", None)
        st.rerun()

# ──────────────────────────────────────────────
#  WELCOME MESSAGE
# ──────────────────────────────────────────────
if not st.session_state.messages:
    st.info("👋 Hi! I'm the KCET AI Chatbot. Ask me anything about Kamaraj College — departments, placements, facilities, events, and more! You can also attach a photo from the sidebar and ask about it, or open 📚 Notes to download your year's notes.")