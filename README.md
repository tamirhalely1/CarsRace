Implementation of deep learning framework 

In this project, I tried to build the most ideal car that will finish the race the quickest.
I implemented a sort of LiDAR sensor code so that the vehicle emits five rays at different angles and computes the distance from the vehicle to the point of impact of the ray. The neural network I built consists of two fully connected layers. The input to the network is a column vector with five elements, each representing the value of a ray. The output of the network is the probability for each of the three actions that can be taken with the vehicle (rotate_right, rotate_left, gas).

In the first attached video, you can see the network training process. In the first iteration, the network was initialized with random parameters, and indeed, it can be observed that most vehicles rotate in place or move illogically, with only a few vehicles managing to progress along the first segment of the track. After five iterations, it can be seen that a large portion of the vehicles manage to progress along the first segment of the track and even perform their first turn. Finally, in the tenth iteration, it can be seen that several vehicles manage to complete multiple laps of the track.

In the second video, you can see the vehicle's performance after training the network together with the LiDAR rays. 


