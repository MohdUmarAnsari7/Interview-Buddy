from PySide6.QtCore import (
    Qt,
    QPoint,
    Signal,
    QEvent,
)

from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
)

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QFrame,
)
import os
from ctypes import wintypes

from windows_utils import (
    HOTKEY_ID_TRANSPARENT,
    HOTKEY_ID_LISTEN,
    HOTKEY_ID_PROTECT,
    HOTKEY_ID_ASK_AI,
    HOTKEY_ID_ASK_AI_ALT,
)

def load_stylesheet():

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    css_path = os.path.join(
        base_dir,
        "style.css"
    )

    try:

        with open(
            css_path,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()

    except FileNotFoundError:

        print(
            f"Warning: style.css not found at {css_path}"
        )

        return ""

class AssistantWindow(QWidget):

    # ========================================================
    # UI events
    # ========================================================

    listen_requested = Signal()
    ask_ai_requested = Signal()
    capture_toggle_requested = Signal()
    transparent_toggle_requested = Signal()

    # ========================================================
    # Constructor
    # ========================================================

    def __init__(self):
        super().__init__()

        self.drag_position = QPoint()

        self.setup_window()
        self.setup_ui()
        self.setup_style()
        self.setup_connections()

    # ========================================================
    # Window
    # ========================================================

    def setup_window(self):

        self.setWindowTitle(
            "Interview Buddy"
        )

        self.resize(
            580,
            720
        )

        self.setMinimumSize(
            440,
            580
        )

        # Standard window with stays-on-top hint
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            False
        )

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            12,
            12,
            12,
            10,
        )

        main_layout.setSpacing(9)

        # ====================================================
        # Top Header Bar
        # ====================================================

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(10)

        # Brand / Title
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(8)

        logo_label = QLabel("⚡")
        logo_label.setObjectName("headerIcon")
        brand_layout.addWidget(logo_label)

        title = QLabel("Interview Buddy")
        title.setObjectName("title")
        brand_layout.addWidget(title)

        badge = QLabel("PRO")
        badge.setObjectName("headerBadge")
        brand_layout.addWidget(badge)

        header_layout.addLayout(brand_layout)
        header_layout.addStretch()

        # Audio Status Pill
        audio_pill = QFrame()
        audio_pill.setObjectName("audioPill")
        audio_pill_layout = QHBoxLayout(audio_pill)
        audio_pill_layout.setContentsMargins(10, 4, 10, 4)
        audio_pill_layout.setSpacing(6)

        self.audio_status = QLabel("○")
        self.audio_status.setObjectName("audioDot")
        audio_pill_layout.addWidget(self.audio_status)

        self.device_label = QLabel("System Audio")
        self.device_label.setObjectName("deviceLabel")
        audio_pill_layout.addWidget(self.device_label)

        header_layout.addWidget(audio_pill)

        main_layout.addWidget(header)

        # ====================================================
        # AI Response
        # ====================================================

        answer_header = QHBoxLayout()
        answer_header.setContentsMargins(2, 4, 2, 0)

        answer_label = QLabel("AI RESPONSE")
        answer_label.setObjectName("sectionLabel")
        answer_header.addWidget(answer_label)

        answer_header.addStretch()

        self.answer_status = QLabel("Ready")
        self.answer_status.setObjectName("statusPill")
        answer_header.addWidget(self.answer_status)

        main_layout.addLayout(answer_header)

        answer_container = QFrame()
        answer_container.setObjectName("textContainer")
        answer_layout = QVBoxLayout(answer_container)
        answer_layout.setContentsMargins(10, 10, 10, 8)
        answer_layout.setSpacing(6)

        self.answer_box = QTextEdit()
        self.answer_box.setPlaceholderText(
            "AI response will stream here in real-time..."
        )
        self.answer_box.setReadOnly(True)
        self.answer_box.setMinimumHeight(140)

        answer_layout.addWidget(self.answer_box)

        answer_bottom = QHBoxLayout()
        answer_bottom.setContentsMargins(0, 2, 0, 0)
        answer_bottom.setSpacing(8)

        answer_bottom.addStretch()

        self.copy_answer_button = QPushButton("📋 Copy")
        self.copy_answer_button.setObjectName("smallActionButton")
        self.copy_answer_button.setToolTip("Copy response to clipboard")
        self.copy_answer_button.clicked.connect(self.copy_answer_to_clipboard)
        answer_bottom.addWidget(self.copy_answer_button)

        self.clear_answer_button = QPushButton("🗑 Clear")
        self.clear_answer_button.setObjectName("smallActionButton")
        self.clear_answer_button.setToolTip("Clear response")
        self.clear_answer_button.clicked.connect(self.answer_box.clear)
        answer_bottom.addWidget(self.clear_answer_button)

        answer_layout.addLayout(answer_bottom)

        main_layout.addWidget(answer_container, stretch=4)

        # ====================================================
        # Context
        # ====================================================

        context_header = QHBoxLayout()
        context_header.setContentsMargins(2, 4, 2, 0)

        context_label = QLabel("CONTEXT (OPTIONAL)")
        context_label.setObjectName("sectionLabel")
        context_header.addWidget(context_label)

        context_header.addStretch()

        context_hint = QLabel("Appended to question for reference")
        context_hint.setObjectName("hint")
        context_header.addWidget(context_hint)

        main_layout.addLayout(context_header)

        context_container = QFrame()
        context_container.setObjectName("textContainer")
        context_layout = QVBoxLayout(context_container)
        context_layout.setContentsMargins(10, 8, 10, 8)
        context_layout.setSpacing(4)

        self.context_box = QTextEdit()
        self.context_box.setPlaceholderText(
            "Paste resume bullets, company background, role requirements, or notes..."
        )
        self.context_box.setMinimumHeight(55)
        self.context_box.setMaximumHeight(95)

        context_layout.addWidget(self.context_box)

        main_layout.addWidget(context_container, stretch=1)

        # ====================================================
        # Question
        # ====================================================

        question_header = QHBoxLayout()
        question_header.setContentsMargins(2, 4, 2, 0)

        question_label = QLabel("QUESTION")
        question_label.setObjectName("sectionLabel")
        question_header.addWidget(question_label)

        question_header.addStretch()

        self.question_hint = QLabel("Speech will appear here • Ctrl+Enter to send")
        self.question_hint.setObjectName("hint")
        question_header.addWidget(self.question_hint)

        main_layout.addLayout(question_header)

        question_container = QFrame()
        question_container.setObjectName("textContainer")
        question_layout = QVBoxLayout(question_container)
        question_layout.setContentsMargins(10, 8, 10, 8)
        question_layout.setSpacing(6)

        self.question_box = QTextEdit()
        self.question_box.setPlaceholderText(
            "Transcribed speech will appear here... Type or edit, then press Ctrl+Enter to ask AI."
        )
        self.question_box.setMinimumHeight(80)

        question_layout.addWidget(self.question_box)

        question_bottom = QHBoxLayout()
        question_bottom.setContentsMargins(0, 2, 0, 0)
        question_bottom.setSpacing(8)

        clear_q_btn = QPushButton("🗑 Clear")
        clear_q_btn.setObjectName("smallActionButton")
        clear_q_btn.setToolTip("Clear question box")
        clear_q_btn.clicked.connect(self.question_box.clear)
        question_bottom.addWidget(clear_q_btn)

        question_bottom.addStretch()

        self.question_action_button = QPushButton("✦ Ask AI  [Ctrl+↵]")
        self.question_action_button.setToolTip(
            "Send question to AI (Ctrl+Enter or Ctrl+Alt+Enter)"
        )
        self.question_action_button.setObjectName("aiSmallButton")
        self.question_action_button.setFixedHeight(34)

        question_bottom.addWidget(self.question_action_button)

        question_layout.addLayout(question_bottom)

        main_layout.addWidget(question_container, stretch=2)

        # ====================================================
        # Bottom controls
        # ====================================================

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.listen_button = QPushButton(
            "🎙  Start Listening"
        )
        self.listen_button.setToolTip(
            "Start / Stop listening (Ctrl+Alt+L or Ctrl+L)"
        )
        self.listen_button.setObjectName(
            "primaryButton"
        )
        self.listen_button.setFixedHeight(42)

        controls.addWidget(
            self.listen_button,
            stretch=3
        )

        self.transparent_button = QPushButton(
            "👁  Transparent"
        )
        self.transparent_button.setToolTip(
            "Toggle click-through transparency (Ctrl+Alt+T)"
        )
        self.transparent_button.setObjectName(
            "secondaryButton"
        )
        self.transparent_button.setFixedHeight(42)

        controls.addWidget(
            self.transparent_button,
            stretch=2
        )

        main_layout.addLayout(
            controls
        )

        # ====================================================
        # Status / Footer Bar
        # ====================================================

        footer_bar = QFrame()
        footer_bar.setObjectName("footerBar")
        footer_layout = QHBoxLayout(footer_bar)
        footer_layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel(
            "● Loading Whisper model..."
        )
        self.status_label.setObjectName(
            "status"
        )
        footer_layout.addWidget(self.status_label)

        footer_layout.addStretch()

        shortcuts_hint = QLabel(
            "Ctrl+L: Listen • Ctrl+↵: Ask • Ctrl+Alt+T: Ghost"
        )
        shortcuts_hint.setObjectName("shortcutsHint")
        footer_layout.addWidget(shortcuts_hint)

        main_layout.addWidget(
            footer_bar
        )

    # ========================================================
    # Connections
    # ========================================================

    def setup_connections(self):

        self.listen_button.clicked.connect(
            self.listen_requested.emit
        )

        self.question_action_button.clicked.connect(
            self.ask_ai_requested.emit
        )


        self.transparent_button.clicked.connect(
            self.transparent_toggle_requested.emit
        )

        # Install event filter to catch shortcuts even when focused inside text boxes
        self.question_box.installEventFilter(self)
        self.context_box.installEventFilter(self)
        self.answer_box.installEventFilter(self)
        self.installEventFilter(self)

        # Local QShortcut instances for in-window activation
        for seq in (
            "Ctrl+Return",
            "Ctrl+Enter",
            "Ctrl+Alt+Return",
            "Ctrl+Alt+Enter",
            "Ctrl+Alt+A",
        ):
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(self.ask_ai_requested.emit)

        for seq in ("Ctrl+L", "Ctrl+Alt+L"):
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(self.listen_requested.emit)

        for seq in ("Ctrl+P", "Ctrl+Alt+P"):
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(self.capture_toggle_requested.emit)

        for seq in ("Ctrl+T", "Ctrl+Alt+T"):
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(self.transparent_toggle_requested.emit)

    def eventFilter(self, watched, event):

        if event.type() == QEvent.Type.KeyPress:

            key = event.key()
            modifiers = event.modifiers()
            is_ctrl = bool(modifiers & Qt.ControlModifier)
            is_alt = bool(modifiers & Qt.AltModifier)

            # Ctrl+Enter or Ctrl+Return -> Send prompt to AI
            if is_ctrl and not is_alt and key in (Qt.Key_Return, Qt.Key_Enter):
                self.ask_ai_requested.emit()
                return True

            # Ctrl+Alt+Enter or Ctrl+Alt+Return or Ctrl+Alt+A -> Send prompt
            if is_ctrl and is_alt and (key in (Qt.Key_Return, Qt.Key_Enter) or key == Qt.Key_A):
                self.ask_ai_requested.emit()
                return True

            # Ctrl+L or Ctrl+Alt+L -> Toggle listening
            if is_ctrl and key == Qt.Key_L:
                self.listen_requested.emit()
                return True

            # Ctrl+P or Ctrl+Alt+P -> Toggle protection
            if is_ctrl and key == Qt.Key_P:
                self.capture_toggle_requested.emit()
                return True

            # Ctrl+T or Ctrl+Alt+T -> Toggle transparent
            if is_ctrl and key == Qt.Key_T:
                self.transparent_toggle_requested.emit()
                return True

        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):

        key = event.key()
        modifiers = event.modifiers()
        is_ctrl = bool(modifiers & Qt.ControlModifier)
        is_alt = bool(modifiers & Qt.AltModifier)

        if is_ctrl and not is_alt and key in (Qt.Key_Return, Qt.Key_Enter):
            self.ask_ai_requested.emit()
            return

        if is_ctrl and is_alt and (key in (Qt.Key_Return, Qt.Key_Enter) or key == Qt.Key_A):
            self.ask_ai_requested.emit()
            return

        if is_ctrl and key == Qt.Key_L:
            self.listen_requested.emit()
            return

        if is_ctrl and key == Qt.Key_P:
            self.capture_toggle_requested.emit()
            return

        if is_ctrl and key == Qt.Key_T:
            self.transparent_toggle_requested.emit()
            return

        super().keyPressEvent(event)

    # ========================================================
    # UI methods
    # ========================================================

    def set_status(self, text):

        self.status_label.setText(
            text
        )

    def set_device(self, name):

        self.device_label.setText(
            name
        )

    def set_listening(self, listening):

        self.listen_button.setProperty("listening", "true" if listening else "false")
        self.listen_button.style().unpolish(self.listen_button)
        self.listen_button.style().polish(self.listen_button)

        if listening:

            self.listen_button.setText(
                "⏹  Stop Listening"
            )

        else:

            self.listen_button.setText(
                "🎙  Start Listening"
            )

    def set_audio_status(self, active):

        self.audio_status.setText(
            "●" if active else "○"
        )
        self.audio_status.setProperty("active", "true" if active else "false")
        self.audio_status.style().unpolish(self.audio_status)
        self.audio_status.style().polish(self.audio_status)

    def set_question_hint(self, text):

        self.question_hint.setText(
            text
        )

    def set_answer_status(self, text):

        self.answer_status.setText(
            text
        )

    def set_ai_button_busy(self, busy):

        self.question_action_button.setEnabled(
            not busy
        )

        self.question_action_button.setText(
            "⏳ Generating..." if busy else "✦ Ask AI  [Ctrl+↵]"
        )

    def get_context(self):

        return (
            self.context_box
            .toPlainText()
            .strip()
        )

    def get_question(self):

        return (
            self.question_box
            .toPlainText()
            .strip()
        )

    def set_answer(self, answer):

        self.answer_box.setPlainText(
            answer
        )

    def append_question(self, text):

        current = self.get_question()

        if current:

            current = (
                f"{current} {text}"
            )

        else:

            current = text

        self.question_box.setPlainText(
            current
        )

        cursor = (
            self.question_box
            .textCursor()
        )

        cursor.movePosition(
            cursor.MoveOperation.End
        )

        self.question_box.setTextCursor(
            cursor
        )

        self.question_box.ensureCursorVisible()

        self.question_hint.setText(
            "Live transcription"
        )

        self.set_status(
            "● Listening and transcribing..."
        )

    def clear_answer(self):

        self.answer_box.clear()

    def copy_answer_to_clipboard(self):

        answer = (
            self.answer_box
            .toPlainText()
            .strip()
        )

        if not answer:

            self.set_status(
                "● Nothing to copy"
            )

            return

        QApplication.clipboard().setText(
            answer
        )

        self.set_status(
            "● Answer copied"
        )

    def set_capture_state(self, enabled):

        if hasattr(self, "capture_button"):

            if enabled:

                self.capture_button.setText(
                    "🛡  Protected"
                )

            else:

                self.capture_button.setText(
                    "○  Protection Off"
                )

    def set_transparent_state(self, enabled):

        self.transparent_button.setProperty("transparent", "true" if enabled else "false")
        self.transparent_button.style().unpolish(self.transparent_button)
        self.transparent_button.style().polish(self.transparent_button)

        if enabled:

            self.transparent_button.setText(
                "👻  Click-Through Active"
            )

        else:

            self.transparent_button.setText(
                "👁  Transparent"
            )

    def nativeEvent(self, eventType, message):

        if eventType in (b"windows_generic_MSG", "windows_generic_MSG"):

            msg = wintypes.MSG.from_address(message.__int__())

            if msg.message == 0x0312:  # WM_HOTKEY

                if msg.wParam == HOTKEY_ID_TRANSPARENT:

                    self.transparent_toggle_requested.emit()

                    return True, 0

                elif msg.wParam == HOTKEY_ID_LISTEN:

                    self.listen_requested.emit()

                    return True, 0

                elif msg.wParam == HOTKEY_ID_PROTECT:

                    self.capture_toggle_requested.emit()

                    return True, 0

                elif msg.wParam in (HOTKEY_ID_ASK_AI, HOTKEY_ID_ASK_AI_ALT):

                    self.ask_ai_requested.emit()

                    return True, 0

        return super().nativeEvent(eventType, message)

    # ========================================================
    # Window dragging
    # ========================================================

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            self.drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(self, event):

        if event.buttons() & Qt.LeftButton:

            self.move(
                event.globalPosition().toPoint()
                - self.drag_position
            )

            event.accept()

    # ========================================================
    # Style
    # ========================================================
    def setup_style(self):

        stylesheet = load_stylesheet()

        self.setStyleSheet(
            stylesheet
        )

    def start_ai_stream(self):

        self.answer_box.clear()
    
        self.answer_status.setText(
            "Generating..."
        )
    
        self.question_action_button.setEnabled(
            False
        )
    
        self.question_action_button.setText(
            "⏳ Generating..."
        )
    
    
    def append_ai_response(self, text):
    
        self.answer_box.moveCursor(
            self.answer_box.textCursor().MoveOperation.End
        )
    
        self.answer_box.insertPlainText(
            text
        )
    
        self.answer_box.ensureCursorVisible()
    
    
    def finish_ai_stream(self):
    
        self.question_action_button.setEnabled(
            True
        )
    
        self.question_action_button.setText(
            "✦ Ask AI  [Ctrl+↵]"
        )
    
        self.answer_status.setText(
            "Ready"
        )
    
    
    def show_ai_error(self, error):
    
        self.question_action_button.setEnabled(
            True
        )
    
        self.question_action_button.setText(
            "✦ Ask AI  [Ctrl+↵]"
        )
    
        self.answer_status.setText(
            "Error"
        )
    
        self.answer_box.setPlainText(
            "Unable to generate response.\n\n"
            f"{error}"
        )