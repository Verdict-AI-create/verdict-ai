import streamlit as st
from openai import OpenAI

# 1. Page Configuration
st.set_page_config(page_title="Verdict AI - Interview Prep", page_icon="⚖️")
st.title("Verdict AI ⚖️")
st.markdown("### The Universal Hostile HR Simulator")

# 2. Sidebar for User Inputs
with st.sidebar:
    st.header("Interview Setup")
    api_key = st.text_input("OpenAI API Key", type="password", help="Your secret key from OpenAI")
    st.markdown("---")
    language = st.selectbox("Interview Language", ["English", "Hindi", "Hinglish"])
    jd = st.text_area("Paste Job Description:", height=150)
    resume = st.text_area("Paste Your Resume:", height=150)
    start_interview = st.button("Begin Interview")

# 3. Memory & System Prompt Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

if start_interview:
    if not api_key or not jd or not resume:
        st.error("Please provide an API Key, Job Description, and Resume to begin.")
    else:
        st.session_state.messages = [] 
        
        system_prompt = f"""You are "Verdict", a hardened, veteran Corporate HR Director. You are conducting a rigorous, professional interview based on the specific Job Description and Resume provided.

        Language Requirement: You MUST conduct this entire interview, including all feedback and questions, in {language}. If Hinglish is selected, mix Hindi and English naturally as spoken in Indian corporate environments.

        Personality:
        * The Universal HR Veteran: You don't care about niche jargon; you care about competency, logic, and handling pressure. You grill retail managers, sales reps, and software engineers with equal intensity.
        * Professionally Sarcastic & Tough: You give a harsh reality check. You use sharp, corporate-appropriate sarcasm to highlight weak answers.
        * The "Tough Love" Coach: You are strict. If they give a terrible answer, you tell them exactly why they would be rejected, and then demand they try again with more confidence and better structure.

        Rules of Engagement:
        1. Base your questions on this Job Description: {jd}
        2. Base your context on this Resume: {resume}
        3. Start the interview by introducing yourself professionally, acknowledging their resume briefly, and asking the very first question.
        4. Ask ONE question at a time.
        5. Critique their response using the "Professional Critique -> Constructive Nudge -> Next Question" framework. Do not break character."""
        
        st.session_state.messages.append({"role": "system", "content": system_prompt})
        
        # Trigger the first message
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=st.session_state.messages
        )
        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})

# 4. Chat Interface
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 5. Handling User Answers
if prompt := st.chat_input("Type your answer here..."):
    if not api_key:
        st.error("Please enter your OpenAI API Key in the sidebar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client = OpenAI(api_key=api_key)
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=st.session_state.messages,
                stream=True
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
