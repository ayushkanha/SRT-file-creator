import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os

# Function to format text into SRT format
def generate_srt(transcriptions):
    srt_content = ""
    for i, (start_time, end_time, text) in enumerate(transcriptions, 1):
        start_srt = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02},000"
        end_srt = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02},000"
        srt_content += f"{i}\n{start_srt} --> {end_srt}\n{text}\n\n"
    return srt_content

st.title("🎙️ Audio to Text Transcription App (Google)")

uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        file_path = tmpfile.name
        tmpfile.write(uploaded_file.read())

    st.audio(uploaded_file, format="audio/wav")

    # Convert to WAV
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(file_path, format="wav")

    recognizer = sr.Recognizer()
    transcriptions = []
    step = 5
    with sr.AudioFile(file_path) as source:
        duration = int(source.DURATION)  # Get total duration in seconds
        
        # Process in 5-second chunks
        for i in range(0, duration, step):
            source = sr.AudioFile(file_path)  # Reopen file for each iteration
            with source as audio_source:
                recognizer.adjust_for_ambient_noise(audio_source, duration=0.5)
                audio_data = recognizer.record(audio_source, offset=i, duration=step)  # Use offset correctly
            try:
                text = recognizer.recognize_google(audio_data)
                transcriptions.append((i, min(i + step, duration), text))  # Store chunk timestamps
            except sr.UnknownValueError:
                continue  # Skip if the chunk is not recognized
            except sr.RequestError:
                st.error("❌ Google API error. Check internet connection.")
                break

    # Generate SRT content
    srt_text = generate_srt(transcriptions)

    # Save SRT file
    srt_path = file_path.replace(".wav", ".srt")
    with open(srt_path, "w") as srt_file:
        srt_file.write(srt_text)

    st.success("✅ Transcription Complete!")
    st.text_area("Transcribed Text:", "\n".join([t[2] for t in transcriptions]), height=200)

    # Provide SRT file for download
    with open(srt_path, "rb") as srt_file:
        st.download_button("📥 Download SRT File", srt_file, file_name="transcription.srt", mime="text/plain")

    # Clean up
    os.remove(file_path)
    os.remove(srt_path)
