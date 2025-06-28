import pygame
import pygame_gui
import math
import random
import time

# Initialize
pygame.init()

# Screen
WIDTH, HEIGHT = 1270, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cannon")

# Clock
clock = pygame.time.Clock()
FPS = 60

# GUI
manager = pygame_gui.UIManager((WIDTH, HEIGHT))

# Terrain
GROUND_HEIGHT = 100
terrain_y = HEIGHT - GROUND_HEIGHT

# Cannon
cannon_base = (100, terrain_y)
cannon_length = 50
angle = 45
power = 50
ANGLE_STEP = 2

# Physics
GRAVITY = 9.8
projectiles = []

SHOT_COOLDOWN = 0.2  # seconds
last_shot_time = 0

#power variables
super_power_used = False
super_power_active = False
super_power_duration = 5.0  # seconds
super_power_timer = 0


# GUI slider
power_slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((50, 80), (200, 30)),
    start_value=power,
    value_range=(10, 100),
    manager=manager,
)

class Projectile:
    def __init__(self, x, y, angle_deg, power):
        angle_rad = math.radians(angle_deg)
        self.x = x
        self.y = y
        self.vx = power * math.cos(angle_rad)
        self.vy = -power * math.sin(angle_rad)
        self.path = []

    def update(self, dt):
        self.vy += GRAVITY * dt
        self.x += self.vx * dt * 10
        self.y += self.vy * dt * 10
        self.path.append((self.x, self.y))

    def draw(self, surface, trail_color):
        # Trail
        for pos in self.path[-20:]:
            pygame.draw.circle(surface, trail_color, (int(pos[0]), int(pos[1])), 2)

        # Current position
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x), int(self.y)), 5)

class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.max_radius = 50
        self.life = 0.5
        self.elapsed = 0
        self.finished = False

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.life:
            self.finished = True
        else:
            self.radius = 10 + (self.max_radius - 10) * (self.elapsed / self.life)

    def draw(self, surface):
        alpha = max(0, min(255, int(255 * (1 - self.elapsed / self.life))))
        color = (255, 100, 0, alpha)
        surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (int(self.radius), int(self.radius)), int(self.radius))
        surface.blit(surf, (self.x - self.radius, self.y - self.radius))

class Plane:
    def __init__(self):
        self.image = pygame.Surface((60, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (100, 100, 255), [(0, 15), (45, 0), (60, 15), (45, 30)])
        self.speed = 120
        self.alive = True
        self.respawn()

    def respawn(self):
        self.x = random.randint(WIDTH, WIDTH + 200)
        self.y = random.randint(50, terrain_y - 100)
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.alive = True

    def update(self, dt, speed_multiplier=1.0):
        if self.alive:
            self.x -= self.speed * dt * speed_multiplier
            if self.x < -self.rect.width:
                self.respawn()
                global hearts
                hearts -= 1
            self.rect.topleft = (self.x, self.y)

    def draw(self, surface, color):
        if self.alive:
            # Clear previous image and redraw with current color
            self.image.fill((0, 0, 0, 0))  # transparent
            pygame.draw.polygon(self.image, color, [(0, 15), (45, 0), (60, 15), (45, 30)])
            surface.blit(self.image, (self.x, self.y))


class SmokeParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-5, 5)
        self.y = y + random.uniform(-5, 5)
        self.radius = random.randint(5, 10)
        self.life = 1.0
        self.elapsed = 0
        self.alpha = 255

    def update(self, dt):
        self.elapsed += dt
        self.y -= 20 * dt
        self.alpha = max(0, 255 * (1 - self.elapsed / self.life))
        self.radius += dt * 5

    def draw(self, surface):
        surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (200, 200, 200, int(self.alpha)), (int(self.radius), int(self.radius)), int(self.radius))
        surface.blit(surf, (self.x - self.radius, self.y - self.radius))

def spawn_smoke():
    for _ in range(8):
        smoke_particles.append(SmokeParticle(cannon_base[0], cannon_base[1]))

# Plane spawning
MAX_PLANES = 7
planes = []
SPAWN_INTERVAL = 3.0
last_spawn_time = 0

def spawn_planes():
    global last_spawn_time
    now = time.time()
    if now - last_spawn_time >= SPAWN_INTERVAL:
        last_spawn_time = now
        alive_planes = [p for p in planes if p.alive]
        if len(alive_planes) < MAX_PLANES:
            to_spawn = min(random.randint(1, 3), MAX_PLANES - len(alive_planes))
            for _ in range(to_spawn):
                planes.append(Plane())



class BackgroundArtilleryFire:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = terrain_y  # Top of the ground
        self.length = random.randint(10, 20)
        self.width = 2
        self.color = random.choice([(255, 200, 100), (255, 160, 60), (255, 230, 150)])
        self.speed = random.uniform(400, 700)
        self.alpha = 255
        self.life = 0.6
        self.elapsed = 0

        # Determine direction
        direction = random.choices(
            ["up", "left", "right"], weights=[0.6, 0.2, 0.2], k=1
        )[0]

        if direction == "up":
            self.vx = 0
        elif direction == "left":
            self.vx = random.uniform(-50, -80)  # Less horizontal drift
        else:
            self.vx = random.uniform(50, 80)

    def update(self, dt):
        self.y -= self.speed * dt
        self.x += self.vx * dt
        self.elapsed += dt
        self.alpha = max(0, 255 * (1 - self.elapsed / self.life))

    def draw(self, surface):
        # Calculate angle for rotation
        angle_rad = math.atan2(-self.speed, self.vx)
        angle_deg = math.degrees(angle_rad)

        # Create streak surface
        streak = pygame.Surface((self.length, self.width), pygame.SRCALPHA)
        pygame.draw.rect(streak, (*self.color, int(self.alpha)), (0, 0, self.length, self.width))

        # Rotate streak based on direction
        rotated = pygame.transform.rotate(streak, angle_deg)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect.topleft)

    def is_off_screen(self):
        return (self.y + self.length < 0 or self.x < -self.length or self.x > WIDTH + self.length)



