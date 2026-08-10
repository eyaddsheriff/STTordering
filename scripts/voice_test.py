"""Manual test client: talk to the voice-ordering API through your mic/speakers.

Run the server first (uvicorn app.main:app), then:
    .venv/Scripts/python.exe scripts/voice_test.py

Windows-only (uses msvcrt for keypress detection): Enter starts/stops recording, Esc quits.
"""

import io
import json

import msvcrt
import numpy as np
import requests
import sounddevice as sd
import soundfile as sf

API_URL = "http://127.0.0.1:8000"
SAMPLE_RATE = 16000
_ENTER = b"\r"
_ESC = b"\x1b"


def _wait_for_key(*valid_keys: bytes) -> bytes:
    while True:
        key = msvcrt.getch()
        if key in valid_keys:
            return key


def record_until_enter() -> np.ndarray | None:
    """Returns None if the user pressed Esc instead of recording."""
    print("Press Enter to start recording, Esc to quit...")
    if _wait_for_key(_ENTER, _ESC) == _ESC:
        return None

    print("Recording... press Enter to stop, Esc to cancel.")
    frames: list[np.ndarray] = []

    def callback(indata, _frame_count, _time_info, _status) -> None:
        frames.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback):
        key = _wait_for_key(_ENTER, _ESC)

    if key == _ESC:
        return None

    return np.concatenate(frames, axis=0)


def play_audio(audio_bytes: bytes) -> None:
    data, samplerate = sf.read(io.BytesIO(audio_bytes), dtype="float32")
    sd.play(data, samplerate)
    sd.wait()


def main() -> None:
    conversation: list[dict] = []
    print("Voice ordering test client. Esc to quit.\n")

    while True:
        audio = record_until_enter()
        if audio is None:
            print("Bye.")
            return

        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio, SAMPLE_RATE, format="WAV")
        wav_buffer.seek(0)

        response = requests.post(
            f"{API_URL}/api/voice-order",
            files={"audio": ("order.wav", wav_buffer, "audio/wav")},
            data={"conversation": json.dumps(conversation)},
        )
        response.raise_for_status()
        result = response.json()
        conversation = result["conversation"]

        print(f"You said:   {result['transcript']}")
        print(f"Intent:     {result['intent']}")
        print(f"Order:      {result['order_items']}")
        if result["invalid_items"]:
            print(f"Rejected:   {result['invalid_items']}")
        print(f"Assistant:  {result['reply_text']}\n")

        speak_response = requests.post(f"{API_URL}/api/speak", data={"text": result["reply_text"]})
        speak_response.raise_for_status()
        play_audio(speak_response.content)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye.")
