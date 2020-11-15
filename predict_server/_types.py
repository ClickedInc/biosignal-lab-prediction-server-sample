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

        right_hand_primary_button_press = struct.unpack_from('>B', bytes, pos)
        pos += 1

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
            right_hand_angular_velocity,
            right_hand_primary_button_press > 0
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
                 right_hand_angular_velocity,
                 right_hand_primary_button_press):
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
        self.right_hand_primary_button_press = right_hand_primary_button_press

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
                 right_hand_orientation,
                 external_input_id,
                 external_input_actual_press,
                 external_input_predicted_press):
        self.timestamp = timestamp
        self.prediction_time = prediction_time
        self.left_eye_position = left_eye_position
        self.right_eye_position = right_eye_position
        self.head_orientation = head_orientation
        self.camera_projection = camera_projection
        self.right_hand_position = right_hand_position
        self.right_hand_orientation = right_hand_orientation
        self.external_input_id = external_input_id
        self.external_input_actual_press = external_input_actual_press
        self.external_input_predicted_press = external_input_predicted_press

    def pack(self):
        return struct.pack(
            '>q22fH2B',
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
            self.right_hand_orientation[3],
            self.external_input_id,
            1 if self.external_input_actual_press else 0,
            1 if self.external_input_predicted_press else 0
        )

class ExternalInputData:
    @classmethod
    def from_bytes(cls, bytes):
        (
            timestamp,
            device,
            button,
            actual_press,
            predicted_press
        ) = struct.unpack_from('>q4B', bytes, 0)

        return cls(
            timestamp,
            (device << 8) | button,
            actual_press > 0,
            predicted_press > 0
        )

    def __init__(self,
                 timestamp,
                 inputid,
                 actual_press,
                 predicted_press):
        self.timestamp = timestamp
        self.id = inputid
        self.actual_press = actual_press
        self.predicted_press = predicted_press

    def StateEquals(self, obj):
        if not isinstance(obj, ExternalInputData): 
            return False

        return self.actual_press == obj.actual_press and \
               self.predicted_press == obj.predicted_press

    def __str__(self):
        return (
            "timestamp {0}, device {1}, button {2}, "
            "pressed (actual {3}, predicted {4})"
        ).format(
            self.timestamp, self.id >> 8, self.id & 0xff,
            self.actual_press, self.predicted_press
        )
