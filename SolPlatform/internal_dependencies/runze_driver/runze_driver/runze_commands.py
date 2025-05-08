COMMANDS = {
    'Common_commands': {
        'STX': 0xCC,
        'ETX': 0xDD,
        'valve_switch': 0x44,
        'valve_switch_dir': 0xA4,
        'between_valve_switch_dir': 0xB4,
        'forced_stop': 0x49,
        'motor_sts': 0x4A, 
        'get_baudrate': 0x02
        },
    'SwitchValve_commands': {
        'reset': 0x45,
        'reset_origin': 0x4F,
        'current_channel': 0x3E
        },
    'SyringePump_commands': {
        'valve_reset': 0x4C,
        'pump_reset': 0x45,
        'forced_reset': 0x4F,
        'forced_stop': 0x49,
        'inject_liquid': 0x42,
        'absorb_liquid': 0x43,
        'set_dynamic_speed': 0x4B,
        'absolute_move': 0x4E,
        'get_position': 0x66,
        'synchronize_position': 0x67,
        'current_channel': 0xAE,
        'get_valve_sts': 0x4D,
        'get_speed': 0x27, 
        'valve_open': 0x60,  
        'valve_close': 0x61
        },
    'Injector_commands': {
        'absolute_move': 0x4E,
        'reset': 0x45,
        'forced_reset': 0x4F,
        'set_dynamic_speed': 0x4B,
        'get_position': 0x66
        },
    'PeristalticPump_commands': {
        'clockwise_by_step': 0x40,
        'counterclockwise_by_step': 0x41,
        'clockwise_continus': 0x47,
        'counterclockwise_continus': 0x48, 
        'set_dynamic_speed': 0x4B
        }
    }