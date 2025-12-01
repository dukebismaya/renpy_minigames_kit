init python early:
    """Space Rebellion mini-game engine implemented with pygame surfaces."""

    import math
    import os
    import random

    import renpy.pygame as pygame


    def _clamp(value, low, high):
        return max(low, min(high, value))


    class Vec2(object):
        __slots__ = ("x", "y")

        def __init__(self, x=0.0, y=0.0):
            if isinstance(x, Vec2):
                self.x = float(x.x)
                self.y = float(x.y)
            elif isinstance(x, (tuple, list)):
                self.x = float(x[0])
                self.y = float(x[1] if len(x) > 1 else 0.0)
            else:
                self.x = float(x)
                self.y = float(y)

        def set(self, x, y):
            self.x = float(x)
            self.y = float(y)
            return self

        def __add__(self, other):
            other = Vec2(other)
            return Vec2(self.x + other.x, self.y + other.y)

        def __iadd__(self, other):
            other = Vec2(other)
            self.x += other.x
            self.y += other.y
            return self

        def __sub__(self, other):
            other = Vec2(other)
            return Vec2(self.x - other.x, self.y - other.y)

        def __neg__(self):
            return Vec2(-self.x, -self.y)

        def __mul__(self, scalar):
            scalar = float(scalar)
            return Vec2(self.x * scalar, self.y * scalar)

        def __rmul__(self, scalar):
            return self.__mul__(scalar)

        def __imul__(self, scalar):
            scalar = float(scalar)
            self.x *= scalar
            self.y *= scalar
            return self

        def length_squared(self):
            return self.x * self.x + self.y * self.y

        def normalized(self):
            length = math.sqrt(self.length_squared())
            if length <= 1e-6:
                return Vec2(0.0, 0.0)
            inv = 1.0 / length
            return Vec2(self.x * inv, self.y * inv)

        def rotated(self, degrees):
            radians = math.radians(degrees)
            cos_theta = math.cos(radians)
            sin_theta = math.sin(radians)
            return Vec2(self.x * cos_theta - self.y * sin_theta, self.x * sin_theta + self.y * cos_theta)

        def distance_squared_to(self, other):
            other = Vec2(other)
            dx = self.x - other.x
            dy = self.y - other.y
            return dx * dx + dy * dy


    class CircleEntity(object):
        __slots__ = ("position", "radius")

        def __init__(self, position, radius):
            self.position = Vec2(position)
            self.radius = float(radius)


    class Projectile(object):
        __slots__ = ("position", "velocity", "sprite", "radius", "damage", "friendly", "alive")

        def __init__(self, position, velocity, sprite, damage=1, friendly=True):
            self.position = Vec2(position)
            self.velocity = Vec2(velocity)
            self.sprite = sprite
            self.damage = damage
            self.friendly = friendly
            self.radius = max(6.0, sprite.get_width() * 0.35)
            self.alive = True

        def update(self, dt):
            self.position += self.velocity * dt

        def draw(self, surface):
            rect = self.sprite.get_rect(center=(self.position.x, self.position.y))
            surface.blit(self.sprite, rect)

        def offscreen(self, width, height):
            return (
                self.position.x < -72
                or self.position.x > width + 72
                or self.position.y < -120
                or self.position.y > height + 120
            )

        def collides_with(self, entity):
            radius = self.radius + entity.radius
            return self.position.distance_squared_to(entity.position) <= radius * radius


    class Booster(CircleEntity):
        LABELS = {
            "double": "Spread Shot",
            "rapid": "Rapid Fire",
            "heal": "Repair",
            "shield": "Shield",
        }

        def __init__(self, sprite, kind, position, rng):
            super(Booster, self).__init__(position, max(12.0, sprite.get_width() * 0.4))
            self.sprite = sprite
            self.kind = kind
            self.velocity = Vec2(rng.uniform(-20, 20), rng.uniform(60, 110))
            self.alive = True

        def update(self, dt, width):
            self.position += self.velocity * dt
            if self.position.x < 24 or self.position.x > width - 24:
                self.velocity.x *= -1
            self.velocity.x *= 0.99

        def draw(self, surface):
            rect = self.sprite.get_rect(center=(self.position.x, self.position.y))
            surface.blit(self.sprite, rect)


    class Enemy(CircleEntity):
        def __init__(self, sprite, position, velocity, hp, score_value, fire_delay, behavior, bounds, is_monster=False):
            radius_scale = 0.46 if is_monster else 0.36
            super(Enemy, self).__init__(position, max(16.0, sprite.get_width() * radius_scale))
            self.sprite = sprite
            self.velocity = Vec2(velocity)
            self.hp = hp
            self.score_value = score_value
            self.fire_delay = fire_delay
            self.fire_timer = random.uniform(fire_delay * 0.35, fire_delay)
            self.behavior = behavior
            self.bounds = bounds
            self.phase = random.uniform(0.0, math.tau)
            self.amplitude = random.uniform(28.0, 72.0)
            self.anchor_x = float(self.position.x)
            self.is_monster = is_monster
            self.vertical_gate = random.uniform(0.35, 0.6) * bounds[1]

        def update(self, dt):
            self.phase += dt
            if self.behavior == "sway":
                self.position.y += self.velocity.y * dt
                self.position.x = self.anchor_x + math.sin(self.phase * 1.6) * self.amplitude
            elif self.behavior == "flank":
                self.position += self.velocity * dt
                if self.position.x < 40 or self.position.x > self.bounds[0] - 40:
                    self.velocity.x *= -1
            elif self.behavior == "diver":
                self.velocity.y = _clamp(self.velocity.y + 35 * dt, 40, 220)
                self.position += self.velocity * dt
            elif self.behavior == "boss":
                if self.position.y < self.vertical_gate:
                    self.position.y += self.velocity.y * dt
                self.position.x = self.anchor_x + math.sin(self.phase * 0.7) * (self.amplitude + 60)
            else:
                self.position += self.velocity * dt
            self.fire_timer -= dt

        def ready_to_fire(self):
            if self.fire_timer <= 0:
                jitter = random.uniform(0.65, 1.2)
                self.fire_timer = max(0.4, self.fire_delay * jitter)
                return True
            return False

        def take_damage(self, amount):
            self.hp -= amount
            return self.hp <= 0

        def draw(self, surface):
            rect = self.sprite.get_rect(center=(self.position.x, self.position.y))
            surface.blit(self.sprite, rect)

        def muzzle_position(self):
            rect = self.sprite.get_rect(center=(self.position.x, self.position.y))
            return Vec2(rect.centerx, rect.bottom - 8)


    class Player(CircleEntity):
        def __init__(self, sprite, bounds):
            super(Player, self).__init__((bounds[0] / 2, bounds[1] - 80), max(18.0, sprite.get_width() * 0.35))
            self.sprite = sprite
            self.bounds = bounds
            self.speed = 380.0
            self.acceleration = 1200.0
            self.friction = 4.0
            self.velocity = Vec2(0.0, 0.0)
            self.cooldown = 0.18
            self.base_cooldown = self.cooldown
            self.cooldown_timer = 0.0
            self.invulnerable_timer = 0.0
            self.max_health = 100
            self.health = self.max_health
            self.alive = True
            self.damage_bonus = 1.0
            self.ship_name = "Vanguard"

        def reset(self):
            self.position.set(self.bounds[0] / 2, self.bounds[1] - 80)
            self.velocity.set(0.0, 0.0)
            self.cooldown_timer = 0.0
            self.cooldown = self.base_cooldown
            self.invulnerable_timer = 0.0
            self.health = self.max_health
            self.alive = True

        def update(self, dt, direction):
            desired_velocity = Vec2(0.0, 0.0)
            if direction.length_squared() > 0:
                desired_velocity = direction.normalized() * self.speed
            delta = desired_velocity - self.velocity
            delta_len_sq = delta.length_squared()
            if delta_len_sq > 0:
                max_change = self.acceleration * dt
                delta_len = math.sqrt(delta_len_sq)
                if delta_len > max_change:
                    delta *= max_change / delta_len
                self.velocity += delta
            if direction.length_squared() == 0 and self.velocity.length_squared() > 0:
                damping = max(0.0, 1.0 - self.friction * dt)
                self.velocity *= damping
                if self.velocity.length_squared() < 1.0:
                    self.velocity.set(0.0, 0.0)
            self.position += self.velocity * dt
            self.position.x = _clamp(self.position.x, 32, self.bounds[0] - 32)
            self.position.y = _clamp(self.position.y, 32, self.bounds[1] - 32)
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)

        def can_fire(self):
            return self.cooldown_timer <= 0.0

        def fire(self, direction, sprite_provider, double_shot=False):
            if direction.length_squared() == 0:
                direction = Vec2(0, -1)
            direction = direction.normalized()
            self.cooldown_timer = self.cooldown
            directions = [direction]
            if double_shot:
                directions = [direction.rotated(8), direction.rotated(-8)]
            projectiles = []
            for dir_vec in directions:
                dir_norm = dir_vec.normalized()
                spawn = self.position + dir_norm * (self.radius + 10)
                sprite = sprite_provider()
                base_damage = 2 if double_shot else 1
                damage = max(1, int(round(base_damage * self.damage_bonus)))
                projectile = Projectile(
                    position=(spawn.x, spawn.y),
                    velocity=(dir_norm.x * 640, dir_norm.y * 640),
                    sprite=sprite,
                    damage=damage,
                    friendly=True,
                )
                projectiles.append(projectile)
            return projectiles

        def draw(self, surface):
            rect = self.sprite.get_rect(center=(self.position.x, self.position.y))
            surface.blit(self.sprite, rect)

        def take_damage(self, amount):
            if self.invulnerable_timer > 0:
                return False
            self.health = max(0, self.health - int(amount))
            if self.health == 0:
                self.alive = False
            return not self.alive

        def heal(self, amount):
            self.health = min(self.max_health, self.health + int(amount))
            if self.health > 0:
                self.alive = True


    class SpaceRebellionEngine(object):
        def __init__(self, asset_root=None, width=960, height=600, seed=None):
            self.asset_root = asset_root or ""
            self.width = width
            self.height = height
            self.random = random.Random(seed)
            self.scene_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA).convert_alpha()
            self.frame_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA).convert_alpha()

            self.player_sprite = self._load_first_sprite(
                [
                    "sprites/ships/Ship_1_A_Small.png",
                    "sprites/ships/ship6.png",
                    "sprites/ships/ship8.png",
                ],
                scale=1.15,
                fallback_color=(120, 200, 255),
            )
            self.enemy_sprites = self._load_sprite_folder("sprites/enemies", scale=1.05, fallback_color=(255, 120, 120))
            self.boss_sprites = self._load_sprite_folder("sprites/boss", scale=1.2, fallback_color=(255, 196, 92))
            self.pickup_sprites = self._load_sprite_folder("sprites/pickup", scale=0.8, fallback_color=(120, 255, 160))
            self.bullet_sprites = self._load_sprite_folder("sprites/missile", scale=0.6, fallback_color=(255, 255, 255))

            self.player = Player(self.player_sprite, (self.width, self.height))
            self.input_direction = Vec2(0, 0)
            self.pointer = Vec2(self.width / 2, self.height / 2)
            self.use_mouse_aim = False
            self.keyboard_fire = False
            self.mouse_fire = False

            self.player_projectiles = []
            self.enemy_projectiles = []
            self.enemies = []
            self.boosters = []
            self.thruster_particles = []
            self.wave_index = 0
            self.wave_banner_timer = 0.0
            self.wave_cooldown = 0.5
            self.score = 0
            self.combo = 1
            self.combo_timer = 0.0
            self.double_shot_timer = 0.0
            self.rapid_fire_timer = 0.0
            self.shield_timer = 0.0
            self.game_over = False
            self.elapsed = 0.0
            self.kills_since_drop = 0
            self.powerup_spawn_timer = 0.0
            self.powerup_spawn_interval = 10.0
            self.powerup_duration = 6.0
            self.boss_active = False

            self.starfield = self._build_starfield()
            self.camera_offset = Vec2(0, 0)
            self.shake_timer = 0.0
            self.shake_duration = 0.001
            self.shake_strength = 0.0
            self.ship_profile = None
            self.wave_limit = None
            self.mission_complete = False

        def reset(self):
            limit = self.wave_limit
            self.player.reset()
            self.input_direction.set(0, 0)
            self.pointer.set(self.width / 2, self.height / 2)
            self.player_projectiles[:] = []
            self.enemy_projectiles[:] = []
            self.enemies[:] = []
            self.boosters[:] = []
            self.wave_index = 0
            self.wave_banner_timer = 0.0
            self.wave_cooldown = 0.5
            self.score = 0
            self.combo = 1
            self.combo_timer = 0.0
            self.double_shot_timer = 0.0
            self.rapid_fire_timer = 0.0
            self.shield_timer = 0.0
            self.game_over = False
            self.elapsed = 0.0
            self.kills_since_drop = 0
            self.powerup_spawn_timer = 0.0
            self.powerup_spawn_interval = 10.0
            self.powerup_duration = 6.0
            self.boss_active = False
            self.starfield = self._build_starfield()
            self.thruster_particles[:] = []
            self.camera_offset.set(0, 0)
            self.shake_timer = 0.0
            self.shake_duration = 0.001
            self.shake_strength = 0.0
            self.mission_complete = False
            if self.ship_profile:
                self._apply_ship_profile()
            self.set_wave_limit(limit)

        def update(self, dt):
            dt = _clamp(dt, 0.0, 0.05)
            self.elapsed += dt
            self._update_starfield(dt)

            self.player.update(dt, self.input_direction)
            self._update_thruster_particles(dt)
            self.combo_timer = max(0.0, self.combo_timer - dt)
            if self.combo_timer == 0:
                self.combo = 1
            self.double_shot_timer = max(0.0, self.double_shot_timer - dt)
            self.rapid_fire_timer = max(0.0, self.rapid_fire_timer - dt)
            self.shield_timer = max(0.0, self.shield_timer - dt)
            base_cd = getattr(self.player, "base_cooldown", self.player.cooldown)
            if self.rapid_fire_timer > 0:
                self.player.cooldown = max(0.05, base_cd * 0.5)
            else:
                self.player.cooldown = base_cd
            if not self.player.alive and not self.game_over:
                self.game_over = True
                self._halt_player_motion()

            firing = self.keyboard_fire or self.mouse_fire
            if not self.game_over and firing and self.player.can_fire():
                direction = self._aim_direction()
                double_shot = self.double_shot_timer > 0.0
                projectiles = self.player.fire(direction, self._random_bullet_sprite, double_shot)
                self.player_projectiles.extend(projectiles)
                self._spawn_muzzle_flash(direction)

            self._update_projectiles(dt)
            self._update_enemies(dt)
            self._update_boosters(dt)
            self._handle_collisions()
            self._handle_waves(dt)
            self._update_powerup_timer(dt)
            self._update_camera_shake(dt)
            if self.wave_banner_timer > 0:
                self.wave_banner_timer = max(0.0, self.wave_banner_timer - dt)

        def render(self):
            scene = self.scene_surface
            scene.fill((4, 9, 20))
            self._draw_starfield(scene)
            self._draw_thruster_particles(scene)

            for booster in self.boosters:
                booster.draw(scene)
            for projectile in self.enemy_projectiles:
                projectile.draw(scene)
            for projectile in self.player_projectiles:
                projectile.draw(scene)
            for enemy in self.enemies:
                enemy.draw(scene)
            self._draw_powerup_effects(scene)
            self.player.draw(scene)

            canvas = self.frame_surface
            canvas.fill((4, 9, 20))
            offset = (int(round(self.camera_offset.x)), int(round(self.camera_offset.y)))
            canvas.blit(scene, offset)
            return canvas

        def snapshot(self):
            return {
                "score": self.score,
                "wave": self.wave_index,
                "health": self.player.health,
                "max_health": self.player.max_health,
                "double_shot": self.double_shot_timer,
                "rapid_fire": self.rapid_fire_timer,
                "shield": self.shield_timer,
                "game_over": self.game_over,
                "mission_complete": self.mission_complete,
                "wave_banner": self.wave_banner_timer,
                "boss_active": self.boss_active,
                "ship_name": self.player.ship_name,
                "ship_role": (self.ship_profile or {}).get("role", ""),
                "wave_limit": self.wave_limit,
            }

        def result(self, aborted=False):
            data = self.snapshot()
            data.update(
                {
                    "aborted": aborted,
                    "elapsed": round(self.elapsed, 2),
                    "health": self.player.health,
                    "mission_complete": self.mission_complete,
                }
            )
            return data

        def set_direction(self, dx, dy):
            if self.game_over:
                self._halt_player_motion()
                return
            direction = Vec2(dx, dy)
            if direction.length_squared() > 1:
                direction = direction.normalized()
            self.input_direction = direction

        def set_keyboard_fire(self, active):
            self.keyboard_fire = bool(active)

        def set_mouse_fire(self, active):
            self.mouse_fire = bool(active)

        def set_pointer(self, position, use_mouse=True):
            self.pointer.set(
                _clamp(position[0], 0, self.width),
                _clamp(position[1], 0, self.height),
            )
            self.use_mouse_aim = use_mouse

        def _aim_direction(self):
            if self.use_mouse_aim:
                offset = self.pointer - self.player.position
                if offset.length_squared() > 0:
                    return offset.normalized()
            return Vec2(0, -1)

        def _random_bullet_sprite(self):
            return self.random.choice(self.bullet_sprites)

        def _update_projectiles(self, dt):
            for projectile_list in (self.player_projectiles, self.enemy_projectiles):
                for projectile in projectile_list:
                    projectile.update(dt)
                projectile_list[:] = [
                    proj
                    for proj in projectile_list
                    if proj.alive and not proj.offscreen(self.width, self.height)
                ]

        def _update_enemies(self, dt):
            for enemy in list(self.enemies):
                enemy.update(dt)
                if enemy.position.y > self.height + 160:
                    if enemy.is_monster:
                        self.boss_active = False
                    self.enemies.remove(enemy)
                    continue
                if not self.game_over and enemy.ready_to_fire():
                    self._spawn_enemy_fire(enemy)
            if self.boss_active and not any(e.is_monster for e in self.enemies):
                self.boss_active = False

        def _spawn_enemy_fire(self, enemy):
            sprite = self.random.choice(self.bullet_sprites)
            direction = Vec2(0, 1)
            patterns = [0.0]
            damage = 12
            speed = 260 + self.wave_index * 12
            if enemy.behavior == "flank":
                patterns = [-10, 0, 10]
            if enemy.is_monster:
                patterns = [-30, -12, 12, 30]
                damage = 18
                speed += 80
            origin = enemy.muzzle_position()
            for angle in patterns:
                vel = direction.rotated(angle).normalized() * speed
                projectile = Projectile(
                    position=(origin.x, origin.y),
                    velocity=(vel.x, vel.y),
                    sprite=sprite,
                    damage=damage,
                    friendly=False,
                )
                projectile.radius *= 0.8
                self.enemy_projectiles.append(projectile)

        def _update_boosters(self, dt):
            for booster in self.boosters:
                booster.update(dt, self.width)
            self.boosters[:] = [b for b in self.boosters if b.alive and b.position.y < self.height + 120]

        def _handle_collisions(self):
            if self.game_over:
                return

            for projectile in list(self.player_projectiles):
                target = None
                for enemy in self.enemies:
                    if projectile.collides_with(enemy):
                        target = enemy
                        break
                if target:
                    projectile.alive = False
                    died = target.take_damage(projectile.damage)
                    if died:
                        self._on_enemy_destroyed(target)
                        self.enemies.remove(target)
            self.player_projectiles[:] = [p for p in self.player_projectiles if p.alive]

            for projectile in list(self.enemy_projectiles):
                if projectile.collides_with(self.player):
                    projectile.alive = False
                    self._damage_player(projectile.damage)
            self.enemy_projectiles[:] = [p for p in self.enemy_projectiles if p.alive]

            for enemy in list(self.enemies):
                combined = self.player.radius + enemy.radius
                if self.player.position.distance_squared_to(enemy.position) <= combined * combined:
                    self._damage_player(25)
                    self._on_enemy_destroyed(enemy, score_bonus=False)
                    self.enemies.remove(enemy)

            for booster in list(self.boosters):
                combined = self.player.radius + booster.radius
                if self.player.position.distance_squared_to(booster.position) <= combined * combined:
                    booster.alive = False
                    self._apply_booster(booster)
                    self.boosters.remove(booster)

        def _apply_booster(self, booster):
            if booster.kind == "double":
                self.double_shot_timer = max(self.double_shot_timer, self.powerup_duration)
            elif booster.kind == "rapid":
                self.rapid_fire_timer = max(self.rapid_fire_timer, self.powerup_duration)
            elif booster.kind == "shield":
                self.shield_timer = max(self.shield_timer, self.powerup_duration)
                self.player.invulnerable_timer = max(self.player.invulnerable_timer, 0.5)
            elif booster.kind == "heal":
                self.player.heal(25)
            self.combo = min(5, self.combo + 1)
            self.combo_timer = 4.0

        def _on_enemy_destroyed(self, enemy, score_bonus=True):
            if score_bonus:
                multiplier = max(1, 1 + (self.wave_index // 3))
                total = int(enemy.score_value * multiplier)
                self.score += total
                self.combo = min(5, self.combo + 1)
                self.combo_timer = 4.0
            self.kills_since_drop += 1
            guaranteed = enemy.is_monster or self.kills_since_drop >= 9
            self._maybe_spawn_booster(enemy.position, guaranteed)
            if enemy.is_monster:
                self._on_boss_destroyed()

        def _on_boss_destroyed(self):
            self.boss_active = False
            self.wave_banner_timer = 2.2
            self.wave_cooldown = 1.5

        def _complete_mission(self):
            if self.mission_complete:
                return
            self.mission_complete = True
            self.game_over = True
            self._halt_player_motion()
            self.wave_banner_timer = 0.0
            self.boss_active = False
            self.enemy_projectiles[:] = []
            self.player_projectiles[:] = []
            self.boosters[:] = []

        def _halt_player_motion(self):
            self.input_direction.set(0.0, 0.0)
            if hasattr(self.player, "velocity"):
                self.player.velocity.set(0.0, 0.0)

        def set_ship_profile(self, profile):
            if not profile:
                return
            self.ship_profile = dict(profile)
            self._apply_ship_profile()

        def set_wave_limit(self, wave_limit):
            if wave_limit is None:
                self.wave_limit = None
            else:
                try:
                    wave_limit = int(wave_limit)
                except (TypeError, ValueError):
                    self.wave_limit = None
                else:
                    self.wave_limit = max(1, wave_limit)
            if self.wave_limit is None:
                self.mission_complete = False

        def _apply_ship_profile(self):
            if not self.ship_profile:
                return
            profile = self.ship_profile
            sprite_rel = profile.get("sprite")
            sprite = profile.get("_sprite_surface")
            if sprite_rel:
                if sprite is None:
                    sprite = self._load_image(sprite_rel, scale=1.0)
                    if sprite is not None:
                        sprite = self._scale_ship_sprite(sprite, profile)
                        profile["_sprite_surface"] = sprite
                if sprite is not None:
                    self.player.sprite = sprite
                    self.player.radius = max(18.0, sprite.get_width() * 0.35)
            self.player.speed = profile.get("speed", self.player.speed)
            self.player.acceleration = profile.get("acceleration", self.player.acceleration)
            self.player.friction = profile.get("friction", self.player.friction)
            max_health = profile.get("health", self.player.max_health)
            self.player.max_health = max_health
            self.player.health = self.player.max_health
            base_cd = profile.get("cooldown", self.player.base_cooldown)
            self.player.base_cooldown = base_cd
            self.player.cooldown = base_cd
            self.player.damage_bonus = profile.get("damage", self.player.damage_bonus)
            self.player.ship_name = profile.get("name", self.player.ship_name)

        def _update_powerup_timer(self, dt):
            if self.game_over:
                return
            self.powerup_spawn_timer += dt
            if self.powerup_spawn_timer >= self.powerup_spawn_interval:
                self.powerup_spawn_timer = 0.0
                self._spawn_powerup()

        def _maybe_spawn_booster(self, position, guaranteed=False):
            spawn_chance = 0.12 + self.wave_index * 0.008
            if guaranteed or self.random.random() < spawn_chance:
                kind = self._choose_booster_kind()
                sprite = self.random.choice(self.pickup_sprites)
                booster = Booster(sprite, kind, (position.x, position.y), self.random)
                self.boosters.append(booster)
                self.kills_since_drop = 0

        def _choose_booster_kind(self):
            table = []
            def add(kind, weight):
                table.extend([kind] * weight)

            add("double", 3)
            add("rapid", 2)
            add("shield", 2)
            if self.player.health < self.player.max_health:
                add("heal", 4)
            else:
                add("heal", 1)
            if self.double_shot_timer <= 0:
                add("double", 2)
            if self.rapid_fire_timer <= 0:
                add("rapid", 1)
            if self.shield_timer <= 0:
                add("shield", 1)
            return self.random.choice(table)

        def _damage_player(self, amount=12):
            if self.player.invulnerable_timer > 0:
                return
            if self.shield_timer > 0:
                self.shield_timer = max(0.0, self.shield_timer - 1.5)
                self.player.invulnerable_timer = 0.4
                return
            died = self.player.take_damage(amount)
            self._trigger_shake(strength=min(18.0, 4.0 + amount * 0.35), duration=0.35)
            self.player.invulnerable_timer = 0.9
            self.combo = 1
            self.combo_timer = 0.0
            if died:
                self.game_over = True
                self._halt_player_motion()

        def _handle_waves(self, dt):
            if self.game_over:
                return
            if self.wave_limit and self.wave_index >= self.wave_limit:
                if not self.enemies and not self.boss_active:
                    self._complete_mission()
                return
            if self.boss_active:
                return
            if self.enemies:
                return
            self.wave_cooldown -= dt
            if self.wave_cooldown <= 0:
                self._spawn_wave()

        def _spawn_wave(self):
            self.wave_index += 1
            cols = min(8, 3 + self.wave_index // 2)
            rows = min(5, 1 + self.wave_index // 3)
            spacing_x = self.width / (cols + 1)
            start_y = 70
            base_speed = 55 + self.wave_index * 4
            base_hp = 2 + self.wave_index // 2
            for row in range(rows):
                for col in range(cols):
                    sprite = self.random.choice(self.enemy_sprites)
                    pos = (spacing_x * (col + 1), start_y + row * 60)
                    velocity = (self.random.uniform(-35, 35), base_speed)
                    hp = base_hp + row // 2
                    fire_delay = max(0.7, 2.4 - self.wave_index * 0.08)
                    behavior = self.random.choice(["sway", "flank", "diver"])
                    score_value = 120 + self.wave_index * 18
                    enemy = Enemy(
                        sprite=sprite,
                        position=pos,
                        velocity=velocity,
                        hp=hp,
                        score_value=score_value,
                        fire_delay=fire_delay,
                        behavior=behavior,
                        bounds=(self.width, self.height),
                    )
                    self.enemies.append(enemy)

            if self.wave_index % 5 == 0:
                self._spawn_boss()
            self.wave_cooldown = 2.0
            self.wave_banner_timer = 2.0

        def _spawn_boss(self):
            if not self.boss_sprites:
                return
            boss_sprite = self.random.choice(self.boss_sprites)
            boss = Enemy(
                sprite=boss_sprite,
                position=(self.width / 2, -140),
                velocity=(0, 40 + self.wave_index * 3),
                hp=24 + self.wave_index * 4,
                score_value=900 + self.wave_index * 70,
                fire_delay=max(0.5, 1.6 - self.wave_index * 0.04),
                behavior="boss",
                bounds=(self.width, self.height),
                is_monster=True,
            )
            self.enemies.append(boss)
            self.boss_active = True
            self.wave_banner_timer = 2.5

        def _spawn_powerup(self):
            if not self.pickup_sprites:
                return
            kind = self._choose_booster_kind()
            sprite = self.random.choice(self.pickup_sprites)
            x = self.random.uniform(80, self.width - 80)
            booster = Booster(sprite, kind, (x, -40), self.random)
            booster.velocity = Vec2(self.random.uniform(-25, 25), self.random.uniform(55, 95))
            self.boosters.append(booster)

        def _build_starfield(self):
            stars = []
            for _ in range(110):
                stars.append(
                    {
                        "x": self.random.uniform(0, self.width),
                        "y": self.random.uniform(0, self.height),
                        "speed": self.random.uniform(20, 120),
                        "size": self.random.randint(1, 3),
                        "alpha": self.random.randint(120, 220),
                    }
                )
            return stars

        def _update_starfield(self, dt):
            for star in self.starfield:
                star["y"] += star["speed"] * dt
                if star["y"] > self.height:
                    star["y"] = -5
                    star["x"] = self.random.uniform(0, self.width)

        def _draw_starfield(self, surface):
            for star in self.starfield:
                color = (180, 200, 255, int(star["alpha"]))
                pygame.draw.circle(surface, color, (int(star["x"]), int(star["y"])), star["size"])

        def _update_thruster_particles(self, dt):
            velocity_sq = self.player.velocity.length_squared()
            if velocity_sq > 16.0 and not self.game_over:
                intensity = min(1.0, math.sqrt(velocity_sq) / max(1.0, self.player.speed))
                emission_dir = Vec2(-self.player.velocity.x, -self.player.velocity.y)
                if emission_dir.length_squared() == 0:
                    emission_dir.set(0.0, 1.0)
                emission_dir = emission_dir.normalized()
                spawn = 1 + int(intensity * 2)
                for _ in range(spawn):
                    jitter = Vec2(self.random.uniform(-6, 6), self.random.uniform(-4, 4))
                    position = self.player.position + jitter + emission_dir * (self.player.radius * 0.8)
                    particle = {
                        "pos": Vec2(position),
                        "vel": emission_dir * self.random.uniform(160, 260),
                        "age": 0.0,
                        "life": self.random.uniform(0.22, 0.38),
                        "size": self.random.uniform(4.0, 7.0),
                        "intensity": intensity,
                        "variant": "engine",
                    }
                    self.thruster_particles.append(particle)

            alive_particles = []
            for particle in self.thruster_particles:
                particle["age"] += dt
                particle["pos"] += particle["vel"] * dt
                if particle["age"] < particle["life"]:
                    alive_particles.append(particle)
            self.thruster_particles = alive_particles

        def _draw_thruster_particles(self, surface):
            for particle in self.thruster_particles:
                t = particle["age"] / particle["life"]
                fade = max(0.0, 1.0 - t)
                alpha = int(200 * fade)
                size = max(1, int(particle["size"] * (0.6 + 0.4 * fade)))
                if particle.get("variant") == "muzzle":
                    color = (
                        255,
                        int(180 + 60 * (1.0 - particle["intensity"])),
                        int(80 + 40 * (1.0 - particle["intensity"])),
                        alpha,
                    )
                else:
                    color = (
                        int(140 + 60 * (1.0 - particle["intensity"] * 0.5)),
                        int(200 - 80 * particle["intensity"]),
                        255,
                        alpha,
                    )
                if alpha <= 0:
                    continue
                center = (int(particle["pos"].x), int(particle["pos"].y))
                pygame.draw.circle(surface, color, center, size)

        def _draw_powerup_effects(self, surface):
            if not self.player.alive:
                return
            cx = int(self.player.position.x)
            cy = int(self.player.position.y)
            base_radius = int(self.player.radius)

            if self.shield_timer > 0:
                pulse = (math.sin(self.elapsed * 5.5) + 1.0) * 0.5
                outer_radius = int(base_radius * (1.7 + 0.15 * pulse))
                glow_layers = 5
                for i in range(glow_layers):
                    t = i / float(glow_layers)
                    radius = outer_radius - i * 3
                    alpha = int(130 * (1.0 - t) * (0.6 + 0.4 * pulse))
                    color = (80, 230, 255, alpha)
                    if radius > base_radius + 2:
                        pygame.draw.circle(surface, color, (cx, cy), radius, 2)
                inner_color = (40, 150, 255, 70)
                pygame.draw.circle(surface, inner_color, (cx, cy), base_radius + 6)
                # floating shield nodes
                node_radius = outer_radius - 6
                for i in range(6):
                    angle = self.elapsed * 0.9 + i * (math.tau / 6)
                    nx = cx + math.cos(angle) * node_radius
                    ny = cy + math.sin(angle) * node_radius
                    pygame.draw.circle(surface, (200, 255, 255, 120), (int(nx), int(ny)), 3)

            if self.double_shot_timer > 0:
                spin = self.elapsed * 4.2
                orbit_radius = base_radius + 22
                petals = 4
                for i in range(petals):
                    angle = spin + i * (math.tau / petals)
                    px = cx + math.cos(angle) * orbit_radius
                    py = cy + math.sin(angle) * orbit_radius
                    color = (255, 160, 235, 160)
                    pygame.draw.circle(surface, color, (int(px), int(py)), 5)
                    tail_x = cx + math.cos(angle) * (orbit_radius - 10)
                    tail_y = cy + math.sin(angle) * (orbit_radius - 10)
                    pygame.draw.line(surface, (255, 200, 245, 120), (int(px), int(py)), (int(tail_x), int(tail_y)), 2)
                cross_color = (255, 190, 250, 140)
                pygame.draw.line(surface, cross_color, (cx - base_radius - 12, cy), (cx + base_radius + 12, cy), 2)
                pygame.draw.line(surface, cross_color, (cx, cy - base_radius - 12), (cx, cy + base_radius + 12), 2)

            if self.rapid_fire_timer > 0:
                plume_height = int(26 + 6 * math.sin(self.elapsed * 10.0))
                top_y = cy - base_radius - plume_height
                base_y = cy - base_radius + 2
                flame_color = (255, 210, 90, 180)
                inner_color = (255, 255, 150, 120)
                polygon = [
                    (cx - 6, base_y),
                    (cx + 6, base_y),
                    (cx + 2, top_y),
                    (cx - 2, top_y),
                ]
                pygame.draw.polygon(surface, flame_color, polygon)
                pygame.draw.line(surface, inner_color, (cx, base_y), (cx, top_y), 3)
                spark_count = 4
                for i in range(spark_count):
                    t = i / float(spark_count)
                    sx = cx + self.random.uniform(-4, 4)
                    sy = base_y - t * plume_height
                    pygame.draw.circle(surface, (255, 235, 160, 140), (int(sx), int(sy)), 2)

        def _spawn_muzzle_flash(self, direction):
            if self.game_over:
                return
            dir_vec = Vec2(direction)
            if dir_vec.length_squared() == 0:
                dir_vec = Vec2(0, -1)
            dir_norm = dir_vec.normalized()
            perp = Vec2(-dir_norm.y, dir_norm.x)
            base_forward = dir_norm * (self.player.radius * 0.2)
            lateral_offset = self.player.radius * 0.8
            speed_side = 180.0
            speed_back = 120.0
            for side in (-1, 1):
                offset = perp * (lateral_offset * side)
                origin = self.player.position + base_forward + offset
                for _ in range(3):
                    jitter = Vec2(self.random.uniform(-4, 4), self.random.uniform(-4, 4))
                    side_push = offset.normalized() * self.random.uniform(speed_side * 0.7, speed_side * 1.2)
                    backward = (-dir_norm) * self.random.uniform(speed_back * 0.5, speed_back * 1.1)
                    inherit = self.player.velocity * 0.4
                    velocity = side_push + backward + inherit
                    particle = {
                        "pos": Vec2(origin + jitter),
                        "vel": velocity,
                        "age": 0.0,
                        "life": self.random.uniform(0.14, 0.28),
                        "size": self.random.uniform(4.5, 7.5),
                        "intensity": 1.0,
                        "variant": "muzzle",
                    }
                    self.thruster_particles.append(particle)
            # Spawn a short flare following firing direction for added punch
            flare_origin = self.player.position + dir_norm * (self.player.radius * 0.9)
            for _ in range(2):
                jitter = Vec2(self.random.uniform(-2, 2), self.random.uniform(-2, 2))
                velocity = dir_norm * self.random.uniform(80, 150)
                particle = {
                    "pos": Vec2(flare_origin + jitter),
                    "vel": velocity,
                    "age": 0.0,
                    "life": self.random.uniform(0.08, 0.14),
                    "size": self.random.uniform(3.0, 5.0),
                    "intensity": 1.0,
                    "variant": "muzzle",
                }
                self.thruster_particles.append(particle)

        def _trigger_shake(self, strength=8.0, duration=0.25):
            self.shake_strength = max(self.shake_strength, strength)
            self.shake_timer = max(duration, 0.001)
            self.shake_duration = self.shake_timer

        def _update_camera_shake(self, dt):
            if self.shake_timer > 0.0:
                self.shake_timer = max(0.0, self.shake_timer - dt)
                decay = self.shake_timer / self.shake_duration if self.shake_duration > 0 else 0.0
                magnitude = self.shake_strength * decay
                self.camera_offset.set(
                    self.random.uniform(-1.0, 1.0) * magnitude,
                    self.random.uniform(-1.0, 1.0) * magnitude,
                )
                if self.shake_timer == 0:
                    self.camera_offset.set(0, 0)
                    self.shake_strength = 0.0
            else:
                self.camera_offset.set(0, 0)
                self.shake_strength = 0.0


        def _load_first_sprite(self, candidates, scale=1.0, fallback_color=(255, 255, 255)):
            for relative in candidates:
                sprite = self._load_image(relative, scale)
                if sprite is not None:
                    return sprite
            return self._placeholder_sprite(fallback_color)

        def _load_sprite_folder(self, relative_folder, scale=1.0, fallback_color=(255, 255, 255)):
            folder = os.path.join(self.asset_root, relative_folder) if self.asset_root else relative_folder
            sprites = []
            if os.path.isdir(folder):
                for name in sorted(os.listdir(folder)):
                    if not name.lower().endswith((".png", ".webp", ".jpg")):
                        continue
                    path = os.path.join(folder, name)
                    sprite = self._load_image(path, scale, absolute_path=True)
                    if sprite is not None:
                        sprites.append(sprite)
            if not sprites:
                sprites.append(self._placeholder_sprite(fallback_color))
            return sprites

        def _load_image(self, relative_path, scale=1.0, absolute_path=False):
            path = relative_path if absolute_path or not self.asset_root else os.path.join(self.asset_root, relative_path)
            if not os.path.exists(path):
                return None
            try:
                image = pygame.image.load(path).convert_alpha()
            except Exception:
                return None
            if scale != 1.0:
                width = max(1, int(image.get_width() * scale))
                height = max(1, int(image.get_height() * scale))
                image = pygame.transform.smoothscale(image, (width, height))
            return image

        def _scale_ship_sprite(self, sprite, profile):
            scale_hint = float(profile.get("scale", 1.0))
            max_width = profile.get("max_runtime_width")
            result = sprite
            if scale_hint != 1.0:
                result = self._scale_surface(result, scale_hint)
            if max_width:
                result = self._scale_surface_to_width(result, max_width)
            return result

        def _scale_surface(self, surface, factor):
            if factor == 1.0 or factor <= 0:
                return surface
            width = max(1, int(surface.get_width() * factor))
            height = max(1, int(surface.get_height() * factor))
            if width == surface.get_width() and height == surface.get_height():
                return surface
            return pygame.transform.smoothscale(surface, (width, height))

        def _scale_surface_to_width(self, surface, max_width):
            if not max_width or surface.get_width() <= max_width:
                return surface
            factor = float(max_width) / float(surface.get_width())
            return self._scale_surface(surface, factor)

        def _placeholder_sprite(self, color):
            surface = pygame.Surface((48, 32), pygame.SRCALPHA)
            surface.fill((*color, 255))
            pygame.draw.rect(surface, (10, 10, 16), surface.get_rect(), 2)
            return surface
