import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os
import textwrap

st.title("🎙️ Audio to Text Transcription App (Google)")

uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])

def split_text(text, words_per_line=3):
    words = text.split()
    return textwrap.wrap(" ".join(words), width=words_per_line * 5)

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        file_path = tmpfile.name
        tmpfile.write(uploaded_file.read())

    st.audio(uploaded_file, format="audio/wav")

    # Convert audio to WAV format (Mono & 16000 Hz)
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(file_path, format="wav")

    recognizer = sr.Recognizer()

    with sr.AudioFile(file_path) as source:
        st.write("🔄 Transcribing entire audio... Please wait!")

        # Recognizing audio in a single step
        audio_data = recognizer.record(source)

        try:
            full_text = recognizer.recognize_google(audio_data)
            st.success("✅ Transcription Complete!")

            # Splitting text into 3-4 word lines
            formatted_text = "\n".join(split_text(full_text))
            st.text_area("Transcribed Text:", formatted_text, height=200)

            # Save as SRT file
            srt_text = "1\n00:00:00,000 --> 00:00:10,000\n" + formatted_text  # Placeholder timestamp
            srt_path = file_path.replace(".wav", ".srt")
            
            with open(srt_path, "w") as srt_file:
                srt_file.write(srt_text)

            with open(srt_path, "rb") as srt_file:
                st.download_button("📥 Download SRT File", srt_file, file_name="transcription.srt", mime="text/plain")

        except sr.UnknownValueError:
            st.error("❌ Could not understand the audio.")
        except sr.RequestError:
            st.error("❌ Google API error. Check internet connection.")

    # Clean up temp files
    os.remove(file_path)
