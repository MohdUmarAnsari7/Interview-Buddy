import json
import time

import requests

try:
    from ollama import chat as ollama_chat
except ImportError:
    ollama_chat = None


class AIClient:
    """
    AI client for Interview Helper.

    Supports:
    - OpenAI-compatible cloud endpoints (NVIDIA NIM, OpenAI, etc.)
    - Local Ollama models
    - Streaming responses with latency diagnostics
    """

    def __init__(
        self,
        api_key,
        model,
        base_url,
        temperature=1,
        timeout=120,
    ):
        self.api_key = (api_key or "").strip()
        self.model = model
        self.base_url = (base_url or "").rstrip("/")
        self.temperature = temperature
        self.timeout = timeout

    # ========================================================
    # Backend detection
    # ========================================================

    def _is_ollama_backend(self):
        """
        Detect if configuration targets local Ollama.
        """
        if "localhost:11434" in self.base_url or "127.0.0.1:11434" in self.base_url:
            return True
        if not self.api_key and "api.nvidia.com" not in self.base_url:
            return True
        return False

    # ========================================================
    # Messages
    # ========================================================

    def _build_messages(self, prompt):
        return [
            {
                "role": "system",
                "content": (
                    "You are a live interview assistant. "
                    "Answer clearly, directly, and concisely without preamble or internal monologue. "
                    "Keep answers brief, sharp, and easy to speak."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

    # ========================================================
    # Streaming entrypoint
    # ========================================================

    def stream_answer(
        self,
        prompt,
        on_chunk,
    ):
        if not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        if self._is_ollama_backend():
            self._stream_ollama(prompt, on_chunk)
        else:
            self._stream_openai_compatible(prompt, on_chunk)

    # ========================================================
    # NVIDIA / OpenAI-compatible streaming
    # ========================================================

    def _stream_openai_compatible(
        self,
        prompt,
        on_chunk,
    ):
        start_time = time.perf_counter()

        print(f"[AI] Sending request to {self.base_url}...")
        print(f"[AI] Model: {self.model}")

        url = self.base_url
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": self._build_messages(prompt),
            "stream": True,
            "temperature": self.temperature,
            "chat_template_kwargs": {"thinking": False},
        }

        first_token_time = None
        total_chunks = 0

        try:
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=self.timeout,
            )

            # Fallback if an API provider rejects chat_template_kwargs
            if res.status_code == 400 and "chat_template_kwargs" in res.text:
                payload.pop("chat_template_kwargs", None)
                res = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                )

            connection_time = (
                time.perf_counter() - start_time
            )

            print(
                f"[AI] API stream connected in {connection_time:.2f}s "
                f"(Status: {res.status_code})"
            )

            if res.status_code != 200:
                raise RuntimeError(
                    f"API request failed ({res.status_code}): {res.text}"
                )

            for line in res.iter_lines():
                if not line:
                    continue

                decoded = line.decode("utf-8")

                if decoded.startswith("data: "):
                    data_str = decoded[6:].strip()

                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")

                        if content:
                            total_chunks += 1

                            if first_token_time is None:
                                first_token_time = (
                                    time.perf_counter()
                                    - start_time
                                )
                                print(
                                    "\n[AI] Time to first answer token: "
                                    f"{first_token_time:.2f}s"
                                )

                            on_chunk(content)

                    except json.JSONDecodeError:
                        continue

            total_time = (
                time.perf_counter() - start_time
            )

            print(
                f"\n[AI] Total generation time: {total_time:.2f}s"
            )
            print(
                f"[AI] Total answer chunks: {total_chunks}"
            )

            if total_chunks == 0:
                print(
                    "[AI] WARNING: No answer chunks received."
                )

        except Exception as exc:
            total_time = (
                time.perf_counter() - start_time
            )
            print(
                f"[AI] API request failed after {total_time:.2f}s"
            )
            raise RuntimeError(
                f"AI API error: {exc}"
            ) from exc

    # ========================================================
    # Ollama streaming
    # ========================================================

    def _stream_ollama(
        self,
        prompt,
        on_chunk,
    ):
        if ollama_chat is None:
            raise RuntimeError(
                "The 'ollama' Python library is not installed."
            )

        start_time = time.perf_counter()

        print("[AI] Sending request to Ollama...")
        print(f"[AI] Model: {self.model}")

        first_token_time = None
        total_chunks = 0

        try:
            stream = ollama_chat(
                model=self.model,
                messages=self._build_messages(prompt),
                stream=True,
                think=False,
                options={
                    "temperature": self.temperature,
                    "num_predict": 500,
                },
            )

            connection_time = (
                time.perf_counter() - start_time
            )

            print(
                "[AI] Ollama stream connected in "
                f"{connection_time:.2f}s"
            )

            for chunk in stream:
                content = chunk.message.content
                if not content:
                    continue

                total_chunks += 1

                if first_token_time is None:
                    first_token_time = (
                        time.perf_counter()
                        - start_time
                    )
                    print(
                        "\n[AI] Time to first answer token: "
                        f"{first_token_time:.2f}s"
                    )

                on_chunk(content)

            total_time = (
                time.perf_counter() - start_time
            )

            print(
                f"\n[AI] Total generation time: {total_time:.2f}s"
            )
            print(
                f"[AI] Total answer chunks: {total_chunks}"
            )

            if total_chunks == 0:
                print(
                    "[AI] WARNING: No answer chunks received."
                )

        except Exception as exc:
            total_time = (
                time.perf_counter() - start_time
            )
            print(
                f"[AI] Ollama request failed after {total_time:.2f}s"
            )
            raise RuntimeError(
                f"Ollama error: {exc}"
            ) from exc