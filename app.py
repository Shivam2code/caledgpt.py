import os
import requests
from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse
import openai

app = Flask(__name__)

# Set up API keys (replace these with your actual keys)
DEEPGRAM_API_KEY = "db9a5a32d08c917d679c7f55aa3f48edc0096b0a"
OPENAI_API_KEY = "sk-qP-FZ9XGCwNlY04OCpm5xrBo-apViZyjx_kp25r_C3T3BlbkFJvZmHs4OPbg4U-PARaPlRE-xR2GYtb7MgVRBOuZRRMA"
openai.api_key = OPENAI_API_KEY
@app.route("/")
def start():
    return "The Called gpt server is running"
# Welcome message for incoming calls
@app.route("/voice", methods=["POST"])
def voice():
    response = VoiceResponse()
    response.say("Welcome to Called GPT, How can I help you?", voice='alice')
    
    # Record the caller's message
    response.record(max_length=30, action="/transcribe")
    return str(response)

# Handle audio and send it to Deepgram for transcription and response generation
@app.route("/transcribe", methods=["POST"])
def transcribe():
    audio_url = request.form['RecordingUrl'] + ".wav"
    
    # Send audio to Deepgram for transcription
    headers = {
        'Authorization': f'Token {DEEPGRAM_API_KEY}',
    }
    data = {
        'url': audio_url,
        'language': 'auto'  # Auto-detect language
    }
    
    deepgram_response = requests.post(
        'https://api.deepgram.com/v1/listen',
        headers=headers,
        json=data
    )
    
    transcription = deepgram_response.json()['results']['channels'][0]['alternatives'][0]['transcript']
    
    # Generate a response using GPT-3.5 based on the transcription
    gpt_response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=f"The user said: '{transcription}'. Respond emotionally and in the same language.",
        max_tokens=100
    )
    ai_response = gpt_response['choices'][0]['text'].strip()
    
    # Send AI's response to Deepgram for TTS
    tts_data = {
        'text': ai_response,
        'language': 'auto',  # Auto-detect language for TTS output
        'voice': 'en-US'  # You can change the voice if needed
    }
    tts_headers = {
        'Authorization': f'Token {DEEPGRAM_API_KEY}',
    }
    tts_response = requests.post(
        'https://api.deepgram.com/v1/text-to-speech',
        headers=tts_headers,
        json=tts_data
    )
    
    # Save the audio response
    with open("response.mp3", "wb") as audio_file:
        audio_file.write(tts_response.content)
    
    # Play the AI's response back to the caller
    voice_response = VoiceResponse()
    voice_response.play("/static/response.mp3")
    
    return str(voice_response)

# Serve the audio file for playback
@app.route("/static/response.mp3")
def serve_audio():
    return send_file("response.mp3", mimetype="audio/mp3")

