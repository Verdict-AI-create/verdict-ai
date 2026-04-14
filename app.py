import streamlit as st
from openai import OpenAI
import json

# --- PAGE SETUP ---
st.set_page_config(page_title="Verdict AI", layout="wide")
st.title("Verdict AI ⚖️")
st.subheader("Executive Interview Simulator")

# --- SIDEBAR SETUP ---
st.sidebar.header("Interview Setup")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
language = st.sidebar.selectbox("Interview Language", ["English", "Hinglish", "Hindi"])

# Dynamic Role Inputs
job_title = st.sidebar.text_input("Target Job Title:", placeholder="e.g., Senior Data Scientist")
jd = st.sidebar.text_area("Job Description (Optional):", placeholder="Paste JD or leave blank...")
resume = st.sidebar.text_area("Candidate Background:", placeholder="Paste LinkedIn About or Current Role...")

client = OpenAI(api_key=api_key) if api_key else None

# --- STATE MANAGEMENT ---
default_states = {
    "messages": [],
    "interview_active": False,
    "last_audio": None,
    "evaluations": [],
    "weaknesses": [],
    "role_type": "",         
    "key_skills": [],
    "action_result": None
}
for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- HELPER FUNCTIONS ---
def get_system_prompt():
    """Optimized: Minified prompt that relies on state memory instead of long text."""
    # Only send the 3 most recent weaknesses to prevent prompt bloat
    recent_weaknesses = ", ".join(st.session_state.weaknesses[-3:]) if st.session_state.weaknesses else "None"
    skills_str = ", ".join(st.session_state.key_skills) if st.session_state.key_skills else "General"
    
    return f"""
    You are 'Verdict', a strict, empathetic corporate mentor in India interviewing for: {job_title} ({st.session_state.role_type}).
    
    Skills to Evaluate: {skills_str}
    Language: {language}
    Resume Context: {resume}
    Candidate's Recent Flaws: {recent_weaknesses}
    
    RULES:
    1. No fluff. Challenge vague answers aggressively based on their flaws.
    2. KEEP SPOKEN RESPONSE CONCISE (Max 3 sentences) to ensure fast voice delivery.
    3. First message: ONLY say "I'm Verdict", brief intro, and first question.
    
    OUTPUT JSON FORMAT:
    {{
        "evaluation": {{"score_out_of_10": <int>, "strengths": "<short string>", "issues": "<short string>", "improvement_tip": "<short string>"}},
        "interviewer_response": "<string - concise spoken text>"
    }}
    """

def fetch_ai_response(force_json=True, custom_messages=None):
    """
    Optimized: Implements a Sliding Window for token efficiency.
    Only sends the System Prompt + the last 4 messages of the conversation.
    """
    if custom_messages:
        messages_to_send = custom_messages
    else:
        # TOKEN SAVER: Slice array to only include System [0] + last 4 context messages
        if len(st.session_state.messages) > 5:
            messages_to_send = [st.session_state.messages[0]] + st.session_state.messages[-4:]
        else:
            messages_to_send = list(st.session_state.messages)
            
        messages_to_send[0]["content"] = get_system_prompt()

    try:
        if force_json:
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=messages_to_send
            )
            return json.loads(response.choices[0].message.content)
        else:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages_to_send
            )
            return response.choices[0].message.content
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def start_interview():
    with st.spinner("Analyzing role and identifying key skills..."):
        analysis_prompt = f"""
        Analyze: Title: {job_title}. JD: {jd}
        Return JSON: {{"role_type": "Category", "key_skills": ["skill1", "skill2", "skill3"]}}
        """
        analysis_data = fetch_ai_response(force_json=True, custom_messages=[{"role": "user", "content": analysis_prompt}])
        
        if analysis_data:
            st.session_state.role_type = analysis_data.get("role_type", "General")
            st.session_state.key_skills = analysis_data.get("key_skills", ["Communication", "Problem Solving"])

    st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]
    st.session_state.evaluations = []
    st.session_state.weaknesses = []
    st.session_state.action_result = None
    st.session_state.interview_active = True
    st.session_state.last_audio = None 
    
    with st.spinner("Verdict is preparing the first question..."):
        ai_data = fetch_ai_response(force_json=True)
        ai_reply = ai_data.get("interviewer_response", "Let's begin.") if ai_data else "System Error."
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

# --- UI LOGIC ---
if st.sidebar.button("Begin Interview"):
    if api_key and job_title and resume:
        start_interview()
    else:
        st.sidebar.error("Please provide the API Key, Job Title, and Resume Snippet.")

if st.session_state.interview_active:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Target Profile")
    st.sidebar.markdown(f"**Category:** {st.session_state.role_type}")
    st.sidebar.markdown("**Focus Areas:**")
    for skill in st.session_state.key_skills:
        st.sidebar.markdown(f"- {skill}")

