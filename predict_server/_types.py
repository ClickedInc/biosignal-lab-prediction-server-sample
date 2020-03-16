import math
import struct


class MotionData:
    @classmethod
    def from_bytes(cls, bytes):
        def float_list_from_bytes(bytes, count, pos):
            return list(
                struct.unpack_from('>{}f'.format(count), bytes, pos)
            ), pos + 4 * count
        
        pos = 0

        timestamp = struct.unpack_from('>q', bytes, pos)[0]
        pos += 8

        left_eye_position, pos = float_list_from_bytes(bytes, 3, pos)
        right_eye_position, pos = float_list_from_bytes(bytes, 3, pos)
        head_orientation, pos = float_list_from_bytes(bytes, 4, pos)
        head_acceleration, pos = float_list_from_bytes(bytes, 3, pos)
        head_angular_velocity, pos = float_list_from_bytes(bytes, 3, pos)
        camera_projection, pos = float_list_from_bytes(bytes, 4, pos)
        right_hand_position, pos = float_list_from_bytes(bytes, 3, pos)
        right_hand_orientation, pos = float_list_from_bytes(bytes, 4, pos)
        right_hand_acceleration, pos = float_list_from_bytes(bytes, 3, pos)
        right_hand_angular_velocity, pos = float_list_from_bytes(bytes, 3, pos)

        return cls(
            timestamp,
            left_eye_position,
            right_eye_position,
            head_orientation,
            head_acceleration,
            head_angular_velocity,
            camera_projection,
            right_hand_position,
            right_hand_orientation,
            right_hand_acceleration,
            right_hand_angular_velocity
        )
    
    def __init__(self,
                 timestamp,
                 left_eye_position,
                 right_eye_position,
                 head_orientation,
                 head_acceleration,
                 head_angular_velocity,
                 camera_projection,
                 right_hand_position,
                 right_hand_orientation,
                 right_hand_acceleration,
                 right_hand_angular_velocity):
        self.timestamp = timestamp
        self.left_eye_position = left_eye_position
        self.right_eye_position = right_eye_position
        self.head_orientation = head_orientation
        self.head_acceleration = head_acceleration
        self.head_angular_velocity = head_angular_velocity
        self.camera_projection = camera_projection
        self.right_hand_position = right_hand_position
        self.right_hand_orientation = right_hand_orientation
        self.right_hand_acceleration = right_hand_acceleration
        self.right_hand_angular_velocity = right_hand_angular_velocity

    def fov(self):
        return math.atan(self.camera_projection[1]) + math.atan(-self.camera_projection[3])

    def __str__(self):
        return (
            "timestamp {0}, eye positions ({1}), ({2}), "
            "head orientation {3}, camera fov {4}, "
            "right hand position {5}, right hand orientation {6}"
        ).format(
            self.timestamp, self.left_eye_position, self.right_eye_position,
            self.head_orientation, self.fov(),
            self.right_hand_position, self.right_hand_orientation
        )

    
class PredictedData:
    def __init__(self,
                 timestamp,
                 prediction_time,
                 left_eye_position,
                 right_eye_position,
                 head_orientation,
                 camera_projection,
                 right_hand_position,
                 right_hand_orientation):
        self.timestamp = timestamp
        self.prediction_time = prediction_time
        self.left_eye_position = left_eye_position
        self.right_eye_position = right_eye_position
        self.head_orientation = head_orientation
        self.camera_projection = camera_projection
        self.right_hand_position = right_hand_position
        self.right_hand_orientation = right_hand_orientation

    def pack(self):
        return struct.pack(
            '>q22f',
            self.timestamp,
            self.prediction_time,
            self.left_eye_position[0],
            self.left_eye_position[1],
            self.left_eye_position[2],
            self.right_eye_position[0],
            self.right_eye_position[1],
            self.right_eye_position[2],
            self.head_orientation[0],
            self.head_orientation[1],
            self.head_orientation[2],
            self.head_orientation[3],
            self.camera_projection[0],
            self.camera_projection[1],
            self.camera_projection[2],
            self.camera_projection[3],            
            self.right_hand_position[0],
            self.right_hand_position[1],
            self.right_hand_position[2],
            self.right_hand_orientation[0],
            self.right_hand_orientation[1],
            self.right_hand_orientation[2],
            self.right_hand_orientation[3]
        )
