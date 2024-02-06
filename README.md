# Autonomous Racing: Completing Laps with LiDAR

---

## Overview

The primary objective of this project is to develop a sophisticated autonomous racing system that enables a car to complete laps around a race track with precision and efficiency. We achieve this by integrating a LiDAR sensor system with advanced neural network algorithms to enable real-time decision-making and navigation.
 
## Features
* LiDAR Sensor Integration: Our system simulates a LiDAR sensor to provide accurate and detailed environmental data, allowing the vehicle to perceive the track layout, obstacles, and other vehicles. We simulated the LiDAR sensor by emitting 5 rays with different angles (-90, -45, 0, 45, 90).
* Neural Network Decision Making: A neural network architecture processes LiDAR data to make decisions regarding vehicle speed, steering and maneuvering, ensuring the vehicle follows the optimal racing line and avoids collisions.

## The Model
* The model input is the distance travelled by the 5 LiDAR rays.
* The output of the model will be the next decision of the vehicle (GAS/ROTATE RIGHT/ROTATE LEFT)
* The model is build from 2 fully connected layers.

## Training
* I chose to use a genetic optimization algorithm. For the first iteration, I used 100 cars with a random model (2 random matrices). Then, for each iteration, I chose the best 20 vehicles, according to the distance travelled by each car, and created permutations from their matrices.
* During the training process, I set the LiDAR such that it will ignore other vehicles. This was done in order to get a faster converges.
* A video of the training process: [[Learning process](https://drive.google.com/file/d/1LM4swQw5MVwdM_OmyDwrS0ZMYzKrh5ZO/view?usp=sharing)]

## Evaluation
* A video of the trained car with it's LiDAR rays: [[Best car with LiDAR on](https://drive.google.com/file/d/1I3fvv5NgbNeY34BsLonrbTZNmd56p1kM/view?usp=sharing)]