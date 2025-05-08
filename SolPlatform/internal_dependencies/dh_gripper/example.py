from dh_gripper import Gripper
from serial import Serial

# Create a serial connection to the gripper
ser_config = {
    'port': '<insert port here>',
    'baudrate': 115200, 
    'timeout': 0.1}
ser = Serial(**ser_config)
gripper = Gripper(ser = ser, slave = '<insert slave>', _logger = '<insert logger>', name = '<insert Gripper model>')

# Initialize the gripper
gripper.initialization()
# Close the gripper
gripper.set_site(0)
# Open the gripper
gripper.set_site(1000)
# set the speed of the gripper
gripper.set_speed(100)
# set the force of the gripper
gripper.set_force(100)
# set the angle of the gripper
gripper.set_rotation_angle(180)
# set the rotation speed of the gripper
gripper.set_rotation_speed(100)
# set the rotation force of the gripper
gripper.set_rotation_force(100)

