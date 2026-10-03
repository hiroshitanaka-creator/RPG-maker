#!/usr/bin/env python3
"""Original deterministic dry repair tap; Python standard library only.

Run in any directory; outputs are written beside this script.
No external audio, sample recordings, musical work, voice, or trained audio
generator is used. The synthesis contains one onset and no delay/reverb.
"""
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import sys
import wave
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
RATE = 44100
DURATION = 0.480
ONSET = 0.005
ATTACK = 0.0015
FADE_OUT = 0.025
TARGET_PEAK_DBFS = -15.0
SEED = 20261003
# Frequency Hz, amplitude, exponential decay time seconds, phase radians.
MODES = [
    (760.0, 0.58, 0.070, 0.00),
    (1387.0, 0.29, 0.052, 0.37),
    (2189.0, 0.12, 0.036, 0.81),
    (3310.0, 0.035, 0.021, 1.20),
]
NOISE_CUTOFF_HZ = 2400.0
NOISE_AMP = 0.065
NOISE_DECAY = 0.006
BODY_HZ = 180.0
BODY_AMP = 0.085
BODY_DECAY = 0.013

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    rng = random.Random(SEED)
    low_noise = 0.0
    alpha = 1.0 - math.exp(-2.0 * math.pi * NOISE_CUTOFF_HZ / RATE)
    floats = []
    for index in range(round(RATE * DURATION)):
        t = index / RATE
        elapsed = t - ONSET
        if elapsed < 0:
            floats.append(0.0)
            continue
        # Raised-cosine attack softens the impulse without adding another hit.
        attack = 0.5 - 0.5 * math.cos(math.pi * min(elapsed / ATTACK, 1.0))
        ring = sum(amplitude * math.exp(-elapsed / decay) *
                   math.sin(2.0 * math.pi * frequency * elapsed + phase)
                   for frequency, amplitude, decay, phase in MODES)
        low_noise += alpha * (rng.uniform(-1.0, 1.0) - low_noise)
        contact = NOISE_AMP * low_noise * math.exp(-elapsed / NOISE_DECAY)
        body = BODY_AMP * math.sin(2.0 * math.pi * BODY_HZ * elapsed) * math.exp(-elapsed / BODY_DECAY)
        fade_start = DURATION - FADE_OUT
        fade = 1.0 if t < fade_start else 0.5 + 0.5 * math.cos(math.pi * min((t - fade_start) / FADE_OUT, 1.0))
        floats.append((ring + contact + body) * attack * fade)
    # Keep exact zero endpoints and a modest peak with ample clipping headroom.
    floats[0] = floats[-1] = 0.0
    gain = 10.0 ** (TARGET_PEAK_DBFS / 20.0) / max(map(abs, floats))
    pcm = [int(round(value * gain * 32767.0)) for value in floats]
    output = ROOT / "repair-tap.wav"
    with wave.open(str(output), "wb") as handle:
        handle.setparams((1, 2, RATE, len(pcm), "NONE", "not compressed"))
        handle.writeframes(struct.pack("<" + "h" * len(pcm), *pcm))
    # Re-open the encoded artifact so verification is based on delivered bytes.
    with wave.open(str(output), "rb") as handle:
        channels = handle.getnchannels()
        bits = handle.getsampwidth() * 8
        rate = handle.getframerate()
        frames = handle.getnframes()
        compression = handle.getcomptype()
        decoded = struct.unpack("<" + "h" * frames, handle.readframes(frames))
    peak_int = max(map(abs, decoded))
    peak = peak_int / 32768.0
    rms = math.sqrt(sum(value * value for value in decoded) / len(decoded)) / 32768.0
    clips = sum(value in (-32768, 32767) for value in decoded)
    validation = {
        "container": "RIFF WAVE", "encoding": "PCM signed 16-bit little-endian",
        "channels": channels, "sample_rate_hz": rate, "bits_per_sample": bits,
        "frames": frames, "duration_seconds": frames / rate,
        "peak_sample_absolute": peak_int, "peak_dbfs": 20.0 * math.log10(peak),
        "rms_dbfs": 20.0 * math.log10(rms), "clipped_sample_count": clips,
        "dc_offset_normalized": sum(decoded) / len(decoded) / 32768.0,
        "first_sample": decoded[0], "last_sample": decoded[-1],
        "file_bytes": output.stat().st_size,
        "listened": False,
        "listening_limitation": "No audio audition/listening tool was available. Perceptual quality and in-game mix are unverified; waveform metrics do not establish these.",
    }
    assert channels == 1 and bits == 16 and rate == RATE and compression == "NONE"
    assert 0.2 <= frames / rate <= 0.8 and clips == 0 and peak < 0.20
    assert decoded[0] == decoded[-1] == 0
    provenance = {
        "asset": "repair-tap.wav", "asset_type": "original synthesized nonvoice one-shot sound effect",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "A modest, dry, single small-hammer-on-metal repair tap candidate for an RPG workshop action.",
        "method": "Deterministic additive damped inharmonic resonances with low-pass seeded noise contact and a damped low body mode; raised-cosine 1.5 ms attack; 25 ms end fade; peak normalization; direct 16-bit PCM encoding.",
        "external_sources": [], "external_samples_used": False,
        "source_origin": "New mathematical synthesis made for this task; no sampled or copied recording or musical work.",
        "speech": False, "music": False, "loop": False, "reverb_or_delay": False,
        "seed": SEED,
        "parameters": {
            "sample_rate_hz": RATE, "duration_seconds": DURATION,
            "onset_seconds": ONSET, "attack_seconds": ATTACK, "end_fade_seconds": FADE_OUT,
            "target_peak_dbfs": TARGET_PEAK_DBFS, "modes_hz_amplitude_decay_seconds_phase_radians": MODES,
            "noise_cutoff_hz": NOISE_CUTOFF_HZ, "noise_amplitude": NOISE_AMP,
            "noise_decay_seconds": NOISE_DECAY, "body_hz": BODY_HZ,
            "body_amplitude": BODY_AMP, "body_decay_seconds": BODY_DECAY,
            "normalization_gain": gain,
        },
        "original_sha256": sha256(output),
        "generation_code_file": Path(__file__).name,
        "generation_code_sha256": sha256(Path(__file__)),
        "python_version": sys.version,
        "validation": validation,
    }
    (ROOT / "repair-tap.provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(provenance, indent=2))

if __name__ == "__main__":
    main()
