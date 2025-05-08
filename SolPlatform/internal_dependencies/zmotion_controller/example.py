import yaml
from zmotion import AxisMotion

with open('config.yaml') as f:
    config = yaml.safe_load(f)

axis = AxisMotion(motion_prm=config, logger="<insert logger here>")

# move to home position
axis.datum(axis_index="x")
# move to position 100
axis._absolute_move(axis_index="x", position=100)
# all axes move to home position
axis.datum_xyz()
# all axes move to position 100
axis._move_xyz([100, 100, 100, 100])