import streamlit as st
import base64
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

ABOUT THE BOT:
- Built by: Vrijin Steffi A (IT, 2027 batch)
- This is Phase 2 — an AI-powered upgrade from the original rule-based chatbot
- Phase 1 used Python keyword matching; Phase 2 uses Groq AI API with a Streamlit UI
""".strip()

# Vision-capable Groq model. Check Groq's model list before deploying —
# vision model names/availability change over time.
VISION_MODEL = "qwen/qwen3.8-27b"
TEXT_MODEL = "llama-3.3-70b-versatile"

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
with st.sidebar:
    st.header("⚙️ Settings")
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = None
        st.warning("⚠️ API key not configured.")

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

    st.markdown("---")
    st.caption("Phase 2 · Groq AI Powered · Streamlit UI")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ──────────────────────────────────────────────
#  SESSION STATE
# ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

# ──────────────────────────────────────────────
#  HELPERS
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
        st.warning("⚠️ Please enter your Groq API key in the sidebar to use the AI chatbot.")
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
                    # Vision call: image + text go in a single user message.
                    # (Vision models on Groq currently support one user turn
                    # with image content, not a full running history.)
                    b64 = encode_image(image_for_this_turn)
                    mime = image_mime(image_for_this_turn)

                    vision_messages = [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"{SYSTEM_PROMPT}\n\nUser question about the attached image: {user_input}"
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
                        max_tokens=512,
                    )
                else:
                    # Normal text-only call with full chat history
                    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                        if not m.get("image_preview")  # skip image turns' raw content here
                    ]

                    response = client.chat.completions.create(
                        model=TEXT_MODEL,
                        messages=api_messages,
                        max_tokens=512,
                    )

                reply = response.choices[0].message.content
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

            except Exception as e:
                err = str(e)
                if "auth" in err.lower() or "api key" in err.lower() or "401" in err:
                    st.error("❌ Invalid API key. Please check and try again.")
                elif "rate" in err.lower():
                    st.error("⏳ Rate limit reached. Please wait a moment and try again.")
                elif "model" in err.lower() and "decommission" in err.lower():
                    st.error("❌ The vision model may have been renamed/retired by Groq. Check the current model list.")
                else:
                    st.error(f"❌ Something went wrong: {err}")

    # Clear the used image so it doesn't attach to the next question by accident
    if image_for_this_turn:
        st.session_state.pop("uploader", None)
        st.session_state.pop("camera", None)

# ──────────────────────────────────────────────
#  WELCOME MESSAGE
# ──────────────────────────────────────────────
if not st.session_state.messages:
    st.info("👋 Hi! I'm the KCET AI Chatbot. Ask me anything about Kamaraj College — departments, placements, facilities, events, and more! You can also attach a photo (e.g. a form, notice, or timetable) from the sidebar and ask about it.")