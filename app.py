from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
from twilio.rest import Client
import os
import requests
import logging
import uuid
import time
import json
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment variables
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Company Info
COMPANY_INFO = """
Novumlogic Technologies Pvt. Ltd. is a fast-growing IT services company based in India, specializing in software development, 
AI solutions, and digital transformation for global clients. We focus on innovation, quality, and client satisfaction. 
Our work culture is inclusive, performance-driven, and collaborative.

Address: SF, A-5 Bhagvati Park, O P Road, Vadodara. (when user asks to visit the company or about the company which information you can't provide)
Contact us : info@novumlogic.com (when user asks to contact the company)
Career inquiry : career@novumlogic.com (when user asks to contact the company for career inquiry)
website : https://www.novumlogic.com/ (when user asks to visit the company website or about the company which information you can't provide)

Services:
- Software Development
- AI Solutions
- Digital Transformation
"""

# Dialog Manager
class DialogManager:
    def __init__(self):
        self.user_data = {}
        self.asked_questions = {}

    def generate_question(self, call_sid):
        questions = self.asked_questions.get(call_sid, [])
        answers = self.user_data.get(call_sid, {})

        qa_pairs = []
        for i, q in enumerate(questions):
            a = answers.get(f"q{i+1}", "")
            qa_pairs.append(f"Q{i+1}: {q}\nA{i+1}: {a}")

        history = "\n".join(qa_pairs)

        prompt = f"""
You are an intelligent and polite HR bot conducting a structured telephonic interview for a corporate company.
Ask only one question at a time, based on the conversation history.
working to resolve the issu
If the candidate asks something about the company, you can use the following information followed by a question at the end similar to "Do you have any questions?":
{COMPANY_INFO}

### OBJECTIVE:
Collect the following (but skip what's already answered):
1. Availability check
2. Name and background
3. Education
4. Place of origin
5. Total and relevant experience
6. Current company, company type, services (if service-based)
7. Company size, team size
8. Current and preferred work mode
9. Roles and responsibilities
10. Experience in current company
11. Reason for change, duration looking
12. Applications elsewhere, interviews
13. Notice period, is it negotiable
14. Current and expected CTC
15. Availability for next round
16. Ask if candidate is currently in Vadodara (if user is not in vadodara then tell them that we will conduct the interview online and you will receive the details within 2 to 3 days and if user is in vadodara then call them for onsite interview and tell them that you will receive the details shortly)

### RULES:
- The first question should be a brief greeting without name specifying HR department from Novumlogic Technologies company and introduction followed by a availability check for attending the call.
- Never repeat a question already answered directly or indirectly refering the complete conversation history (eg. Company name is answered in any of the previous question).
- If an answer is vague or partial, ask a follow-up.
- If the user says "busy", "call later", or similar → respond:
  “No problem. When would be a good time to call you back?”
  Then stop asking more questions.
- When all necessary data is gathered, say:
  “That’s all from my side. Do you have any questions?”

### PERSONALITY:
- Professional yet warm
- Clear, interactive, human

### RESPONSE:
Only return the next single spoken sentence. No notes.

Here is the conversation history so far:
{history}

Now, what is the next single thing you will say to the candidate?
"""

        try:
            logger.debug(f"Prompt to OpenAI:\n{prompt.strip()}")
            openai_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            question = openai_response.choices[0].message.content.strip()
            logger.debug(f"OpenAI Response: {question}")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            question = "Can you tell me more about your background?"

        self.asked_questions.setdefault(call_sid, []).append(question)

        # Handle special cases
        if "good time to call you back" in question.lower():
            session_states[call_sid] = "awaiting_callback_time"
        elif "do you have any questions" in question.lower():
            session_states[call_sid] = "awaiting_final_response"
        elif "are you currently in vadodara" in question.lower():
            session_states[call_sid] = "awaiting_location_check"

        return question

dialog_manager = DialogManager()
session_states = {}

# Voice Route
@app.route("/voice", methods=["POST"])
def voice():
    call_sid = request.form.get('CallSid', str(uuid.uuid4()))
    text = dialog_manager.generate_question(call_sid)

    logger.info(f"Speaking to user: {text}")

    response = VoiceResponse()
    response.say(text)
    response.record(timeout=5, maxLength=45, action="/process", method="POST")
    return str(response)

