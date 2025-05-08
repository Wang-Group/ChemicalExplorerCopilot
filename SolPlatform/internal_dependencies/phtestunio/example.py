from pHTestuino import pHTestMeter

meter = pHTestMeter(port="<insert port here>", logger="<insert logger here>")

# record a pH value (4.00)
meter.record_ref(4.00)
# record a pH value (7.00)
meter.record_ref(7.00)
# record a pH value (10.00)
meter.record_ref(10.00)
# calibrate the meter
meter.calibrate_meter()

# read a pH value
meter.read_pH()