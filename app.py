import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os

# Title
st.title("🎙️ Audio to Text Transcription App (Google)")

# Upload audio file
uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        file_path = tmpfile.name
        tmpfile.write(uploaded_file.read())

    st.audio(uploaded_file, format="audio/wav")

    # Convert to WAV (Google API requires WAV)
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(file_path, format="wav")

    # Recognize speech
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        st.write("🔄 Transcribing... Please wait!")
        audio_data = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio_data)
            st.success("✅ Transcription Complete!")
            st.text_area("Transcribed Text:", text, height=200)
        except sr.UnknownValueError:
            st.error("❌ Could not understand the audio.")
        except sr.RequestError:
            st.error("❌ Google API error. Check internet connection.")

    # Clean up temp file
    os.remove(file_path)