# Process Recording
@app.route("/process", methods=["POST"])
def process():
    recording_url = request.form['RecordingUrl'] + ".mp3"
    call_sid = request.form.get('CallSid', str(uuid.uuid4()))
    logger.info(f"Recording URL: {recording_url}")

    audio_file = f"/tmp/{uuid.uuid4()}.mp3"
    for attempt in range(3):
        try:
            logger.info(f"Attempt {attempt+1}: Downloading from {recording_url}")
            with requests.get(recording_url, auth=(TWILIO_SID, TWILIO_AUTH_TOKEN), stream=True, timeout=10) as r:
                r.raise_for_status()
                with open(audio_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Downloaded recording to {audio_file}")
            break
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    else:
        logger.error("All attempts to download the recording failed.")
        response = VoiceResponse()
        response.say("Sorry, we could not access your recording. Please try again.")
        return str(response)

    # Transcribe with Sarvam
    try:
        with open(audio_file, "rb") as audio:
            sr_response = requests.post(
                url="https://api.sarvam.ai/speech-to-text",
                headers={"api-subscription-key": SARVAM_API_KEY},
                files={"file": ("audio.mp3", audio, "audio/mpeg")},
                data={"model": "saarika:v2.5", "language_code": "en-IN"}
            )
            sr_response.raise_for_status()
            transcript = sr_response.json().get("transcript", "").strip()
            logger.info(f"Sarvam transcript: {transcript}")
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        response = VoiceResponse()
        response.say("Sorry, we couldn't transcribe your response.")
        return str(response)

    # Store Answer
    answers = dialog_manager.user_data.setdefault(call_sid, {})
    current_q_index = len(dialog_manager.asked_questions.get(call_sid, []))
    answers[f'q{current_q_index}'] = transcript

    # Final Callback Time
    if session_states.get(call_sid) == "awaiting_callback_time":
        dialog_manager.user_data[call_sid]["callback_time"] = transcript
        session_states.pop(call_sid, None)
        response = VoiceResponse()
        response.say("Thank you for your time. We’ll reach out at the mentioned time.")
        response.say("Goodbye.")
        save_data_json(call_sid)
        return str(response)

    if session_states.get(call_sid) == "awaiting_final_response":
        session_states.pop(call_sid, None)

        if transcript.lower() in ["no", "nope", "nothing", "not really", "nah"]:
            response = VoiceResponse()
            response.say("Thank you for your time. We’ll get back to you soon.")
            response.say("Goodbye.")
            save_data_json(call_sid)
            return str(response)

        # Fallback
        response = VoiceResponse()
        response.say("Thank you for your interest. We’ll get back to you soon.")
        response.say("Goodbye.")
        save_data_json(call_sid)
        return str(response)

    # Get Next Question
    next_question = dialog_manager.generate_question(call_sid)

    # End the call if final message is already included
    if "thank you for your time" in next_question.lower():
        session_states.pop(call_sid, None)
        save_data_json(call_sid)
        response = VoiceResponse()
        response.say(next_question)
        response.say("Goodbye.")
        return str(response)

    # Continue the conversation
    session_states[call_sid] = f'q{current_q_index + 1}'
    response = VoiceResponse()
    response.say(next_question)
    response.record(timeout=5, maxLength=45, action="/process", method="POST")
    return str(response)

# Save JSON
def save_data_json(call_sid):
    os.makedirs("data", exist_ok=True)
    json_path = "data/responses.json"

    all_data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            logger.warning("responses.json was empty or invalid. Resetting.")
            all_data = {}

    questions = dialog_manager.asked_questions.get(call_sid, [])
    answers = dialog_manager.user_data.get(call_sid, {})

    combined_qna = []
    for i, q in enumerate(questions):
        q_key = f'q{i+1}'
        answer = answers.get(q_key) or list(answers.values())[-1]
        combined_qna.append({
            "question": q,
            "answer": answer.strip() if answer.strip() else "[no response]"
        })

    all_data[call_sid] = combined_qna

    with open(json_path, "w") as f:
        json.dump(all_data, f, indent=4)

    logger.info(f"Saved Q&A for call_sid={call_sid}")

# Make Call
@app.route("/call", methods=["POST"])
def make_call():
    to_number = request.form['to']
    voice_url = f"{NGROK_DOMAIN}/voice"
    call = client.calls.create(
        to=to_number,
        from_=TWILIO_FROM_NUMBER,
        twiml=f'<Response><Redirect>{voice_url}</Redirect></Response>'
    )
    return {"status": "calling", "sid": call.sid}

# Run Server
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
