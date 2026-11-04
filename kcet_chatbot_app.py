
import streamlit as st
import base64
from groq import Groq

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="KCET Info Chatbot",
    page_icon="🎓",
    layout="centered"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------
st.markdown("""
<style>
    .main {
        background-color: #f8f9fb;
    }

    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 8px;
    }

    .title-block {
        background: linear-gradient(135deg, #1a237e, #1565c0);
        padding: 24px 20px;
        border-radius: 14px;
        text-align: center;
        margin-bottom: 20px;
    }

    .title-block h1 {
        color: white;
        font-size: 1.8rem;
        margin: 0;
    }

    .title-block p {
        color: #bbdefb;
        font-size: 0.95rem;
        margin: 6px 0 0 0;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# COLLEGE KNOWLEDGE BASE
# --------------------------------------------------
SYSTEM_PROMPT = """
You are an AI-powered assistant for Kamaraj College of
Engineering and Technology (KCET), located in Virudhunagar,
Tamil Nadu, India.

You were built by Vrijin Steffi A, an IT student
(2023-2027 batch) at KCET.

Answer questions in a friendly, helpful and concise way.
Always stay on topic. Answer questions related to KCET
or general college and academic queries.

If a question is outside your scope, politely redirect
the user to KCET-related topics.

COLLEGE INFORMATION:

GENERAL INFO:
- Full Name: Kamaraj College of Engineering and Technology
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
- UG: B.E / B.Tech (4 years)
- Civil, Mechanical, EEE, ECE, CSE, IT and AI&DS
- PG: M.E / M.Tech in selected departments
- MBA: 2-year programme

FACILITIES:
- Central Library with digital resources
- Computer labs with high-speed internet
- AI and Data Science lab
- Sports ground and indoor games
- Canteen and cafeteria
- Boys and Girls Hostel
- Wi-Fi campus
- Active Placement Cell

PLACEMENTS:
- Placement training and mock interviews
- Resume preparation workshops
- Top Recruiters: TCS, Infosys, Wipro, HCL,
  Cognizant, Capgemini, Zoho, Amazon and Accenture

EVENTS AND FESTS:
- Technovanza - Annual Technical Symposium
- Kalaimagal - Cultural Fest
- Sports Day
- NSS Events
- Workshops and Guest Lectures

IT DEPARTMENT:
- Programming in C
- Object-Oriented Programming (Java)
- Data Structures
- DBMS
- Computer Networks
- Artificial Intelligence
- Machine Learning
- Web Technologies
- Cloud Computing
- Software Engineering

ABOUT THE CHATBOT:
- Built by: Vrijin Steffi A (IT, 2027 batch)
- Phase 2: AI-powered upgrade from the original
  rule-based chatbot.
- Phase 1 used Python keyword matching.
- Phase 2 uses Groq AI API with a Streamlit interface.
"""

# --------------------------------------------------
# GROQ MODELS
# --------------------------------------------------
TEXT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.8-27b"

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

# --------------------------------------------------
# API KEY
# --------------------------------------------------
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    api_key = None

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def encode_image(file):
    return base64.b64encode(file.getvalue()).decode("utf-8")


def image_mime(file):
    return getattr(file, "type", None) or "image/jpeg"


# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown("""
<div class="title-block">
    <h1>🎓 KCET College Info Chatbot</h1>
    <p>
        Kamaraj College of Engineering and Technology
        · AI-Powered · Built by Vrijin Steffi A
    </p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:

    st.header("⚙️ Settings")

    if not api_key:
        st.warning("⚠️ API key not configured.")

    st.markdown("---")
    st.markdown("**📸 Attach an Image**")

    img_tab1, img_tab2 = st.tabs(["Upload", "Camera"])

    with img_tab1:
        uploaded_file = st.file_uploader(
            "Upload an image",
            type=["jpg", "jpeg", "png"],
            key="uploader"
        )

    with img_tab2:
        camera_file = st.camera_input(
            "Take a photo",
            key="camera"
        )

    active_image = camera_file or uploaded_file

    if active_image:
        st.image(
            active_image,
            caption="Attached image",
            use_container_width=True
        )

        if st.button("❌ Remove image", use_container_width=True):
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
        "Tell me about the IT department"
    ]

    for suggestion in suggestions:
        if st.button(suggestion, use_container_width=True):
            st.session_state.pending_input = suggestion
            st.rerun()

    st.markdown("---")
    st.caption("Phase 2 · Groq AI Powered · Streamlit UI")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_input = None
        st.rerun()


# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------
for msg in st.session_state.messages:

    with st.chat_message(
        msg["role"],
        avatar="🧑‍🎓" if msg["role"] == "user" else "🎓"
    ):

        if msg.get("image_preview"):
            st.image(msg["image_preview"], width=220)

        st.markdown(msg["content"])


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------
user_input = st.chat_input("Ask me anything about KCET...")

if st.session_state.pending_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None


# --------------------------------------------------
# PROCESS USER QUESTION
# --------------------------------------------------
if user_input:

    if not api_key:
        st.error(
            "API key is missing. Please configure "
            "GROQ_API_KEY in Streamlit Secrets."
        )
        st.stop()

    image_for_this_turn = active_image

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "image_preview": image_for_this_turn
    })

    with st.chat_message("user", avatar="🧑‍🎓"):

        if image_for_this_turn:
            st.image(image_for_this_turn, width=220)

        st.markdown(user_input)

    # --------------------------------------------------
    # GROQ API CALL
    # --------------------------------------------------
    with st.chat_message("assistant", avatar="🎓"):

        with st.spinner("Thinking..."):

            try:

                client = Groq(api_key=api_key)

                # IMAGE QUESTION
                if image_for_this_turn:

                    b64 = encode_image(image_for_this_turn)
                    mime = image_mime(image_for_this_turn)

                    vision_messages = [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Please answer this question "
                                        "about the attached image: "
                                        + user_input
                                    )
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": (
                                            f"data:{mime};base64,{b64}"
                                        )
                                    }
                                }
                            ]
                        }
                    ]

                    response = client.chat.completions.create(
                        model=VISION_MODEL,
                        messages=vision_messages,
                        max_completion_tokens=1024
                    )

                # TEXT-ONLY QUESTION
                else:

                    api_messages = [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        }
                    ]

                    for msg in st.session_state.messages:

                        if not msg.get("image_preview"):
                            api_messages.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })

                    response = client.chat.completions.create(
                        model=TEXT_MODEL,
                        messages=api_messages,
                        max_completion_tokens=1024
                    )

                # GET RESPONSE
                reply = response.choices[0].message.content

                if not reply:
                    reply = "Sorry, I couldn't generate a response. Please try again."

                st.markdown(reply)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply
                })

            except Exception as e:

                err = str(e).lower()

                if "401" in err or "authentication" in err or "api key" in err:
                    st.error(
                        "❌ Invalid API key. Please check "
                        "your Groq API key in Streamlit Secrets."
                    )

                elif "429" in err or "rate limit" in err:
                    st.error(
                        "⏳ Rate limit reached. Please wait "
                        "and try again."
                    )

                elif "model" in err or "404" in err:
                    st.error(
                        "❌ Model error. Please check the "
                        "Groq model availability and access."
                    )

                else:
                    st.error(f"❌ Something went wrong: {e}")

    # Clear image after sending
    if image_for_this_turn:
        st.session_state.pop("uploader", None)
        st.session_state.pop("camera", None)
        st.rerun()


# --------------------------------------------------
# WELCOME MESSAGE
# --------------------------------------------------
if not st.session_state.messages:

    st.info(
        "👋 Hi! I'm the KCET AI Chatbot. "
        "Ask me anything about Kamaraj College — "
        "departments, placements, facilities, events "
        "and more! You can also attach a photo, "
        "such as a form, notice or timetable, "
        "and ask me about it."
    )
