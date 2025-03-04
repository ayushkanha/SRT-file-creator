import streamlit as st
import whisper
import tempfile
import os

st.title("🎙️ Audio to SRT Transcription App (Whisper)")

uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        file_path = tmpfile.name
        tmpfile.write(uploaded_file.read())

    st.audio(uploaded_file, format="audio/wav")

    # Load Whisper model
    model = whisper.load_model("medium")  # Change to "medium" or "large" for better accuracy

    # Transcribe
    result = model.transcribe(file_path)

    # Save as SRT
    srt_path = file_path.replace(".wav", ".srt")
    with open(srt_path, "w") as srt_file:
        for i, segment in enumerate(result["segments"]):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            srt_file.write(f"{i+1}\n{start:.3f} --> {end:.3f}\n{text}\n\n")

    st.success("✅ Transcription Complete!")
    st.text_area("Transcribed Text:", result["text"], height=200)

    with open(srt_path, "rb") as srt_file:
        st.download_button("📥 Download SRT File", srt_file, file_name="transcription.srt", mime="text/plain")

    os.remove(file_path)
    os.remove(srt_path)
