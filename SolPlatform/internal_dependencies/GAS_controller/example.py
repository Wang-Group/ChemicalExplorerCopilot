import yaml
from Gas_controller import GASAxis

with open(r'config.yaml') as f:
    config = yaml.safe_load(f)

axis = GASAxis(config, logger='<insert logger here>')

# Move the axis to home position
axis.return_home(axis_index='x')
# Move the axis to a specific position
axis.trap(axis_index='x', position=100, speed=50)
# Jog mode
axis.jog(axis_index='x', speed=300)
# set output signal
axis.output_trigger(op_index='<input the output index>', onoff=True)
# set analog output
axis.analog_trigger(dac_index='<input the dac index>', voltage="<input the voltage>")
# get analog input
axis.read_analog(adc_index='<input the adc index>')