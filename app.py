import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment, silence
import tempfile
import os
import textwrap

# Ensure ffmpeg is installed (Streamlit Cloud needs this)
AudioSegment.converter = "/usr/bin/ffmpeg"

# Function to split text into 3-4 word chunks
def split_text(text, words_per_line=3):
    words = text.split()
    return textwrap.wrap(" ".join(words), width=words_per_line * 5)  # Approximate width

# Function to format text into SRT format
def generate_srt(transcriptions):
    srt_content = ""
    index = 1

    for start_time, end_time, text in transcriptions:
        chunks = split_text(text, words_per_line=3)  # Split into 3-word lines
        chunk_duration = (end_time - start_time) / max(1, len(chunks))  # Distribute duration

        for chunk in chunks:
            start_srt = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02},000"
            end_srt = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02},000"

            srt_content += f"{index}\n{start_srt} --> {end_srt}\n{chunk}\n\n"
            index += 1
            start_time += chunk_duration  # Shift start time for next chunk

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

    with sr.AudioFile(file_path) as source:
        # Split audio on silence with better thresholds
        audio_chunks = silence.split_on_silence(
            audio,
            min_silence_len=700,  # Increase to 700ms to ensure proper chunks
            silence_thresh=-35,  # Lower threshold for catching speech parts
            keep_silence=400  # Keep some silence to maintain context
        )

        if not audio_chunks:
            st.error("⚠️ No speech detected in audio file!")
        else:
            st.write(f"🔄 Processing {len(audio_chunks)} audio chunks...")

        for i, chunk in enumerate(audio_chunks):
            chunk_path = f"{file_path}_{i}.wav"
            chunk.export(chunk_path, format="wav")

            # Skip chunks that are too short (<1 sec)
            if len(chunk) < 1000:
                os.remove(chunk_path)
                continue

            with sr.AudioFile(chunk_path) as audio_source:
                recognizer.adjust_for_ambient_noise(audio_source, duration=0.5)
                audio_data = recognizer.record(audio_source)

            try:
                text = recognizer.recognize_google(audio_data)
                st.write(f"✅ Chunk {i+1}: {text}")  # Debug output
                transcriptions.append((i * 3, (i + 1) * 3, text))
            except sr.UnknownValueError:
                st.write(f"❌ Chunk {i+1}: Could not recognize speech")
            except sr.RequestError:
                st.error("❌ Google API error. Check internet connection.")
                break
            finally:
                os.remove(chunk_path)  # Remove temp files

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
