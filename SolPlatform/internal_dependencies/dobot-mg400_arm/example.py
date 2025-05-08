from Dobot_Arms import MG400

ip = "<input your arm's ip>"

my_arm = MG400(ip = ip)
# Initialize the robot
my_arm.initialize_robot()
# Set the speed of the robot
my_arm.SetSpeedL(50)
# Move the robot to the position [0, 0, 0, 0]
my_arm.MoveL([0, 0, 0, 0])