"""Music, sound effects and voice lines through OpenRouter.

  music / jingles / sfx -> google/lyria-3-pro-preview and google/lyria-3-clip-preview (streamed MP3)
  voices                -> google/gemini-3.8-flash-tts (raw 24 kHz PCM, wrapped as WAV)

The API key is read from the OPENROUTER_API_KEY environment variable and never written anywhere.
Raw downloads are cached in tools/_audio_tmp/raw so re-running never pays twice (use --force to regenerate).

  python gen_audio.py sfx sword_swing sword_hit      # specific items
  python gen_audio.py music                          # a whole group
  python gen_audio.py voices
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "tools" / "_audio_tmp" / "raw"
OUT = ROOT / "assets" / "audio"
LOG = ROOT / "tools" / "build" / "audio_cost.log"
API = "https://openrouter.ai/api/v1"
PRO = "google/lyria-3-pro-preview"
CLIP = "google/lyria-3-clip-preview"
TTS = "google/gemini-3.8-flash-tts"

# ---------------------------------------------------------------- manifest
MUSIC = {  # name -> prompt  (Pro model, full tracks, loop in-game)
    "village": "Cozy village theme for a 2D top-down pixel-art fantasy game. Warm acoustic guitar and pizzicato strings, "
               "a soft wooden flute melody, gentle hand percussion, major key, around 90 bpm, calm and homely. "
               "Instrumental only, no vocals, about 60 seconds, ends in a way that loops smoothly back to the start.",
    "mistwood": "Mysterious forest exploration theme for a 2D top-down pixel-art adventure. Music box, soft synth pads, "
                "hollow flute, light plucked harp and low strings, a hint of tension but still whimsical, around 100 bpm. "
                "Instrumental only, no vocals, about 60 seconds, loops smoothly.",
    "ruin": "Slow atmospheric ambient music for exploring an ancient stone ruin in a 2D adventure game. Deep warm synth drones, "
            "sparse reverberant piano notes, soft airy pads, around 60 bpm, mysterious and eerie but gentle. "
            "Instrumental only, about 60 seconds, loops smoothly.",
}
JINGLE_CUT = {"shrine_lit": (8.0, 1.5), "game_over": (5.2, 0.6)}   # (seconds kept, fade-out): the model ignores length requests
JINGLES = {  # Clip model, short stingers
    "shrine_lit": "A short triumphant magical fanfare, about 6 seconds: glittering bells, harp glissando, warm brass swell, "
                  "resolving to a bright major chord. Instrumental, ends cleanly.",
    "game_over": "A short sad descending melody played on a solo piano, about 5 seconds, gentle and wistful, ends cleanly.",
}
SFX = {  # Clip model; each is trimmed to the real sound afterwards. (max seconds to keep)
    "sword_swing": ("Sound effect only, no music, no melody: a single quick sword swish through the air, whoosh, 0.4 seconds.", 0.6),
    "sword_hit": ("Sound effect only, no music, no melody: a sharp short sword impact hit on a soft creature, thwack, 0.3 seconds.", 0.5),
    "enemy_die": ("Sound effect only, no music, no melody: a small magical mist creature dissipating, soft airy poof with a tiny descending chime, 0.8 seconds.", 1.2),
    "player_hurt": ("Sound effect only, no music, no melody: a short retro video game damage hurt sound, quick 8-bit style descending blip, 0.4 seconds.", 0.6),
    "pickup_shard": ("Sound effect only, no music, no melody: a bright magical crystal pickup chime, two quick rising sparkle notes, 0.5 seconds.", 0.8),
    "pickup_heart": ("Sound effect only, no music, no melody: a soft warm healing chime, gentle rising three-note sparkle, 0.7 seconds.", 1.0),
    "bush_cut": ("Sound effect only, no music, no melody: leaves rustling and a quick snip as a bush is cut, 0.4 seconds.", 0.6),
    "pot_break": ("Sound effect only, no music, no melody: a clay pot shattering into pieces on the ground, 0.6 seconds.", 0.9),
    "chest_open": ("Sound effect only, no music, no melody: a wooden treasure chest creaking open followed by a magical sparkle, 1.2 seconds.", 1.6),
    "shrine_light": ("Sound effect only, no music, no melody: a magic lantern igniting, a whoosh of flame followed by a warm shimmering chime, 1.5 seconds.", 2.2),
    "ui_blip": ("Sound effect only, no music, no melody: a tiny soft retro text blip, one very short high bleep, 0.05 seconds.", 0.12),
    "slime_hop": ("Sound effect only, no music, no melody: a squishy cartoon slime boing hop, 0.4 seconds.", 0.6),
    "bat_flap": ("Sound effect only, no music, no melody: soft quick leathery bat wing flutter, 0.5 seconds.", 0.7),
}

# (character, voice, character note (not sent to the API), [(key, text), ...])
VOICES = {
    "elder": ("Gacrux", "Say in the warm, slow, slightly raspy voice of a wise old village elder",
              [("a0", "The lanterns have gone out, and the night-mist creeps closer every evening."),
               ("a1", "Take your sword, lantern-keeper. Slimes and bats now roam the Mistwood to the east."),
               ("a2", "The first shrine lies in the old ruin to the north. Relight it!"),
               ("b0", "Look, the mist is thinning already! You have done well, lantern-keeper.")]),
    "shopkeeper": ("Puck", "Say in a cheerful, upbeat, friendly shopkeeper's voice",
                   [("a0", "Welcome! I have nothing to sell just yet."),
                    ("a1", "But bring me ember shards and we shall talk business!"),
                    ("b0", "Business is picking up now the lanterns are back. Thank you!")]),
    "child": ("Leda", "Say in a bright, excited, youthful child's voice",
              [("a0", "I saw a glow in the ruin last night. Honest!"),
               ("a1", "Try hitting the bushes and pots. Sometimes they hide hearts."),
               ("b0", "The mist is going away! Can I carry the lantern next time?")]),
}


# ---------------------------------------------------------------- api
def _key() -> str:
    k = os.environ.get("OPENROUTER_API_KEY", "")
    if not k:
        sys.exit("Set OPENROUTER_API_KEY in the environment first.")
    return k


def _log(what: str, cost) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{what}\t{cost}\n")


def lyria(model: str, prompt: str, dest: Path) -> bool:
    """Stream a Lyria generation and save the returned MP3. Returns False if no audio came back."""
    body = {"model": model, "modalities": ["text", "audio"], "stream": True,
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(f"{API}/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + _key(), "Content-Type": "application/json"})
    audio, cost, text = [], None, ""
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            for raw in r:
                line = raw.decode().strip()
                if not line.startswith("data:") or line.endswith("[DONE]"):
                    continue
                ev = json.loads(line[5:])
                if "error" in ev:
                    print("  api error:", ev["error"])
                    return False
                for ch in ev.get("choices", []):
                    d = ch.get("delta", {})
                    if d.get("audio", {}).get("data"):
                        audio.append(d["audio"]["data"])
                    text += d.get("content") or ""
                if ev.get("usage"):
                    cost = ev["usage"].get("cost")
    except urllib.error.HTTPError as e:
        print("  http", e.code, e.read()[:300])
        return False
    _log(f"{model} {dest.name}", cost)
    if not audio:
        print("  no audio returned; text was:", text[:200])
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(base64.b64decode("".join(audio)))
    print(f"  saved {dest.name} ({dest.stat().st_size // 1024} KB, cost {cost})")
    return True


def speak(text: str, voice: str, dest: Path) -> bool:
    body = {"model": TTS, "input": text, "voice": voice, "response_format": "pcm"}
    req = urllib.request.Request(f"{API}/audio/speech", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + _key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            pcm = r.read()
    except urllib.error.HTTPError as e:
        print("  http", e.code, e.read()[:300])
        return False
    _log(f"{TTS} {dest.name}", "see account")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dest), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(pcm)
    print(f"  saved {dest.name} ({len(pcm) / 48000:.1f}s)")
    return True


# ---------------------------------------------------------------- post-processing
def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    return float(out.stdout.strip() or 0)


def _decode(raw: Path):
    import numpy as np
    out = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(raw), "-f", "f32le", "-ac", "2", "-ar", "44100", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").reshape(-1, 2).copy()


def _encode(x, dest: Path, loudness: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ac", "2", "-ar", "44100", "-i", "-",
                    "-af", f"loudnorm=I={loudness}:TP=-1.5:LRA=11", "-c:a", "libvorbis", "-q:a", "5", str(dest)],
                   input=x.astype("<f4").tobytes(), check=True)


def finish_music(raw: Path, dest: Path, loudness: int = -16, xfade: float = 4.0) -> None:
    """Trim the silent tail, then crossfade the ending into the beginning so the track loops without a gap."""
    import numpy as np
    sr = 44100
    x = _decode(raw)
    win = sr // 2
    rms = [20 * np.log10(max(1e-6, float(np.sqrt((x[i:i + win] ** 2).mean())))) for i in range(0, len(x) - win, win)]
    last = max(i for i, v in enumerate(rms) if v > -50)
    x = x[: (last + 1) * win]
    f = int(xfade * sr)
    t = np.linspace(0, 1, f)[:, None]
    seam = x[-f:] * np.cos(t * np.pi / 2) + x[:f] * np.sin(t * np.pi / 2)
    _encode(np.concatenate([x[f:-f], seam]), dest, loudness)


def finish_jingle(raw: Path, dest: Path, keep: float, fade: float, loudness: int = -16) -> None:
    """Keep the first `keep` seconds (the first musical phrase) with a fade-out."""
    import numpy as np
    sr = 44100
    x = _decode(raw)[: int(keep * sr)]
    n = int(fade * sr)
    x[-n:] *= np.linspace(1, 0, n)[:, None]
    _encode(x, dest, loudness)


def finish_sfx(raw: Path, dest: Path, max_len: float) -> None:
    """Strip leading silence, keep the first max_len seconds, short fade-out, normalise, 44.1 kHz mono WAV."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    af = (f"silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,"
          f"atrim=0:{max_len},afade=t=out:st={max(0.0, max_len - 0.08):.2f}:d=0.08,"
          f"loudnorm=I=-18:TP=-2:LRA=7")
    ffmpeg("-i", str(raw), "-vn", "-af", af, "-ar", "44100", "-ac", "1", str(dest))


