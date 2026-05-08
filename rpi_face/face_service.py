import math
import os
import random
import sys
import threading
import time

import pygame
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# ── Display ────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 480, 320
FPS = 30

# ── Colors ─────────────────────────────────────────────────────────────
BG    = (10,  10,  10)
CYAN  = (0,  220, 255)
WHITE = (220, 220, 220)
GRAY  = (80,  80,  80)
BLUE  = (60,  80, 220)

# ── Eye geometry ───────────────────────────────────────────────────────
EYE_L  = (155, 148)
EYE_R  = (325, 148)
EYE_W  = 38
EYE_H  = 38

# ── Shared state ────────────────────────────────────────────────────────
_lock       = threading.Lock()
_face_state = {"state": "idle", "text": ""}

# ── API ────────────────────────────────────────────────────────────────
api = FastAPI(title="Atlas Face")


class StateUpdate(BaseModel):
    state: str  # idle | listening | echo | thinking | speaking
    text: str = ""


@api.post("/face/state")
def set_state(u: StateUpdate):
    with _lock:
        _face_state["state"] = u.state
        _face_state["text"]  = u.text
    return {"ok": True}


@api.get("/face/state")
def get_state():
    with _lock:
        return dict(_face_state)


def _run_api():
    port = int(os.getenv("FACE_PORT", "8004"))
    uvicorn.run(api, host="0.0.0.0", port=port, log_level="warning")


# ── Helpers ────────────────────────────────────────────────────────────
def _draw_eye(surf, center, rx, ry, color=CYAN):
    if ry < 1:
        return
    rect = pygame.Rect(center[0] - rx, center[1] - ry, rx * 2, ry * 2)
    pygame.draw.ellipse(surf, color, rect)


