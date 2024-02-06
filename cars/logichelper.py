from carsgame import Car, ACTIVATE_NITRO, DROP_OIL, GAS, ROTATE_LEFT, ROTATE_RIGHT, SHOOT_MISSILE, GameState, \
    CarController

import math
import random

LOOK_AHEAD = 40


def trivial_logic(carController: CarController, gameState: GameState) -> str:
    my_car = next(car for car in gameState.cars if car.name == carController.id)

    ahead_x = my_car.rect.centerx + LOOK_AHEAD * math.cos(my_car.angle)
    ahead_y = my_car.rect.centery + LOOK_AHEAD * math.sin(my_car.angle)

    if random.random() < 0.005:
        chosen_action = SHOOT_MISSILE
    elif my_car.nitrosLeft > 0 and not my_car.usingNitro and random.random() < 0.02:
        chosen_action = ACTIVATE_NITRO
    elif my_car.has_oil_spill and random.random() < 0.002:
        chosen_action = DROP_OIL
    elif not my_car.is_on_track(ahead_x, ahead_y):
        chosen_action = ROTATE_RIGHT
    elif random.random() < 0.002:
        chosen_action = ROTATE_LEFT
    elif random.random() < 0.001:
        chosen_action = ROTATE_RIGHT
    else:
        chosen_action = GAS
    return chosen_action

def complete_random_logic(carController: CarController, gameState: GameState) -> str:
    my_car = next(car for car in gameState.cars if car.name == carController.id)

    if random.random() < 0.9:
        chosen_action = GAS
    else:
        chosen_action = random.choice([ACTIVATE_NITRO, DROP_OIL, ROTATE_LEFT, ROTATE_RIGHT, SHOOT_MISSILE])

    return chosen_action

def straight_and_right_logic(carController: CarController, gameState: GameState) -> str:
    my_car = next(car for car in gameState.cars if car.name == carController.id)

    if random.random() < 0.98:
        chosen_action = GAS
    else:
        chosen_action = ROTATE_RIGHT

    return chosen_action