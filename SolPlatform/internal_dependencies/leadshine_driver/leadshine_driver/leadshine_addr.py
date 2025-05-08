READ_ADDR = {
    "running_status": 0x1003, # 
    "saving_stats": 0x1901, # succeed: 0x5555, failed: 0xAAAA
    "current_alarm": 0x2203, #
    "motion_status": 0x6002,  # move over: 0x0000
    "peak_current": 0x0191
}
WRITE_ADDR = {
    "Pr0.00": 0x0001, # set the unit (pulse per circle)
    "Pr0.02": 0x0005, # set the control mode
    "Pr0.03": 0x0007, # set the direction of motor e.g. 0: positive, 1: negative
    "Pr0.04": 0x0009, # set the inductance, unit: uH
    "Pr0.07": 0x00F,  # forced to enable
    "Pr4.02": 0x0145, # Pr4.02~Pr4.08 means DI1~DI7
    "Pr4.03": 0x0147, 
    "Pr4.04": 0x0149, 
    "Pr4.05": 0x014B, 
    "Pr4.06": 0x014D, 
    "Pr4.07": 0x014F,
    "Pr4.08": 0x0151, 
    "Pr4.11": 0x0157, # Pr4.11~Pr4.13 means DO1~DO3
    "Pr4.12": 0x0159, 
    "Pr4.13": 0x015B, 
    "Pr5.00": 0x0191, # set the peak current
    "Pr5.33": 0x01D3, # set the current when the motor is not moving
    "control_board": 0x1801,  # save_EEPROM: 0x2244
    "Pr8.00": 0x6000, 
    "Pr8.02": 0x6002, # trigger register; datum: 0x020, set_origin: 0x021, forced_stop: 0x040
    "Pr8.10": 0x600A, # datum_mode: default: 0x0005
    "Pr8.15": 0x600F, # datum_high_speed
    "Pr8.16": 0x6010, # datum_low_speed
    "Pr8.17": 0x6011, # datum_accelerate
    "Pr8.18": 0x6012, # datum_deccelerate
    "Pr9.00": 0x6200, # set the motion mode 
    "Pr9.01": 0x6201, # high_position
    "Pr9.02": 0x6202, # low_position
    "Pr9.03": 0x6203, # set_speed
    "Pr9.04": 0x6204, # accelerate
    "Pr9.05": 0x6205, # deccelerate
    "Pr9.07": 0x6207, # start_moving
    }