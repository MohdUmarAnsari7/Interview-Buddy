import threading

import numpy as np
import soundcard as sc

from config import RATE, CHUNK_SECONDS
from windows_utils import (
    initialize_com,
    uninitialize_com,
)


class SystemAudioService:
    """
    Captures Windows playback audio using
    SoundCard loopback.
    """

    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = None
        self.running = False
        self.selected_speaker_name = None

    # ========================================================
    # Start
    # ========================================================

    def start(
        self,
        on_chunk,
        on_status,
        on_device,
        on_error,
    ):
        """
        Start system audio capture.

        Callbacks:
            on_chunk(audio)
            on_status(message)
            on_device(device_name)
            on_error(error_message)
        """

        if self.running:
            return False

        self.stop_event = threading.Event()
        self.running = True

        self.thread = threading.Thread(
            target=self._worker,
            args=(
                on_chunk,
                on_status,
                on_device,
                on_error,
            ),
            daemon=True,
        )

        self.thread.start()

        return True

    # ========================================================
    # Stop
    # ========================================================

    def stop(self):
        self.stop_event.set()
        self.running = False

    # ========================================================
    # Worker
    # ========================================================

    def _worker(
        self,
        on_chunk,
        on_status,
        on_device,
        on_error,
    ):
        com_hr = None

        try:

            # SoundCard / WASAPI needs COM.
            com_hr = initialize_com()

            speakers = sc.all_speakers()

            if not speakers:
                raise RuntimeError(
                    "No playback devices found."
                )

            default = sc.default_speaker()

            selected = (
                default
                if default
                else speakers[0]
            )

            self.selected_speaker_name = (
                selected.name
            )

            on_device(
                selected.name
            )

            on_status(
                "● Listening..."
            )

            # Create loopback microphone.
            mic = sc.get_microphone(
                id=str(selected.name),
                include_loopback=True,
            )

            with mic.recorder(
                samplerate=RATE,
                channels=2,
            ) as recorder:

                while not self.stop_event.is_set():

                    audio = recorder.record(
                        numframes=(
                            RATE * CHUNK_SECONDS
                        )
                    )

                    # Stereo -> mono
                    mono = np.mean(
                        audio,
                        axis=1,
                    ).astype(
                        np.float32
                    )

                    on_chunk(mono)

        except Exception as exc:

            self.running = False
            self.stop_event.set()

            on_error(str(exc))

        finally:

            self.running = False

            if com_hr is not None:
                uninitialize_com(com_hr)