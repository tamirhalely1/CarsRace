from carsgame import (Car, ACTIVATE_NITRO, DROP_OIL, GAS, ROTATE_LEFT,
                      ROTATE_RIGHT, GameState, CarController, USE_COMPLEX_TRACK, TRIVIAL_INNER_BOUNDARY,
                      TRIVIAL_OUTER_BOUNDARY, COMPLEX_INNER_BOUNDARY, COMPLEX_OUTER_BOUNDARY, screen, spills,
                      OIL_SPILL_RADIUS)
import math
import numpy as np

LOOK_AHEAD = 40


class model:
    def __init__(self, number_of_rays, n_outputs, mode="test"):
        self.number_of_rays = number_of_rays
        self.n_outputs = n_outputs
        self.fc1 = np.random.random((6, number_of_rays))
        self.fc2 = np.random.random((n_outputs, 6))
        if mode == "test":
            self.load_model()

    def forward(self, distances):
        output = self.fc2.dot(self.fc1.dot(distances))
        return output

    def load_model(self):
        self.fc1 = np.array([[1.014111972587649069e-01, 7.746883909364062903e-01, 8.343981843895461603e-01, 3.575327227672494557e-01, 3.015828182966916460e-01],
                            [9.177051566686806883e-01, 4.061827360506713447e-01, 2.160795063474153510e-01, 6.780013222126936023e-01, 1.209207966070036111e-01],
                            [7.997020553251130703e-01, 7.408187099807955756e-01, 8.585668725229023135e-02, 5.020458533409768442e-01, 9.427094185157677275e-01],
                            [5.948065360616305863e-02, 8.686825788869964038e-01, 5.208985664311586161e-01, 7.247371915430194100e-01, 2.299411925469467821e-01],
                            [9.887251742145131139e-01, 9.540493027998790954e-01, 7.058581155923930872e-01, 2.099978612796381539e-01, 3.205483824973116569e-01],
                            [5.373498435707497745e-01, 1.827603489732240183e-01, 6.751542570410519195e-01, 6.837794646805991361e-01, 7.648663693396230423e-01]])
        self.fc2 = np.array([[7.087575131095626979e-01, 2.379492063859701689e-01, 2.685721282874466986e-01, 4.975159867869147767e-01, 6.437370769980713670e-01, 9.516046996718394713e-01],
                            [2.478115096033378650e-01, 1.426739069451077313e-01, 5.811265673405490162e-01, 9.597386858786177699e-01, 6.393905164965194565e-01, 6.920066563277772476e-01],
                            [5.357431864842585600e-01, 7.823839523254594308e-02, 5.919485909565859183e-01, 3.853004393723532539e-01, 3.861786347994800028e-01, 2.620047183804348201e-01]])

    def save_model(self, checkpoint):
        np.savetxt(f'fc1_{checkpoint}.txt', self.fc1, delimiter=',')
        np.savetxt(f'fc2_{checkpoint}.txt', self.fc2, delimiter=',')


class CPUCarController(CarController):
    def __init__(self, car_id: str, mode="test"):
        self.car_id = car_id
        self.previousPosition = None
        self.current_state = 0
        self.model = model(number_of_rays=5, n_outputs=3, mode=mode)
        self.mode = mode
        self.end_positions = []

    @property
    def id(self) -> str:
        if self.mode == "test":
            return "tamir_h"
        else:
            return self.car_id

    def decide_what_to_do_next(self, gameState: GameState, mode="test") -> str:
        # TODO: Implement this function
        my_car = next(car for car in gameState.cars if car.name == self.id)
        scanning_angles = [math.radians(-90), math.radians(-45), 0, math.radians(45), math.radians(90)]
        look_ahead_angles = [1 for i in range(len(scanning_angles))]
        self.end_positions = [0 for i in range(len(look_ahead_angles))]
        distance_from_obstacle = []
        for i in range(len(scanning_angles)):
            while self.no_collision(my_car, look_ahead_angles, scanning_angles, i, gameState, mode):
                look_ahead_angles[i] += 1
            laser_x = my_car.rect.centerx + look_ahead_angles[i] * math.cos(scanning_angles[i] + my_car.angle)
            laser_y = my_car.rect.centery + look_ahead_angles[i] * math.sin(scanning_angles[i] + my_car.angle)
            self.end_positions[i] = (laser_x, laser_y)
            distance_from_obstacle.append(math.sqrt((my_car.rect.centerx - laser_x) ** 2 + (my_car.rect.centery - laser_y) ** 2))
        distance_from_obstacle = np.transpose(np.array([distance_from_obstacle]))
        output = self.model.forward(distance_from_obstacle)
        actions = [GAS, ROTATE_RIGHT, ROTATE_LEFT]
        argmax = np.argmax(output)
        chosen_action = actions[argmax]
        return chosen_action

    def no_collision(self, my_car, look_ahead_angles, scanning_angles, i, game_state, mode):
        laser_x = my_car.rect.centerx + look_ahead_angles[i] * math.cos(scanning_angles[i] + my_car.angle)
        laser_y = my_car.rect.centery + look_ahead_angles[i] * math.sin(scanning_angles[i] + my_car.angle)
        no_collision = my_car.is_on_track(laser_x, laser_y)
        if mode == "test":
            for j in range(len(game_state.cars) - 1):
                car = game_state.cars[j]
                rect_x_start = car.rect.centerx
                rect_x_stop = car.rect.centerx + car.rect.width / 2
                rect_y_start = car.rect.centery
                rect_y_stop = car.rect.centery + car.rect.height / 2
                if rect_x_start < laser_x < rect_x_stop and rect_y_start < laser_y < rect_y_stop:
                    no_collision = False

        return no_collision

