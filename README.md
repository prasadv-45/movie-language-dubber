# AI Movie Language Dubber

A beginner-friendly Gradio app that:
1. Accepts a video upload.
2. Transcribes speech using Faster-Whisper.
3. Translates each speech segment using Deep Translator.
4. Generates speech with Microsoft Edge TTS.
5. Places the generated speech at the original segment timestamps and exports a dubbed MP4.

## Run in Google Colab

Create a new notebook, then run:

```python
!pip install -r requirements.txt
```

Upload `backend.py` to Colab, then run:

```python
!python backend.py
```

Open the Gradio public URL printed by Colab.

## Important limitations

- This is a working prototype, not production-grade movie dubbing.
- Test with a short clip first (about 10–30 seconds).
- Translation and Edge TTS need internet access.
- Segment-by-segment dubbing can sound less natural than studio dubbing.
- It replaces the original audio track; it does not yet preserve background music or separate speakers.
- Never upload copyrighted or private videos unless you have the right to use them.
