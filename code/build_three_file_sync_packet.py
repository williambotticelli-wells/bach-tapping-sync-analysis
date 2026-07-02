#!/usr/bin/env python3
"""Small MIDI/WAV helpers used by the Bach sync rebuild scripts."""

from __future__ import annotations

import struct
import wave
from pathlib import Path

import numpy as np


def read_varlen(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    while True:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            return value, pos


def midi_tick_to_seconds(tick: int, tempo_map: list[tuple[int, int]], tpq: int) -> float:
    if not tempo_map:
        tempo_map = [(0, 500000)]
    tempo_map = sorted(tempo_map)
    seconds = 0.0
    last_tick = tempo_map[0][0]
    tempo = tempo_map[0][1]
    if tick < last_tick:
        return tick * (tempo / 1_000_000.0) / tpq
    for next_tick, next_tempo in tempo_map[1:]:
        if tick <= next_tick:
            seconds += (tick - last_tick) * (tempo / 1_000_000.0) / tpq
            return seconds
        seconds += (next_tick - last_tick) * (tempo / 1_000_000.0) / tpq
        last_tick = next_tick
        tempo = next_tempo
    seconds += (tick - last_tick) * (tempo / 1_000_000.0) / tpq
    return seconds


def parse_midi_note_events(path: Path) -> list[tuple[float, float, int, int]]:
    """Return MIDI note events as `(start_s, end_s, pitch, velocity)` tuples."""
    data = path.read_bytes()
    if data[:4] != b"MThd":
        raise ValueError(f"Not a MIDI file: {path}")
    header_len = struct.unpack(">I", data[4:8])[0]
    _, n_tracks, division = struct.unpack(">HHH", data[8:14])
    if division >= 0x8000:
        raise ValueError("SMPTE MIDI timing is not supported")
    tpq = division
    pos = 8 + header_len
    tempo_events: list[tuple[int, int]] = [(0, 500000)]
    raw_events: list[tuple[int, str, int, int]] = []

    for _ in range(n_tracks):
        if data[pos:pos + 4] != b"MTrk":
            raise ValueError("Missing MTrk header")
        track_len = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        pos += 8
        end = pos + track_len
        tick = 0
        running_status: int | None = None
        while pos < end:
            delta, pos = read_varlen(data, pos)
            tick += delta
            status = data[pos]
            if status & 0x80:
                pos += 1
                running_status = status
            elif running_status is not None:
                status = running_status
            else:
                raise ValueError("MIDI running status without prior status")

            if status == 0xFF:
                meta_type = data[pos]
                pos += 1
                length, pos = read_varlen(data, pos)
                payload = data[pos:pos + length]
                pos += length
                if meta_type == 0x51 and length == 3:
                    tempo_events.append((tick, int.from_bytes(payload, "big")))
                continue
            if status in (0xF0, 0xF7):
                length, pos = read_varlen(data, pos)
                pos += length
                continue

            event_type = status & 0xF0
            if event_type in (0xC0, 0xD0):
                pos += 1
                continue
            pitch, velocity = data[pos], data[pos + 1]
            pos += 2
            if event_type == 0x90 and velocity > 0:
                raw_events.append((tick, "on", pitch, velocity))
            elif event_type == 0x80 or (event_type == 0x90 and velocity == 0):
                raw_events.append((tick, "off", pitch, velocity))
        pos = end

    tempo_events = sorted(set(tempo_events))
    active: dict[int, list[tuple[int, int]]] = {}
    notes: list[tuple[float, float, int, int]] = []
    for tick, kind, pitch, velocity in sorted(raw_events, key=lambda item: (item[0], item[1] == "on")):
        if kind == "on":
            active.setdefault(pitch, []).append((tick, velocity))
        else:
            starts = active.get(pitch)
            if starts:
                start_tick, start_velocity = starts.pop(0)
                start_s = midi_tick_to_seconds(start_tick, tempo_events, tpq)
                end_s = midi_tick_to_seconds(max(tick, start_tick + 1), tempo_events, tpq)
                notes.append((start_s, end_s, pitch, start_velocity))
    for pitch, starts in active.items():
        for start_tick, start_velocity in starts:
            start_s = midi_tick_to_seconds(start_tick, tempo_events, tpq)
            notes.append((start_s, start_s + 0.75, pitch, start_velocity))
    return sorted(notes)


def piano_tone(freq: float, duration_s: float, sr: int, velocity: int) -> np.ndarray:
    n = max(1, int(round(duration_s * sr)))
    t = np.arange(n) / sr
    vel = max(0.15, min(1.0, velocity / 110.0))
    attack = max(1, int(0.008 * sr))
    decay = np.exp(-3.4 * t / max(duration_s, 0.2))
    env = decay
    env[:attack] *= np.linspace(0.0, 1.0, attack)
    tone = (
        np.sin(2 * np.pi * freq * t)
        + 0.45 * np.sin(2 * np.pi * 2 * freq * t)
        + 0.22 * np.sin(2 * np.pi * 3 * freq * t)
        + 0.10 * np.sin(2 * np.pi * 4 * freq * t)
    )
    return 0.11 * vel * env * tone


def render_midi_piano(
    midi_path: Path,
    out_path: Path,
    total_duration_s: float,
    align_first_note_to_s: float,
    sr: int = 44100,
) -> tuple[bool, str]:
    try:
        notes = parse_midi_note_events(midi_path)
    except Exception as exc:
        return False, str(exc)
    if not notes:
        return False, "no note events"
    first_note_s = min(note[0] for note in notes)
    total_samples = max(1, int(round(total_duration_s * sr)))
    audio = np.zeros(total_samples, dtype=np.float64)
    for start_s, end_s, pitch, velocity in notes:
        aligned_start = (start_s - first_note_s) + align_first_note_to_s
        if aligned_start >= total_duration_s:
            continue
        note_duration = min(max(end_s - start_s, 0.12), 4.0)
        idx = int(round(aligned_start * sr))
        if idx < 0:
            continue
        freq = 440.0 * (2 ** ((pitch - 69) / 12))
        tone = piano_tone(freq, note_duration, sr, velocity)
        end_idx = min(total_samples, idx + len(tone))
        if end_idx > idx:
            audio[idx:end_idx] += tone[: end_idx - idx]
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = 0.92 * audio / peak
    stereo = np.column_stack([audio, audio])
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return True, ""


def wav_duration(path: str | Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / wf.getframerate()