# ---------------------------------------------------------------- driver
def run(group: str, names: list[str], force: bool) -> None:
    if group == "voices":
        for who, (voice, direction, lines) in VOICES.items():
            for key, text in lines:
                name = f"{who}_{key}"
                if names and who not in names and name not in names:
                    continue
                dest = OUT / "voice" / f"{name}.wav"
                if dest.exists() and not force:
                    continue
                print("voice", name)
                speak(text, voice, dest)   # no inline direction: the model reads those out loud
        return
    table = {"music": MUSIC, "jingles": JINGLES, "sfx": SFX}[group]
    for name, spec in table.items():
        if names and name not in names:
            continue
        prompt, max_len = (spec if isinstance(spec, tuple) else (spec, None))
        raw = RAW / f"{group}_{name}.mp3"
        if force or not raw.exists():
            print(group, name)
            if not lyria(PRO if group == "music" else CLIP, prompt, raw):
                continue
        if group == "music":
            finish_music(raw, OUT / "music" / f"{name}.ogg")
        elif group == "jingles":
            finish_jingle(raw, OUT / "music" / f"{name}.ogg", *JINGLE_CUT[name])
        else:
            finish_sfx(raw, OUT / "sfx" / f"{name}.wav", max_len)
        print(f"  -> {name} ready")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or args[0] not in ("music", "jingles", "sfx", "voices"):
        sys.exit(__doc__)
    run(args[0], args[1:], "--force" in sys.argv)