def _wrap_text(text, font, max_width):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if font.size(test)[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


# ── Main loop ──────────────────────────────────────────────────────────
def main():
    # Pygame 2 uses SDL2, which usually auto-detects kmsdrm or x11.
    # If running headless, ensure you export DISPLAY=:0

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Atlas Face")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    font_sm = pygame.font.SysFont("monospace", 16)
    font_md = pygame.font.SysFont("monospace", 22)

    # Blink
    BLINK_DUR  = 0.14
    blink_t    = 0.0
    blink_next = time.time() + random.uniform(2.5, 5.0)
    blink_ry   = float(EYE_H)

    # Listening pulse ring
    pulse_r = 0.0

    # Listening waveform bars
    wave_bars = [random.uniform(0.2, 0.6) for _ in range(10)]
    wave_t    = 0.0

    # Thinking dots
    dot_phase = 0.0

    # Speaking mouth
    speak_phase  = 0.0
    speak_mouth_h = 2.0

    threading.Thread(target=_run_api, daemon=True).start()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        with _lock:
            state = _face_state["state"]
            text  = _face_state["text"]

        screen.fill(BG)
        now = time.time()

        # ── Blink (idle + echo + speaking) ────────────────────────────
        if state in ("idle", "echo", "speaking"):
            if now >= blink_next and blink_t == 0.0:
                blink_t = BLINK_DUR
            if blink_t > 0.0:
                blink_t = max(0.0, blink_t - dt)
                p = 1.0 - (blink_t / BLINK_DUR)   # 0 → 1
                half = 0.5
                if p < half:
                    blink_ry = EYE_H * (1.0 - p / half)
                else:
                    blink_ry = EYE_H * ((p - half) / half)
                if blink_t == 0.0:
                    blink_ry = float(EYE_H)
                    blink_next = now + random.uniform(2.5, 5.0)
            else:
                blink_ry = float(EYE_H)
        else:
            blink_t  = 0.0
            blink_ry = float(EYE_H)

        # ── Idle ───────────────────────────────────────────────────────
        if state == "idle":
            _draw_eye(screen, EYE_L, EYE_W, int(blink_ry))
            _draw_eye(screen, EYE_R, EYE_W, int(blink_ry))
            pygame.draw.arc(
                screen, CYAN,
                pygame.Rect(195, 212, 90, 32),
                math.pi, 2 * math.pi, 3,
            )

        # ── Listening ──────────────────────────────────────────────────
        elif state == "listening":
            _draw_eye(screen, EYE_L, EYE_W + 6, EYE_H + 6)
            _draw_eye(screen, EYE_R, EYE_W + 6, EYE_H + 6)

            # Single slow ring rising from below
            pulse_r = (pulse_r + dt * 60) % 110
            alpha = max(0.0, 1.0 - pulse_r / 110)
            pc = tuple(int(v * alpha) for v in CYAN)
            if pulse_r > 2 and any(pc):
                pygame.draw.circle(screen, pc, (WIDTH // 2, 270), int(pulse_r + 10), 2)

            # Smooth waveform — 10 bars, gentle movement
            wave_t += dt
            if wave_t > 0.1:
                wave_bars = [
                    max(0.1, min(1.0, b + random.uniform(-0.15, 0.15)))
                    for b in wave_bars[:10]
                ] + wave_bars[10:]
                wave_t = 0.0
            bar_w   = 18
            gap     = 6
            n_bars  = 10
            total_w = n_bars * (bar_w + gap)
            sx      = (WIDTH - total_w) // 2
            for i, h in enumerate(wave_bars[:n_bars]):
                bh = int(h * 28)
                pygame.draw.rect(
                    screen, CYAN,
                    (sx + i * (bar_w + gap), 300 - bh, bar_w, bh),
                )

        # ── Echo ───────────────────────────────────────────────────────
        elif state == "echo":
            _draw_eye(screen, EYE_L, EYE_W, int(blink_ry))
            _draw_eye(screen, EYE_R, EYE_W, int(blink_ry))

            lbl = font_sm.render("I HEARD:", True, CYAN)
            screen.blit(lbl, (WIDTH // 2 - lbl.get_width() // 2, 200))
            pygame.draw.line(screen, GRAY, (20, 220), (WIDTH - 20, 220), 1)

            lines = _wrap_text(text or "...", font_md, WIDTH - 40)[:3]
            for i, line in enumerate(lines):
                surf = font_md.render(line, True, WHITE)
                screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, 228 + i * 27))

        # ── Thinking ───────────────────────────────────────────────────
        elif state == "thinking":
            # Squinted eyes
            _draw_eye(screen, EYE_L, EYE_W, max(5, EYE_H // 4))
            _draw_eye(screen, EYE_R, EYE_W, max(5, EYE_H // 4))

            lbl = font_sm.render("THINKING", True, BLUE)
            screen.blit(lbl, (WIDTH // 2 - lbl.get_width() // 2, 212))

            dot_phase = (dot_phase + dt * 5.0) % (2 * math.pi)
            for i in range(3):
                offset = math.sin(dot_phase + i * (2 * math.pi / 3))
                y = int(262 + offset * 14)
                pygame.draw.circle(screen, BLUE, (WIDTH // 2 - 32 + i * 32, y), 9)

        # ── Speaking ───────────────────────────────────────────────────
        elif state == "speaking":
            # Normal eyes with blink — slightly wider for engagement
            _draw_eye(screen, EYE_L, EYE_W + 3, int(blink_ry) + 3)
            _draw_eye(screen, EYE_R, EYE_W + 3, int(blink_ry) + 3)

            # Two overlapping sine waves → natural, non-mechanical mouth rhythm
            speak_phase = (speak_phase + dt * 8.5) % (2 * math.pi)
            raw = (abs(math.sin(speak_phase)) * 0.65
                   + abs(math.sin(speak_phase * 1.73 + 1.1)) * 0.35)
            target_h = raw * 22 + 3
            speak_mouth_h += (target_h - speak_mouth_h) * min(1.0, dt * 16)

            # Mouth: top lip stays fixed, lower jaw drops
            mouth_cx = WIDTH // 2
            mouth_top = 232          # upper lip y — fixed
            mouth_ry  = max(2, int(speak_mouth_h))
            mouth_rx  = 46

            # Rect centered on mouth_top so only the bottom arc is visible
            mouth_rect = pygame.Rect(
                mouth_cx - mouth_rx,
                mouth_top - mouth_ry,
                mouth_rx * 2,
                mouth_ry * 2,
            )
            pygame.draw.arc(screen, CYAN, mouth_rect, 0, math.pi, 3)
            pygame.draw.line(
                screen, CYAN,
                (mouth_cx - mouth_rx, mouth_top),
                (mouth_cx + mouth_rx, mouth_top),
                3,
            )

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
