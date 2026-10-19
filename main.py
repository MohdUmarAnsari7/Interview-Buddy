import sys
import queue
import threading

from PySide6.QtCore import (
    QObject,
    Signal,
)
from PySide6.QtWidgets import (
    QApplication,
)

from assistant_window import AssistantWindow
from audio_service import SystemAudioService
from whisper_service import WhisperService
from ai_client import AIClient
from windows_utils import (
    set_capture_protection,
    set_tool_window,
    set_click_through, 
    register_global_hotkeys,
    unregister_global_hotkeys,
    register_transparent_hotkey,
    unregister_transparent_hotkey,
) 

from config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
)


class AppController(QObject):

    # ========================================================
    # Worker -> UI signals
    # ========================================================

    status_changed = Signal(str)

    device_changed = Signal(str)

    transcription_received = Signal(str)

    listening_changed = Signal(bool)

    audio_state_changed = Signal(bool)

    capture_state_changed = Signal(bool)

    transparent_state_changed = Signal(bool)

    # AI streaming
    ai_stream_started = Signal()

    ai_stream_chunk = Signal(str)

    ai_stream_finished = Signal()

    ai_error_received = Signal(str)

    # ========================================================
    # Constructor
    # ========================================================

    def __init__(self, window):

        super().__init__()

        self.window = window

        # ----------------------------------------------------
        # Services
        # ----------------------------------------------------

        self.audio_service = (
            SystemAudioService()
        )

        self.whisper_service = (
            WhisperService()
        )

        self.ai_client = AIClient(
            api_key=AI_API_KEY,
            base_url=AI_BASE_URL,
            model=AI_MODEL,
        )

        # ----------------------------------------------------
        # Audio queue
        # ----------------------------------------------------

        self.audio_queue = queue.Queue(
            maxsize=4
        )

        self.transcription_stop_event = (
            threading.Event()
        )

        self.listening = False

        self.capture_protection_enabled = (
            True
        )

        self.transparent_enabled = (
            False
        )

        register_global_hotkeys(
            self.window
        )

        # ----------------------------------------------------
        # UI connections
        # ----------------------------------------------------

        self.window.listen_requested.connect(
            self.toggle_listening
        )

        self.window.ask_ai_requested.connect(
            self.ask_ai
        )

        self.window.capture_toggle_requested.connect(
            self.toggle_capture_protection
        )

        self.window.transparent_toggle_requested.connect(
            self.toggle_transparent
        )

        # ----------------------------------------------------
        # Normal UI updates
        # ----------------------------------------------------

        self.status_changed.connect(
            self.window.set_status
        )

        self.device_changed.connect(
            self.window.set_device
        )

        self.transcription_received.connect(
            self.window.append_question
        )

        self.listening_changed.connect(
            self.window.set_listening
        )

        self.audio_state_changed.connect(
            self.window.set_audio_status
        )

        self.capture_state_changed.connect(
            self.window.set_capture_state
        )

        # Apply capture protection by default on startup
        self.apply_capture_protection(
            True,
            update_status=False,
        )

        self.transparent_state_changed.connect(
            self.window.set_transparent_state
        )

        self.transparent_state_changed.emit(
            self.transparent_enabled
        )

        # ----------------------------------------------------
        # Streaming AI updates
        # ----------------------------------------------------

        self.ai_stream_started.connect(
            self.window.start_ai_stream
        )

        self.ai_stream_chunk.connect(
            self.window.append_ai_response
        )

        self.ai_stream_finished.connect(
            self.window.finish_ai_stream
        )

        self.ai_error_received.connect(
            self.window.show_ai_error
        )

        # ----------------------------------------------------
        # Load Whisper
        # ----------------------------------------------------

        threading.Thread(
            target=self.load_whisper,
            daemon=True,
        ).start()

    # ========================================================
    # Whisper
    # ========================================================

    def load_whisper(self):

        try:

            self.whisper_service.load()

            self.status_changed.emit(
                "● Ready - press Start Listening"
            )

        except Exception as exc:

            self.status_changed.emit(
                f"● Whisper error: {exc}"
            )

    # ========================================================
    # Listening
    # ========================================================

    def toggle_listening(self):

        if self.listening:
            self.stop_listening()

        else:
            self.start_listening()

    def start_listening(self):

        if self.whisper_service.model is None:

            self.status_changed.emit(
                "● Whisper model is still loading..."
            )

            return

        if self.listening:
            return

        self._clear_audio_queue()

        self.transcription_stop_event = (
            threading.Event()
        )

        self.listening = True

        self.audio_state_changed.emit(
            True
        )

        self.listening_changed.emit(
            True
        )

        self.status_changed.emit(
            "● Starting audio capture..."
        )

        # ----------------------------------------------------
        # Start audio
        # ----------------------------------------------------

        self.audio_service.start(
            on_chunk=self.handle_audio_chunk,
            on_status=self.handle_status,
            on_device=self.handle_device,
            on_error=self.handle_audio_error,
        )

        # ----------------------------------------------------
        # Start Whisper
        # ----------------------------------------------------

        transcription_event = (
            self.transcription_stop_event
        )

        threading.Thread(
            target=self.transcription_worker,
            args=(transcription_event,),
            daemon=True,
        ).start()

    def stop_listening(self):

        self.listening = False

        self.audio_service.stop()

        self.transcription_stop_event.set()

        self.audio_state_changed.emit(
            False
        )

        self.listening_changed.emit(
            False
        )

        self.status_changed.emit(
            "● Stopped"
        )

    # ========================================================
    # Audio
    # ========================================================

    def handle_audio_chunk(self, audio):

        try:

            self.audio_queue.put(
                audio,
                timeout=0.5,
            )

        except queue.Full:

            pass

    def handle_status(self, text):

        self.status_changed.emit(
            text
        )

    def handle_device(self, name):

        self.device_changed.emit(
            name
        )

    def handle_audio_error(self, error):

        self.listening = False

        self.transcription_stop_event.set()

        self.audio_state_changed.emit(
            False
        )

        self.listening_changed.emit(
            False
        )

        self.status_changed.emit(
            f"● Audio error: {error}"
        )

    # ========================================================
    # Whisper worker
    # ========================================================

    def transcription_worker(
        self,
        stop_event,
    ):

        while (
            not stop_event.is_set()
            or not self.audio_queue.empty()
        ):

            try:

                audio = self.audio_queue.get(
                    timeout=0.5
                )

            except queue.Empty:

                continue

            try:

                text = (
                    self.whisper_service
                    .transcribe(audio)
                )

                if text:

                    self.transcription_received.emit(
                        text
                    )

            except Exception as exc:

                self.status_changed.emit(
                    f"● Transcription error: {exc}"
                )

    # ========================================================
    # AI
    # ========================================================

    def ask_ai(self):

        if getattr(self, "ai_busy", False):
            return

        context = (
            self.window
            .get_context()
        )

        question = (
            self.window
            .get_question()
        )

        if not question:

            self.status_changed.emit(
                "● Question box is empty"
            )

            return

        # ----------------------------------------------------
        # Build prompt
        # ----------------------------------------------------

        if context:

            final_prompt = (
                "Use the following context to understand "
                "the user's situation.\n\n"
                "CONTEXT:\n"
                f"{context}\n\n"
                "QUESTION:\n"
                f"{question}"
            )

        else:

            final_prompt = question

        self.status_changed.emit(
            "● Generating answer..."
        )

        # ----------------------------------------------------
        # Start worker
        # ----------------------------------------------------

        threading.Thread(
            target=self.ai_worker,
            args=(final_prompt,),
            daemon=True,
        ).start()

    # ========================================================
    # AI worker with streaming
    # ========================================================

    def ai_worker(self, prompt):

        self.ai_busy = True

        try:

            # Tell UI that generation started.
            self.ai_stream_started.emit()

            # Stream every piece as it arrives.
            self.ai_client.stream_answer(
                prompt,
                self.handle_ai_chunk,
            )

            # Generation finished.
            self.ai_stream_finished.emit()

            self.status_changed.emit(
                "● Answer ready"
            )

        except Exception as exc:

            self.ai_error_received.emit(
                str(exc)
            )

        finally:

            self.ai_busy = False

    def handle_ai_chunk(self, chunk):

        self.ai_stream_chunk.emit(
            chunk
        )

    # ========================================================
    # Capture protection
    # ========================================================

    def apply_capture_protection(self, enabled=True, update_status=True):

        try:

            success = set_capture_protection(
                self.window,
                enabled,
            )

            if not success:

                if update_status:
                    self.status_changed.emit(
                        "● Could not change capture protection"
                    )

                return False

            set_tool_window(
                self.window,
                enabled,
            )

            self.capture_protection_enabled = (
                enabled
            )

            self.capture_state_changed.emit(
                enabled
            )

            if update_status:
                if enabled:

                    self.status_changed.emit(
                        "● Protected: Screen & Taskbar hidden"
                    )

                else:

                    self.status_changed.emit(
                        "● Protection disabled"
                    )

            return True

        except Exception as exc:

            if update_status:
                self.status_changed.emit(
                    f"● Capture protection error: {exc}"
                )

            return False

    def toggle_capture_protection(self):

        self.apply_capture_protection(
            not self.capture_protection_enabled
        )

    # ========================================================
    # Transparent / Click-through
    # ========================================================

    def toggle_transparent(self):

        enabled = (
            not self.transparent_enabled
        )

        try:

            set_click_through(
                self.window,
                enabled,
            )

            self.transparent_enabled = (
                enabled
            )

            self.transparent_state_changed.emit(
                enabled
            )

            if enabled:

                self.status_changed.emit(
                    "● Click-Through ON (Press Ctrl+Alt+T to restore)"
                )

            else:

                self.status_changed.emit(
                    "● Click-Through OFF"
                )

        except Exception as exc:

            self.status_changed.emit(
                f"● Transparency error: {exc}"
            )

    # ========================================================
    # Helpers
    # ========================================================

    def _clear_audio_queue(self):

        while True:

            try:

                self.audio_queue.get_nowait()

            except queue.Empty:

                break

    # ========================================================
    # Cleanup
    # ========================================================

    def close(self):

        self.listening = False

        self.transcription_stop_event.set()

        self.audio_service.stop()

        unregister_global_hotkeys(
            self.window
        )


# ============================================================
# Main
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    window = AssistantWindow()

    controller = AppController(
        window
    )

    window.show()

    controller.apply_capture_protection(
        True,
        update_status=False,
    )

    app.aboutToQuit.connect(
        controller.close
    )

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()