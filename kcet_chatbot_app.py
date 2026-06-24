import streamlit as st
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
#  DISPLAY CHAT HISTORY
# ──────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🎓"):
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

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(user_input)

    # Call Groq API
    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("Thinking..."):
            try:
                client = Groq(api_key=api_key)

                api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
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
                else:
                    st.error(f"❌ Something went wrong: {err}")

# ──────────────────────────────────────────────
#  WELCOME MESSAGE
# ──────────────────────────────────────────────
if not st.session_state.messages:
    st.info("👋 Hi! I'm the KCET AI Chatbot. Ask me anything about Kamaraj College — departments, placements, facilities, events, and more!")