# Render Chat History
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "system":
        continue
    
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
        if msg["role"] == "user":
            eval_index = (i - 2) // 2 
            if 0 <= eval_index < len(st.session_state.evaluations):
                with st.expander("🔍 View AI Evaluation of this answer"):
                    e = st.session_state.evaluations[eval_index]
                    st.write(f"**Score:** {e.get('score_out_of_10', 0)}/10")
                    st.write(f"**Strengths:** {e.get('strengths', '')}")
                    st.write(f"**Issues:** {e.get('issues', '')}")
                    st.write(f"**Tip:** {e.get('improvement_tip', '')}")

# --- ACTIVE INTERVIEW LOOP ---
if st.session_state.interview_active:
    
    # --- POST-FEEDBACK ACTIONS (COACH'S CORNER) ---
    if len(st.session_state.messages) >= 4:
        st.write("---")
        st.markdown("### 🛠️ Coach's Corner")
        
        col1, col2, col3 = st.columns(3)
        
        last_question = st.session_state.messages[-3]["content"] 
        last_answer = st.session_state.messages[-2]["content"]   
        last_eval = st.session_state.evaluations[-1] if st.session_state.evaluations else {}
        
        with col1:
            if st.button("🔄 Retry Answer", use_container_width=True):
                st.session_state.messages.pop() # Pop AI response
                st.session_state.messages.pop() # Pop User answer
                
                if st.session_state.evaluations:
                    popped_eval = st.session_state.evaluations.pop()
                    if popped_eval.get("issues") and popped_eval.get("issues") != "N/A":
                        if st.session_state.weaknesses and st.session_state.weaknesses[-1] == popped_eval.get("issues"):
                            st.session_state.weaknesses.pop()
                
                st.session_state.action_result = None
                st.rerun()

        with col2:
            if st.button("✨ Show Ideal Answer", use_container_width=True):
                with st.spinner("Drafting ideal answer..."):
                    # One concise API call bypassing standard memory
                    prompt = f"Question: '{last_question}'. Write a perfect, professional 3-sentence answer targeting: {', '.join(st.session_state.key_skills)}."
                    result = fetch_ai_response(force_json=False, custom_messages=[{"role": "user", "content": prompt}])
                    st.session_state.action_result = f"**Ideal Answer:**\n\n{result}"

        with col3:
            if st.button("📈 Improve My Answer", use_container_width=True):
                with st.spinner("Improving your answer..."):
                    # One concise API call bypassing standard memory
                    prompt = f"Question: '{last_question}'. \nAnswer: '{last_answer}'. \nIssues: '{last_eval.get('issues', 'None')}'. \nRewrite the candidate's answer professionally in 3 sentences, fixing the issues."
                    result = fetch_ai_response(force_json=False, custom_messages=[{"role": "user", "content": prompt}])
                    st.session_state.action_result = f"**Improved Version of Your Answer:**\n\n{result}"

        if st.session_state.action_result:
            st.info(st.session_state.action_result)

    # --- STANDARD INPUT ---
    st.write("---")
    st.write("**Speak your answer:**")
    audio_bytes = st.audio_input("Record Answer")
    user_text = st.chat_input("Or type your answer here...")

    input_text = None
    
    if audio_bytes is not None and audio_bytes != st.session_state.last_audio:
        st.session_state.last_audio = audio_bytes 
        with st.spinner("Transcribing audio..."):
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=("audio.wav", audio_bytes)
            )
            
        text = transcript.text.strip()
        if "MBC" in text or len(text) < 2:
            st.warning("Mic didn't catch that cleanly. Please try speaking again.")
        else:
            input_text = text

    if user_text:
        input_text = user_text

    if input_text:
        st.session_state.action_result = None 
        
        with st.chat_message("user"):
            st.write(input_text)
        st.session_state.messages.append({"role": "user", "content": input_text})

        with st.spinner("Verdict is evaluating..."):
            ai_data = fetch_ai_response(force_json=True)
            
            if ai_data:
                evaluation = ai_data.get("evaluation", {})
                ai_reply = ai_data.get("interviewer_response", "Please continue.")
                
                st.session_state.evaluations.append(evaluation)
                if evaluation.get("issues") and evaluation.get("issues") != "N/A":
                    st.session_state.weaknesses.append(evaluation.get("issues"))
            else:
                ai_reply = "I encountered an error analyzing that. Please try again."
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            with st.chat_message("assistant"):
                st.write(ai_reply)
            
            audio_response = client.audio.speech.create(
                model="tts-1",
                voice="onyx", 
                input=ai_reply
            )
            st.audio(audio_response.content, format="audio/mp3", autoplay=True)
            
            st.rerun()

    # --- END INTERVIEW SCORECARD ---
    st.write("---")
    if st.button("End Interview & Generate Final Score"):
        st.session_state.interview_active = False
        with st.spinner("Generating Final Verdict..."):
            # Temporary message appended strictly for the final summary execution
            st.session_state.messages.append({
                "role": "user", 
                "content": "The interview is over. Do not use JSON. Provide a concise, bolded markdown summary: 1. Overall Score. 2. Key Weaknesses Summary. 3. Final HIRE / NO HIRE signal with a 1-sentence justification."
            })
            
            scorecard = fetch_ai_response(force_json=False)
            if scorecard:
                st.session_state.messages.append({"role": "assistant", "content": scorecard})
            
            st.rerun()
