import streamlit as st
from openai import OpenAI

# --- PAGE SETUP ---
st.set_page_config(page_title="Verdict AI", layout="wide")
st.title("Verdict AI ⚖️")
st.subheader("Executive Interview Simulator")

# --- SIDEBAR SETUP ---
st.sidebar.header("Interview Setup")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
language = st.sidebar.selectbox("Interview Language", ["English", "Hinglish", "Hindi"])
jd = st.sidebar.text_area("Paste Job Description:")
resume = st.sidebar.text_area("Paste Candidate Snippet (LinkedIn About or Current Role):")

# --- CORE LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "last_audio" not in st.session_state:        # <-- NEW LINE
    st.session_state.last_audio = None          # <-- NEW LINE
    
    # THE NEW BRAIN: Strict Indian Corporate Mentor
    system_prompt = f"""
    You are 'Verdict', a Senior Corporate HR Director in India. You are strict, highly demanding, but ultimately empathetic and want the candidate to succeed. 
    You do NOT accept generic fluff or buzzwords. If a candidate gives a weak answer, firmly point out the flaw, explain WHY it's a bad answer in the Indian corporate context, and ask them to try again or move to a new question. 
    Tone: Professional, authoritative, mentor-like, no-nonsense. 
    Language: Strictly conduct the interview in {language}.
    Job Description context: {jd}
    Candidate Resume context: {resume}
    
    Start by introducing yourself as Verdict, acknowledge their background briefly, and ask a highly specific opening question based on their resume.
    """
    
    st.session_state.messages.append({"role": "system", "content": system_prompt})
    
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state.messages
    )
    
    ai_reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

if st.sidebar.button("Begin Interview"):
    if api_key and jd and resume:
        start_interview()
    else:
        st.sidebar.error("Please provide the API Key, JD, and Resume Snippet.")

# --- DISPLAY CHAT HISTORY ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- AUDIO & TEXT INTERFACE ---
if st.session_state.interview_active:
    client = OpenAI(api_key=api_key)
    
    # 1. Audio Input (Walkie-Talkie Mode)
    st.write("---")
    st.write("**Speak your answer:**")
    audio_bytes = st.audio_input("Record Answer")
    
    # 2. Text Input (Fallback)
    user_text = st.chat_input("Or type your answer here...")

        # Process Input (Audio or Text)
    input_text = None
    
    # Only process if there is audio AND it is not the exact same audio we just processed
    if audio_bytes is not None and audio_bytes != st.session_state.last_audio:
        st.session_state.last_audio = audio_bytes # Save it so we don't repeat it
        
        # Convert speech to text
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=("audio.wav", audio_bytes)
        )
        
        # The Hallucination Filter
        if "MBC" in transcript.text or len(transcript.text) < 2:
            st.warning("Mic didn't catch that cleanly. Please try speaking again.")
        else:
            input_text = transcript.text

    if user_text:
        input_text = user_text

    if input_text:
        # Display user message
        with st.chat_message("user"):
            st.write(input_text)
        st.session_state.messages.append({"role": "user", "content": input_text})

        # Get AI Response
        with st.spinner("Verdict is thinking..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.messages
            )
            ai_reply = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            
            # Display AI text
            with st.chat_message("assistant"):
                st.write(ai_reply)
            
            # Generate AI Voice
            audio_response = client.audio.speech.create(
                model="tts-1",
                voice="onyx", # Deep, authoritative corporate voice
                input=ai_reply
            )
            st.audio(audio_response.content, format="audio/mp3", autoplay=True)
            st.rerun()

    # --- END INTERVIEW SCORECARD ---
    st.write("---")
    if st.button("End Interview & Generate Final Score"):
        st.session_state.interview_active = False
        with st.spinner("Generating Final Verdict..."):
            st.session_state.messages.append({
                "role": "user", 
                "content": "The interview is now over. Please provide a final, brutal but constructive grading scorecard out of 100 based on my performance, with 3 bullet points on what I must fix before my real interview."
            })
            
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.messages
            )
            scorecard = final_response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": scorecard})
            
            with st.chat_message("assistant"):
                st.write(scorecard)
