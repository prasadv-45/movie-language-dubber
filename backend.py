import asyncio
import os
import tempfile
from pathlib import Path

import gradio as gr
import edge_tts
from deep_translator import GoogleTranslator
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")
_model = None

LANGUAGES = {
    "Telugu": {"code": "te", "voice": "te-IN-ShrutiNeural"},
    "Hindi": {"code": "hi", "voice": "hi-IN-SwaraNeural"},
    "Tamil": {"code": "ta", "voice": "ta-IN-PallaviNeural"},
    "English": {"code": "en", "voice": "en-US-AriaNeural"},
    "Kannada": {"code": "kn", "voice": "kn-IN-SapnaNeural"},
    "Malayalam": {"code": "ml", "voice": "ml-IN-SobhanaNeural"},
}

def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model

async def make_speech(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def dub_video(video_path, target_language):
    if not video_path:
        raise gr.Error("Please upload a video first.")
    if target_language not in LANGUAGES:
        raise gr.Error("Please select a supported target language.")

    workdir = Path(tempfile.mkdtemp(prefix="dubber_"))
    output_path = str(workdir / "dubbed_video.mp4")
    video = None

    try:
        model = get_model()
        segments, info = model.transcribe(video_path, beam_size=1, vad_filter=True)
        translated_segments = []

        for index, segment in enumerate(segments):
            original = segment.text.strip()
            if not original:
                continue
            translated = GoogleTranslator(
                source="auto", target=LANGUAGES[target_language]["code"]
            ).translate(original)
            translated_segments.append((segment.start, segment.end, translated))

        if not translated_segments:
            raise gr.Error("No clear speech was detected. Try another video with audible speech.")

        voice = LANGUAGES[target_language]["voice"]
        audio_clips = []

        for index, (start, end, translated) in enumerate(translated_segments):
            speech_path = str(workdir / f"speech_{index}.mp3")
            asyncio.run(make_speech(translated, voice, speech_path))
            clip = AudioFileClip(speech_path).set_start(start)
            audio_clips.append(clip)

        video = VideoFileClip(video_path)
        dubbed_audio = CompositeAudioClip(audio_clips).set_duration(video.duration)
        final_video = video.set_audio(dubbed_audio)
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(workdir / "temp-audio.m4a"),
            remove_temp=True,
            logger=None,
        )
        final_video.close()
        return output_path, f"Done! Detected source language: {info.language}. Dubbed into {target_language}."
    except gr.Error:
        raise
    except Exception as exc:
        raise gr.Error(f"Dubbing failed: {exc}")
    finally:
        if video is not None:
            video.close()
        for clip in locals().get("audio_clips", []):
            try:
                clip.close()
            except Exception:
                pass

with gr.Blocks(title="AI Movie Language Dubber") as demo:
    gr.Markdown("# 🎬 AI Movie Language Dubber")
    gr.Markdown("Upload a short video, choose a language, and generate an AI-dubbed version.")
    video_input = gr.Video(label="Upload video", sources=["upload"], type="filepath")
    language_input = gr.Dropdown(
        choices=list(LANGUAGES.keys()),
        value="Telugu",
        label="Target language",
    )
    run_button = gr.Button("Generate Dubbed Video", variant="primary")
    output_video = gr.Video(label="Dubbed video")
    status = gr.Textbox(label="Status", interactive=False)
    run_button.click(
        fn=dub_video,
        inputs=[video_input, language_input],
        outputs=[output_video, status],
    )
    gr.Markdown("**Note:** Best for short clips during testing. Translation and voice generation require an internet connection.")

if __name__ == "__main__":
    demo.queue().launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 10000))
    )
