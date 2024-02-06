import time
import numpy as np
import pygame
import math
import random
import os
import importlib
import inspect
from abc import ABC, abstractmethod
import matplotlib.colors
import numpy

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800
TRACK_COLOR = (0, 255, 0)
CAR_COLOR = (255, 0, 0)
WRONG_DIR_COLOR = CAR_COLOR
BG_COLOR = (255, 255, 255)
START_LINE_COLOR = (255, 255, 0)
LAP_COUNT = 4
INITIAL_MISSILE_COUNT = 8

INITIAL_CAR_SPEED = 0
CAR_REGULAR_MAX_SPEED = 4
CHECKPOINT_RADIUS = 10
DISTANCE_FROM_CHECKPOINT = 60
NITRO_SPEED = 3
NITRO_DURATION = 2000
GAS_SPEED_INCREASE = 0.005
INCLUDE_ONLY_NON_CPU_CARS = False
MISSILE_HIT_EFFECT_DURATION = 1000
SHOULD_DRAW_CHECKPOINTS = False
TURN_LASER_ON = True
NUMBER_OF_CARS = 1

OIL_SPILL_DURATION = 2000
OIL_SPILL_RADIUS = 25
OIL_SPILL_COLOR = (0, 0, 0)

ROTATE_RIGHT = "ROTATE_RIGHT"
ROTATE_LEFT = "ROTATE_LEFT"
GAS = "GAS"
DROP_OIL = "DROP_OIL"
ACTIVATE_NITRO = "ACTIVATE_NITRO"
SHOOT_MISSILE = "SHOOT_MISSILE"
MISSILE_SHOT_COOLDOWN = 500
MISSILE_SPEED = 10
MISSILE_LIFETIME = 5000  # 5 seconds

USE_COMPLEX_TRACK = False

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Racing Game")
clock = pygame.time.Clock()
leaderboardFont = pygame.font.SysFont(None, 35)
carNameFont = pygame.font.SysFont(None, 25)

TRIVIAL_INNER_BOUNDARY = [
    (150, 100),
    (650, 100),
    (1050, 250),
    (850, 400),
    (150, 400),
    (100, 250),
]

TRIVIAL_OUTER_BOUNDARY = [
    (50, 50),
    (750, 50),
    (1200, 250),
    (950, 450),
    (50, 450),
    (0, 250),
]

COMPLEX_INNER_BOUNDARY = [
    (150, 100),
    (650, 100),
    (1050, 250),
    (850, 350),
    (750, 250),
    (180, 400),
    (260, 300),
    (150, 250),
]

COMPLEX_OUTER_BOUNDARY = [
    (50, 50),
    (750, 50),
    (1200, 250),
    (950, 450),
    (750, 350),
    (50, 460),
    (160, 300),
    (50, 250),
]

# If using complex track, use the complex boundaries, otherwise use the trivial ones
INNER_BOUNDARY = COMPLEX_INNER_BOUNDARY if USE_COMPLEX_TRACK else TRIVIAL_INNER_BOUNDARY
OUTER_BOUNDARY = COMPLEX_OUTER_BOUNDARY if USE_COMPLEX_TRACK else TRIVIAL_OUTER_BOUNDARY

