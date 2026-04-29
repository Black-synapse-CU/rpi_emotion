import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
import pygame
import time
import socket
import threading
# Screen dimensions (common for 3.5" RPi screens)
# XPT2046 screens are often 480x320 or 320x240
WIDTH, HEIGHT = 480, 320
# For XPT2046, you might need to specify the framebuffer
# os.environ["SDL_FBDEV"] = "/dev/fb1"

# Colors
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

class RobotFace:
    def __init__(self, fullscreen=False):
        pygame.init()
        time.sleep(0.5) # Give the OS a moment to prepare
        # Set up display
        if fullscreen:
            # Try to hide the taskbar (LXPanel) for a cleaner fullscreen look
            try:
                import subprocess
                subprocess.run(["lxpanelctl", "hide"], stderr=subprocess.DEVNULL)
            except:
                pass

            # Detect actual screen resolution
            info = pygame.display.Info()
            screen_w, screen_h = info.current_w, info.current_h
            # Use NOFRAME to remove window decorations and borders
            self.screen = pygame.display.set_mode((screen_w, screen_h), pygame.FULLSCREEN | pygame.NOFRAME)
            
            # Update global dimensions for drawing logic
            global WIDTH, HEIGHT
            WIDTH, HEIGHT = screen_w, screen_h
        else:
            # Even in windowed mode, we can use NOFRAME to remove borders
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
            
        pygame.display.set_caption("Robot Face")
        pygame.mouse.set_visible(False) # Hide cursor
        self.clock = pygame.time.Clock()
        self.running = True
        self.emotion = "neutral"
        self.blink_timer = 0
        self.is_blinking = False
        self.last_command_time = time.time()
        self.idle_offset_x = 0
        self.idle_offset_y = 0
        self.flinch_timer = 0
        self.pre_flinch_emotion = "neutral"

    def draw_eye(self, x, y, size, emotion):
        # Apply idle movement offsets
        x += self.idle_offset_x
        y += self.idle_offset_y

        if self.is_blinking:
            # Drawing a thin line for blink
            pygame.draw.line(self.screen, CYAN, (x - size, y), (x + size, y), 5)
            return

        color = CYAN
        if emotion == "angry":
            color = RED
            # Angled eyes
            points = [(x - size, y - size), (x + size, y), (x - size, y + size)]
            pygame.draw.polygon(self.screen, color, points)
        elif emotion == "sad":
            color = CYAN
            # Droopy eyes
            pygame.draw.circle(self.screen, color, (x, y), size)
            pygame.draw.rect(self.screen, BLACK, (x - size, y - size, size * 2, size))
        elif emotion == "happy":
            color = CYAN
            # Curved eyes (arc)
            pygame.draw.arc(self.screen, color, (x - size, y - size, size * 2, size * 2), 0, 3.14, 10)
        elif emotion == "surprised":
            color = YELLOW
            pygame.draw.circle(self.screen, color, (x, y), size + 10, 5)
            pygame.draw.circle(self.screen, color, (x, y), size // 2)
        else: # neutral
            pygame.draw.circle(self.screen, color, (x, y), size)
            # Subtle inner glow
            pygame.draw.circle(self.screen, WHITE, (x - size//3, y - size//3), size//4)

    def draw(self):
        self.screen.fill(BLACK)
        eye_size = 60
        spacing = 100
        
        # Apply flinch shake
        shake_x, shake_y = 0, 0
        if self.flinch_timer > 0:
            import random
            shake_x = random.randint(-15, 15)
            shake_y = random.randint(-15, 15)
            self.flinch_timer -= 1
            if self.flinch_timer == 0:
                self.emotion = self.pre_flinch_emotion

        self.draw_eye(WIDTH // 2 - spacing + shake_x, HEIGHT // 2 + shake_y, eye_size, self.emotion)
        self.draw_eye(WIDTH // 2 + spacing + shake_x, HEIGHT // 2 + shake_y, eye_size, self.emotion)
        pygame.display.flip()

    def update_emotion(self, new_emotion):
        if new_emotion == "blink":
            self.is_blinking = True
            self.blink_timer = 0
            return

        print(f"Switching to emotion: {new_emotion}")
        self.emotion = new_emotion
        self.last_command_time = time.time()

    def run_socket_server(self):
        # UDP server to receive emotion commands
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 5005))
        print("Face Server listening on UDP port 5005...")
        while self.running:
            try:
                sock.settimeout(1.0)
                data, addr = sock.recvfrom(1024)
                cmd = data.decode("utf-8").strip().lower()
                if cmd in ["happy", "sad", "angry", "neutral", "surprised", "blink"]:
                    self.update_emotion(cmd)
            except socket.timeout:
                continue

    def main_loop(self):
        # Start socket thread
        threading.Thread(target=self.run_socket_server, daemon=True).start()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Flinch on touch/click
                    if self.flinch_timer == 0:
                        self.pre_flinch_emotion = self.emotion
                    self.emotion = "surprised"
                    self.flinch_timer = 10 # frames of shaking

            # Auto-reset to neutral after 10 seconds of inactivity
            if self.emotion != "neutral" and (time.time() - self.last_command_time > 10):
                self.update_emotion("neutral")

            # Random eye movement (Idle look around)
            if self.emotion == "neutral":
                if time.time() % 5 < 0.05: # Occasional look
                    import random
                    self.idle_offset_x = random.randint(-10, 10)
                    self.idle_offset_y = random.randint(-5, 5)
                elif time.time() % 5 > 2.0 and time.time() % 5 < 2.05: # Reset look
                    self.idle_offset_x = 0
                    self.idle_offset_y = 0

            # Random blinking logic
            self.blink_timer += 1
            if not self.is_blinking and self.blink_timer > 100:
                if time.time() % 3 < 0.05: # randomish
                    self.is_blinking = True
                    self.blink_timer = 0
            if self.is_blinking and self.blink_timer > 5:
                self.is_blinking = False
                self.blink_timer = 0

            self.draw()
            self.clock.tick(30)

        pygame.quit()

if __name__ == "__main__":
    # Check for fullscreen flag in args or environment
    is_fs = os.environ.get("FULLSCREEN", "false").lower() == "true"
    face = RobotFace(fullscreen=is_fs)
    face.main_loop()

