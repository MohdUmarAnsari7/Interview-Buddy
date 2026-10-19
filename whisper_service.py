from faster_whisper import WhisperModel

from config import (
    MODEL_SIZE,
    DEVICE,
    COMPUTE,
)


class WhisperService:
    """
    Handles Whisper model loading
    and audio transcription.
    """

    def __init__(self):
        self.model = None

    # ========================================================
    # Load model
    # ========================================================

    def load(self):

        if self.model is None:

            self.model = WhisperModel(
                MODEL_SIZE,
                device=DEVICE,
                compute_type=COMPUTE,
            )

    # ========================================================
    # Transcribe
    # ========================================================

    def transcribe(self, audio):

        if self.model is None:

            raise RuntimeError(
                "Whisper model has not been loaded."
            )

        segments, _ = self.model.transcribe(
            audio,
            beam_size=1,
            best_of=1,
            vad_filter=True,
            language="en",
            condition_on_previous_text=False,
            temperature=0,
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        return text