# Fonts
font = pygame.font.SysFont(None, 24)
large_font = pygame.font.SysFont(None, 72)

#--Main Loop--

# Game state
running = True
explosions = []
smoke_particles = []
hearts = 3
score = 0
game_over = False
night_mode = False
last_night_toggle = 0
NIGHT_COOLDOWN = 1.0  # seconds cooldown to prevent rapid toggling
background_artillery = []
ARTILLERY_SPAWN_RATE = 0.5
last_artillery_spawn = time.time()




while running:
    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        manager.process_events(event)
        if not game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            current_time = time.time()
            if current_time - last_shot_time >= SHOT_COOLDOWN:
                projectiles.append(Projectile(cannon_base[0], cannon_base[1], angle, power))
                spawn_smoke()
                last_shot_time = current_time

        if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
            current_time = time.time()
            if current_time - last_night_toggle >= NIGHT_COOLDOWN:
                night_mode = not night_mode
                last_night_toggle = current_time



        elif game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            hearts = 3
            score = 0
            game_over = False
            projectiles.clear()
            explosions.clear()
            smoke_particles.clear()
            planes.clear()
            super_power_used = False
            super_power_active = False

        if not game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_s:
             if not super_power_used and not super_power_active:
                super_power_active = True
                super_power_used = True
                super_power_timer = time.time()

    if not game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN]:
            angle = max(0, angle - ANGLE_STEP)
        if keys[pygame.K_UP]:
            angle = min(90, angle + ANGLE_STEP)

    if hearts <= 0:
        game_over = True

    manager.update(dt)

    # Set colors depending on night_mode
    if night_mode:
        sky_color = (20, 24, 40)  # Dark navy for night sky
        ground_color = (30, 50, 30)  # Dark green ground
        plane_color = (180, 180, 255)  # Light bluish planes
        projectile_trail_color = (250, 230, 0)
        cannon_color = (150, 150, 150)
        label_color = (255, 255, 255)
    else:
        sky_color = (135, 206, 235)  # Day sky blue
        ground_color = (80, 200, 120)  # Bright green ground
        plane_color = (100, 100, 255)  # Day plane color
        projectile_trail_color = (200, 200, 200)
        cannon_color = (60, 60, 60)
        label_color = (0, 0, 0)

    power = power_slider.get_current_value()
    screen.fill(sky_color)
    pygame.draw.rect(screen, ground_color, (0, terrain_y, WIDTH, GROUND_HEIGHT))

    spawn_planes()

    current_time = time.time()

    if super_power_active:
        if current_time - super_power_timer >= super_power_duration:
            super_power_active = False

    slow_factor = 0.3 if super_power_active else 1.0

    if night_mode:
        now = time.time()
        if now - last_artillery_spawn > ARTILLERY_SPAWN_RATE:
            background_artillery.append(BackgroundArtilleryFire())
            last_artillery_spawn = now

        for artillery in background_artillery[:]:
            artillery.update(dt)
            artillery.draw(screen)
            if artillery.is_off_screen():
                background_artillery.remove(artillery)

    for plane in planes:
        plane.update(dt * slow_factor)
        plane.draw(screen, plane_color)

    if not game_over:
        rad = math.radians(angle)
        end_x = cannon_base[0] + cannon_length * math.cos(rad)
        end_y = cannon_base[1] - cannon_length * math.sin(rad)
        pygame.draw.line(screen, (60, 60, 60), cannon_base, (end_x, end_y), 8)
        aim_x = cannon_base[0] + 80 * math.cos(rad)
        aim_y = cannon_base[1] - 80 * math.sin(rad)
        pygame.draw.line(screen, (255, 0, 0), cannon_base, (aim_x, aim_y), 2)

    for proj in projectiles[:]:
        proj.update(dt)
        proj.draw(screen, projectile_trail_color)
        if proj.x < 0 or proj.x > WIDTH or proj.y > HEIGHT:
            projectiles.remove(proj)

    for proj in projectiles:
        hitbox = pygame.Rect(int(proj.x) - 5, int(proj.y) - 5, 10, 10)
        for plane in planes:
            if plane.alive and plane.rect.colliderect(hitbox):
                plane.alive = False
                explosions.append(Explosion(proj.x, proj.y))
                score += 10

    for explosion in explosions[:]:
        explosion.update(dt)
        explosion.draw(screen)
        if explosion.finished:
            explosions.remove(explosion)

    for p in smoke_particles[:]:
        p.update(dt)
        p.draw(screen)
        if p.elapsed >= p.life:
            smoke_particles.remove(p)

    for i in range(hearts):
        pygame.draw.circle(screen, (255, 0, 0), (30 + i * 40, 30), 15)

    screen.blit(font.render(f"Score: {score}", True, label_color), (30, 60))
    screen.blit(font.render(f"Angle: {int(angle)}°", True, label_color), (270, 35))
    screen.blit(font.render(f"Power: {int(power)}", True, label_color), (270, 85))

    manager.draw_ui(screen)

    if super_power_active:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((200, 200, 200, 80))  # light gray with alpha 80 (adjust as you like)
        screen.blit(overlay, (0, 0))

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        go_text = large_font.render("GAME OVER", True, label_color)
        screen.blit(go_text, go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
        score_text = large_font.render(f"Score: {score}", True, label_color)
        screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))
        restart_text = font.render("Press 'R' to Restart", True, label_color)
        screen.blit(restart_text, restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))


    pygame.display.update()

pygame.quit()