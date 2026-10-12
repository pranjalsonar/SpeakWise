"""SpeakWise speech-analysis pipeline.

    from speakwise import process_session
    report = process_session("talk.mp4", topic="...", reading_material="...")
"""
__version__ = "0.1.0"


def process_session(*args, **kwargs):
    """See speakwise.pipeline.process_session (imported lazily to keep `import speakwise` light)."""
    from speakwise.pipeline import process_session as _impl

    return _impl(*args, **kwargs)