def get_line_length(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Generating CHECKPOINTS programmatically
CHECKPOINTS = []
for i in range(len(OUTER_BOUNDARY)):
    x = (OUTER_BOUNDARY[i][0] + INNER_BOUNDARY[i][0]) // 2
    y = (OUTER_BOUNDARY[i][1] + INNER_BOUNDARY[i][1]) // 2
    CHECKPOINTS.append((x, y))

new_checkpoint = []
for i in range(len(CHECKPOINTS)):
    next = (i + 1) % len(CHECKPOINTS)
    x1 = CHECKPOINTS[i][0]
    y1 = CHECKPOINTS[i][1]
    x2 = CHECKPOINTS[next][0]
    y2 = CHECKPOINTS[next][1]
    if x1 == x2:
        m = 10e6
    else:
        m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    line_length = get_line_length(x1, y1, x2, y2)
    increment_line_length = line_length / 10
    if x2 > x1:
        increment_line_length *= 1
    else:
        increment_line_length *= -1
    for j in range(10):
        new_x = x1 + j * increment_line_length * np.cos(np.arctan(m))
        new_y = m * (x1 + j * increment_line_length * np.cos(np.arctan(m))) + b
        new_checkpoint.append((new_x, new_y))
CHECKPOINTS = new_checkpoint

#Move the first checkpoint to the end of the list
firstCheckpoint = CHECKPOINTS[0]
CHECKPOINTS.remove(firstCheckpoint)
CHECKPOINTS.append(firstCheckpoint)


spills = []
cars = []
inner_surface_for_collision_checks = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
outer_surface_for_collision_checks = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
pygame.draw.polygon(outer_surface_for_collision_checks, (0, 0, 0), OUTER_BOUNDARY)
pygame.draw.polygon(inner_surface_for_collision_checks, (0, 0, 0), INNER_BOUNDARY)


class GameState:
    def __init__(self, cars,spills):
        self.cars = cars
        self.spills = spills


class CarController(ABC):
    @abstractmethod
    def decide_what_to_do_next(self, gamestate: GameState) -> str:
        pass


def load_car_controllers_from_directory():
    student_car_controllers = []
    directory = "car-definitions"

    for file in os.listdir(directory):
        if file.endswith("-h.py"):
            file_path = os.path.join(directory, file)
            spec = importlib.util.spec_from_file_location("student_car_module", file_path)
            student_car_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(student_car_module)

            student_car_class = None
            car_controller_class = None
            for name, obj in inspect.getmembers(student_car_module):
                if inspect.isclass(obj):
                    if hasattr(obj, 'decide_what_to_do_next'):
                        student_car_class = obj
                        break

            if student_car_class is not None:
                for i in range(NUMBER_OF_CARS):
                    student_car_controller = student_car_class(str(i), "train")
                    if student_car_controller.id.startswith('cpu') and INCLUDE_ONLY_NON_CPU_CARS:
                        continue
                    student_car_controllers.append(student_car_controller)

    return student_car_controllers


def dot_product(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1]


def track_direction_at_point(x, y):
    closest_points = sorted(OUTER_BOUNDARY, key=lambda point: (point[0] - x) ** 2 + (point[1] - y) ** 2)[:2]
    dir_vector = (closest_points[1][0] - closest_points[0][0], closest_points[1][1] - closest_points[0][1])
    magnitude = math.sqrt(dir_vector[0] ** 2 + dir_vector[1] ** 2)
    return (dir_vector[0] / magnitude, dir_vector[1] / magnitude)





class Missile:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.creation_time = pygame.time.get_ticks()

    def move(self):
        self.x += MISSILE_SPEED * math.cos(self.angle)
        self.y += MISSILE_SPEED * math.sin(self.angle)

    def is_expired(self):
        return pygame.time.get_ticks() - self.creation_time > MISSILE_LIFETIME

    def draw(self):
        # if the missile has left the screen, don't draw it
        if self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT:
            return
        pygame.draw.circle(screen, (200, 0, 0), (int(self.x), int(self.y)), 5)


class Spill:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.creation_time = pygame.time.get_ticks()

    def draw(self):
        pygame.draw.circle(screen, OIL_SPILL_COLOR, (self.x, self.y), OIL_SPILL_RADIUS)

    def is_expired(self):
        return pygame.time.get_ticks() - self.creation_time > OIL_SPILL_DURATION



class Car:
    def __init__(self, name, controller):
        self.image = pygame.image.load("car.png")
        self.image = self.tint_image(self.image)
        self.rect = self.image.get_rect()
        self.place_on_track()
        self.speed = INITIAL_CAR_SPEED
        self.angle = 0  # Start driving to the right
        self.laps = 0

        self.name = name
        self.next_checkpoint = 0  # index of the next checkpoint to cross
        self.checkpoints_crossed = 0  # how many checkpoints the car has crossed so far
        self.has_oil_spill = True
        self.on_oil_spill = False  # Is the car currently on an oil spill?
        self.nitrosLeft = 4
        self.usingNitro = False
        self.nitroUsedTime = pygame.time.get_ticks()
        self.regularSpeed = INITIAL_CAR_SPEED
        self.controller = controller
        # Cache car name text
        self.name_text = carNameFont.render(self.name, True, (0, 0, 0))
        self.missiles = []
        self.missile_count = INITIAL_MISSILE_COUNT
        self.hit_time = None
        self.missileShotTime = pygame.time.get_ticks()

    def reset(self, name, controller, new_generation):
        self.image = pygame.image.load("car.png")
        self.image = self.tint_image(self.image)
        self.rect = self.image.get_rect()
        self.place_on_track()
        self.speed = INITIAL_CAR_SPEED
        self.angle = 0  # Start driving to the right
        self.laps = 0

        self.name = name
        self.next_checkpoint = 0  # index of the next checkpoint to cross
        self.checkpoints_crossed = 0  # how many checkpoints the car has crossed so far
        self.has_oil_spill = True
        self.on_oil_spill = False  # Is the car currently on an oil spill?
        self.nitrosLeft = 4
        self.usingNitro = False
        self.nitroUsedTime = pygame.time.get_ticks()
        self.regularSpeed = INITIAL_CAR_SPEED
        self.controller = controller
        new_fc1, new_fc2 = new_generation
        self.controller.model.fc1 = new_fc1
        self.controller.model.fc2 = new_fc2
        # Cache car name text
        self.name_text = carNameFont.render(self.name, True, (0, 0, 0))
        self.missiles = []
        self.missile_count = INITIAL_MISSILE_COUNT
        self.hit_time = None
        self.missileShotTime = pygame.time.get_ticks()

    def tint_image(self, img):
        # Clone the image to not modify the original one
        tinted_img = img.copy()

        # Create an empty array to store the tinted pixels
        pixels = pygame.surfarray.pixels3d(tinted_img)

        # Convert the RGB values to HSV
        hsv_pixels = matplotlib.colors.rgb_to_hsv(pixels / 255.0)

        # Shift the hue by a random value between 0 and 1
        hue_shift = random.random()
        hsv_pixels[..., 0] = (hsv_pixels[..., 0] + hue_shift) % 1.0

        # Convert the HSV values back to RGB
        rgb_pixels = matplotlib.colors.hsv_to_rgb(hsv_pixels)

        # Update the tinted image with the new RGB values
        pygame.surfarray.blit_array(tinted_img, (rgb_pixels * 255).astype(numpy.uint8))

        return tinted_img
    
    def shoot_missile(self):
        if self.missile_count > 0 and pygame.time.get_ticks() - self.missileShotTime > MISSILE_SHOT_COOLDOWN:
            missile = Missile(self.rect.centerx, self.rect.centery, self.angle)
            self.missiles.append(missile)
            self.missile_count -= 1
            self.missileShotTime = pygame.time.get_ticks()

    def place_on_track(self):
        while True:
            randomX = random.randint(OUTER_BOUNDARY[0][0], INNER_BOUNDARY[0][0])
            randomY = random.randint(OUTER_BOUNDARY[0][1], INNER_BOUNDARY[0][1])

            if self.is_on_track(randomX, randomY):
                self.rect.centerx = randomX
                self.rect.centery = randomY
                return

    def update(self):
        chosenAction = self.controller.decide_what_to_do_next(GameState(cars, spills), "train")

        # Handle chosen action
        if (chosenAction == SHOOT_MISSILE):
            self.shoot_missile()
        if chosenAction == ACTIVATE_NITRO and self.nitrosLeft > 0 and not self.usingNitro:
            self.usingNitro = True
            self.nitrosLeft -= 1
        elif chosenAction == DROP_OIL and self.has_oil_spill:
            spills.append(
                Spill(self.rect.centerx - 40 * math.cos(self.angle), self.rect.centery - 40 * math.sin(self.angle)))
            self.has_oil_spill = False
        elif (chosenAction == ROTATE_RIGHT):
            self.angle += math.pi / 16
        elif (chosenAction == ROTATE_LEFT):
            self.angle -= math.pi / 16
        elif (chosenAction == GAS):
            self.regularSpeed += GAS_SPEED_INCREASE
            if self.regularSpeed > CAR_REGULAR_MAX_SPEED:
                self.regularSpeed = CAR_REGULAR_MAX_SPEED

        prev_x, prev_y = car.rect.centerx, car.rect.centery

        self.move_forward()

        # self.handle_collisions()  # Check and handle collisions with other cars

        move_direction = (self.rect.centerx - prev_x, self.rect.centery - prev_y)
        magnitude = math.sqrt(move_direction[0] ** 2 + move_direction[1] ** 2)
        if magnitude != 0:
            move_direction = (move_direction[0] / magnitude, move_direction[1] / magnitude)
            track_dir = track_direction_at_point(self.rect.centerx, self.rect.centery)

        checkpoint_x, checkpoint_y = CHECKPOINTS[self.next_checkpoint]
        if math.sqrt((self.rect.centerx - checkpoint_x) ** 2 + (
                self.rect.centery - checkpoint_y) ** 2) < DISTANCE_FROM_CHECKPOINT:
            self.checkpoints_crossed += 1
            self.next_checkpoint = (self.next_checkpoint + 1) % len(CHECKPOINTS)
            # print(f"Checkpoint {self.checkpoints_crossed} finished by car {self.name}")

        # if self.checkpoints_crossed == len(CHECKPOINTS):
        # print(f"All checkpoints finished by car {self.name}")
        # Check if the car has crossed the start line
        if prev_x < INNER_BOUNDARY[0][0] and self.rect.centerx >= INNER_BOUNDARY[0][
            0] and self.checkpoints_crossed == len(CHECKPOINTS):
            if not self.has_oil_spill:  # Give an oil spill every lap
                self.has_oil_spill = True
            self.laps += 1
            # self.checkpoints_crossed = 0

        # Check if the car is on an oil spill
        self.on_oil_spill = False
        for spill in spills:
            distance_to_spill = math.sqrt((self.rect.centerx - spill.x) ** 2 + (self.rect.centery - spill.y) ** 2)
            if distance_to_spill <= OIL_SPILL_RADIUS:
                self.on_oil_spill = True
                break

        # After 2 seconds nitro should stop
        if self.usingNitro and pygame.time.get_ticks() - self.nitroUsedTime > NITRO_DURATION:
            self.usingNitro = False

        if self.usingNitro and not self.on_oil_spill:
            self.speed = NITRO_SPEED * self.regularSpeed
        # elif self.on_oil_spill:
        #     self.speed = 0.2 * self.regularSpeed
        else:
            self.speed = self.regularSpeed

        # Remove expired missiles
        self.missiles = [m for m in self.missiles if not m.is_expired()]

        # Check if hit by a missile
        if self.hit_time and pygame.time.get_ticks() - self.hit_time > MISSILE_HIT_EFFECT_DURATION:
            self.hit_time = None  # Reset hit time
        if self.hit_time:
            self.regularSpeed = 0  # If hit by a missile, set speed to 0 for 3 seconds

    def move_forward(self):
        futureX = self.rect.centerx + self.speed * math.cos(self.angle)
        futureY = self.rect.centery + self.speed * math.sin(self.angle)

        if self.is_on_track(futureX, futureY):
            self.rect.centerx = futureX
            self.rect.centery = futureY

    def handle_collisions(self):
        for other_car in cars:
            if other_car != self and self.rect.colliderect(other_car.rect):
                overlap_x = other_car.rect.centerx - self.rect.centerx
                overlap_y = other_car.rect.centery - self.rect.centery
                overlap_distance = math.sqrt(overlap_x ** 2 + overlap_y ** 2)

                # Calculate the unit vector of overlap direction
                if overlap_distance != 0:
                    overlap_direction = (overlap_x / overlap_distance, overlap_y / overlap_distance)
                else:
                    overlap_direction = (0, 0)

                # Move both cars away from each other based on the overlap
                move_distance = overlap_distance / 2

                # Move the car only if the new position is on track
                new_x = self.rect.centerx - overlap_direction[0] * move_distance
                new_y = self.rect.centery - overlap_direction[1] * move_distance
                if self.is_on_track(new_x, new_y):
                    self.rect.centerx = new_x
                    self.rect.centery = new_y

                other_car_new_x = other_car.rect.centerx + overlap_direction[0] * move_distance
                other_car_new_y = other_car.rect.centery + overlap_direction[1] * move_distance
                if self.is_on_track(other_car_new_x, other_car_new_y):
                    other_car.rect.centerx = other_car_new_x
                    other_car.rect.centery = other_car_new_y

                # Get a random number from 8 to 11 inclusive
                randomAngleDivision = random.randint(8, 11)
                # Adjust angles to simulate the push effect (you can fine-tune this)
                self.angle += math.pi / randomAngleDivision
                other_car.angle -= math.pi / randomAngleDivision

    def is_on_track(self, x, y):
        return self.is_inside_outer_boundary(x, y) and not self.is_inside_inner_boundary(x, y)

    def is_inside_outer_boundary(self, x, y):
        # If the pixel is out of screen boundaries, return false
        if x < 0 or x > SCREEN_WIDTH or y < 0 or y > SCREEN_HEIGHT:
            return False
        return outer_surface_for_collision_checks.get_at((int(x), int(y))) == (
        0, 0, 0, 255)  # Check if the pixel at (x, y) is black

    def is_inside_inner_boundary(self, x, y):
        # If the pixel is out of screen boundaries, return false
        if x < 0 or x > SCREEN_WIDTH or y < 0 or y > SCREEN_HEIGHT:
            return False

        return inner_surface_for_collision_checks.get_at((int(x), int(y))) == (
        0, 0, 0, 255)  # Check if the pixel at (x, y) is black

    def draw(self):
        rotated_image = pygame.transform.rotate(self.image, -math.degrees(self.angle))
        rotated_rect = rotated_image.get_rect(center=self.rect.center)
        screen.blit(rotated_image, rotated_rect)
        screen.blit(self.name_text, (self.rect.x, self.rect.y + self.rect.height))


def display_leaderboard():
    sorted_cars = sorted(cars, key=lambda car: car.laps * 100 + car.checkpoints_crossed, reverse=True)[:5]
    y_start = 10

    for i, car in enumerate(sorted_cars):
        checkpointPercentage = round(car.checkpoints_crossed / len(CHECKPOINTS) * 100)
        text = leaderboardFont.render(f"{i + 1}. {car.name} - {car.laps} laps {checkpointPercentage}%", True, (0, 0, 0))
        y_start += 40
        screen.blit(text, (SCREEN_WIDTH - 300, y_start))


car_controllers = load_car_controllers_from_directory()
for car_controller in car_controllers:
    carControllerId = car_controller.id
    car = Car(carControllerId, car_controller)
    cars.append(car)


def generative_optimizer(optimal_cars):
    new_generation = []
    for i in range(90):
        parent1_random_index = random.randint(0, len(optimal_cars) - 1)
        parent2_random_index = random.randint(0, len(optimal_cars) - 1)
        parent1 = optimal_cars[parent1_random_index]
        parent1_fc1, parent1_fc2 = parent1
        parent2 = optimal_cars[parent2_random_index]
        parent2_fc1, parent2_fc2 = parent2

        child_fc1 = np.zeros(parent1_fc1.shape)
        child_fc2 = np.zeros(parent1_fc2.shape)
        parent1_p = 0.4
        if parent1_random_index < parent2_random_index:
            parent1_p = 0.6
        for j in range(len(child_fc1)):
            for k in range(len(child_fc1[j])):
                random_number = random.random()
                if random_number < parent1_p:
                    child_fc1[j][k] = parent1_fc1[j][k]
                else:
                    child_fc1[j][k] = parent2_fc1[j][k]
        for j in range(len(child_fc2)):
            for k in range(len(child_fc2[j])):
                random_number = random.random()
                if random_number < parent1_p:
                    child_fc2[j][k] = parent1_fc2[j][k]
                else:
                    child_fc2[j][k] = parent2_fc2[j][k]

        new_generation.append((child_fc1, child_fc2))
    return optimal_cars + new_generation



# Game loop
running = True
game_over = False
seconds = time.time()
reset_time = 100
cars_100list = []
new_generation = [(np.random.random((6, 5)), np.random.random((3, 6))) for i in range(100)]
iteration = 0
while running:
    if time.time() - seconds > reset_time:
        iteration += 1
        for i in range(len(cars)):
            car = cars[i]
            cars_100list.append((car, car.checkpoints_crossed))
            if iteration <= 4:
                car.reset(car.name, car.controller, new_generation[iteration * 20 + i])
        seconds = time.time()
        print(f'Cars list length: {len(cars_100list)}')
        if len(cars_100list) == 100:
            reset_time = min(reset_time + 5, 60)
            optimal_cars = sorted(cars_100list, key=lambda item: item[1])[-10:]
            print("Max Checkpoints:", optimal_cars[-1][1])
            best_fc1, best_fc2 = optimal_cars[-1][0].controller.model.fc1, optimal_cars[-1][0].controller.model.fc2
            print("Saving best model...")
            optimal_cars[-1][0].controller.model.save_model(optimal_cars[-1][1])
            print("Done!")
            for j in range(len(optimal_cars)):
                optimal_cars[j] = optimal_cars[j][0]
            # print("Max checkpoints", max(cars_l.values()))
            for j in range(len(optimal_cars)):
                optimal_cars[j] = (optimal_cars[j].controller.model.fc1, optimal_cars[j].controller.model.fc2)
            new_generation = generative_optimizer(optimal_cars)
            cars_100list = []
            iteration = 0
            for j in range(len(cars)):
                car = cars[j]
                car.reset(car.name, car.controller, new_generation[j])
    screen.fill(BG_COLOR)
    pygame.draw.polygon(screen, TRACK_COLOR, OUTER_BOUNDARY)
    pygame.draw.polygon(screen, BG_COLOR, INNER_BOUNDARY)
    pygame.draw.line(screen, START_LINE_COLOR, OUTER_BOUNDARY[0], INNER_BOUNDARY[0], 5)
    if TURN_LASER_ON:
        for i in range(len(cars[0].controller.end_positions)):
            pygame.draw.line(screen, (255, 0, 0), (cars[0].rect.centerx, cars[0].rect.centery),
                         (cars[0].controller.end_positions[i][0], cars[0].controller.end_positions[i][1]), 3)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    for car in cars:
        car.update()

    
    if SHOULD_DRAW_CHECKPOINTS:
        for checkpoint in CHECKPOINTS:
            pygame.draw.circle(screen, (0, 0, 255), checkpoint, CHECKPOINT_RADIUS)

    # Draw the oil spills
    for spill in spills:
        spill.draw()

    # Remove expired oil spills
    spills = [spill for spill in spills if not spill.is_expired()]

    for car in cars:
        car.draw()

    # Missile updates
    for car in cars:
        for missile in car.missiles:
            # If missile has left the scree,remove it
            if missile.x < 0 or missile.x > SCREEN_WIDTH or missile.y < 0 or missile.y > SCREEN_HEIGHT:
                car.missiles.remove(missile)
                break

            missile.move()

            for other_car in cars:
                if other_car != car and math.sqrt((other_car.rect.centerx - missile.x) ** 2 + (
                        other_car.rect.centery - missile.y) ** 2) < 20:  # 20 is approx. the size of a car
                    other_car.hit_time = pygame.time.get_ticks()
                    car.missiles.remove(missile)
                    break

    for car in cars:
        for missile in car.missiles:
            missile.draw()

    display_leaderboard()

    fps_text = pygame.font.SysFont(None, 25).render(f"FPS: {int(clock.get_fps())}", True, (0, 0, 0))
    screen.blit(fps_text, (SCREEN_WIDTH - 70, 10))

    pygame.display.flip()
    clock.tick(60)

    winners = [car for car in cars if car.laps >= LAP_COUNT]
    if winners:
        winner_name = winners[0].name
        print(f"Winner: {winner_name}")
        running = False
        game_over=True

while game_over:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = False
    
    winner_name = winners[0].name
    winner_text = pygame.font.SysFont(None, 60).render(f"Winner: {winner_name}", True, (255, 50, 20))
    screen.blit(winner_text, (SCREEN_WIDTH // 2 - winner_text.get_width() // 2, SCREEN_HEIGHT // 2 - winner_text.get_height() // 2))

    pygame.display.flip()
    clock.tick(60)
    
pygame.quit()
