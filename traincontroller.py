# SPDX-License-Identifier: GPL-2.0-or-later
#!/usr/bin/env pybricks-micropython

# ============================================================================
# Hub detection (must use version(); imports are hub-specific in Pybricks)
# ============================================================================
from pybricks import version
from pybricks.tools import wait
from pybricks.parameters import Button, Color, Direction, Port, Stop
from pybricks.pupdevices import ColorDistanceSensor, DCMotor, Motor, Remote

hub_type, *_ = version

if hub_type == "primehub":
    from pybricks.hubs import PrimeHub
    HubClass = PrimeHub
elif hub_type == "technichub":
    from pybricks.hubs import TechnicHub
    HubClass = TechnicHub
elif hub_type == "cityhub":
    from pybricks.hubs import CityHub
    HubClass = CityHub
elif hub_type == "essentialhub":
    from pybricks.hubs import EssentialHub
    HubClass = EssentialHub
elif hub_type == "movehub":
    from pybricks.hubs import MoveHub
    HubClass = MoveHub
else:
    raise RuntimeError("Unsupported hub type: {}".format(hub_type))

hub = HubClass()

# ============================================================================
# Configuration
# ============================================================================

SPEED_STEP_PERCENT = 10        # +/-10% per button press
MAX_PERCENT = 100
LOOP_MS = 20

RED_SAMPLES_TO_STOP = 3
NONRED_SAMPLES_TO_RESUME = 3

HUB_BUTTON_DEBOUNCE_MS = 250

# ============================================================================
# Control state (meaningful system state)
# ============================================================================

motor = None
sensor = None
remote = None

requested_percent = 50         # target speed once started
current_percent = None

stopped_by_button = True       # do not run until first button press
stopped_by_color = False

motor_max_speed = None         # cached Motor.limits()[0], None for DCMotor

# ============================================================================
# Housekeeping state (mechanics, counters, debounce)
# ============================================================================

motors = []
sensors = []

prev_hub_center_pressed = False
debounce_deadline_ms = 0
now_ms = 0

red_count = 0
nonred_count = 0

# ============================================================================
# Detection
# ============================================================================

def detect_peripherals():
    global motors, sensors, motor, sensor, motor_max_speed

    motors = []
    sensors = []

    # 1) Build a safe, hub-supported port list.
    #    - Hard rule: never touch A/B on MoveHub (can crash).
    #    - For everything else: probe with DCMotor and keep only ports that work.
    if hub_type == "movehub":
        candidate_ports = [Port.C, Port.D]
    else:
        candidate_ports = [Port.A, Port.B, Port.C, Port.D, Port.E, Port.F]

    ports = []
    for p in candidate_ports:
        try:
            probe = DCMotor(p, positive_direction=Direction.CLOCKWISE)

            try:
                probe.dc(0)  # minimal touch; should be harmless
            except Exception:
                pass
            ports.append(p)
        except Exception:
            pass

    # 2) Scan only the ports we just proved we can touch.
    for p in ports:
        # Avoid Motor() on MoveHub (known crash behavior)
        if hub_type != "movehub":
            try:
                motors.append(Motor(p, positive_direction=Direction.CLOCKWISE))
            except Exception:
                pass

        try:
            motors.append(DCMotor(p, positive_direction=Direction.CLOCKWISE))
        except Exception:
            pass

        try:
            sensors.append(ColorDistanceSensor(p))
        except Exception:
            pass

    # Policy: first device wins
    motor = motors[0] if motors else None
    sensor = sensors[0] if sensors else None

    # Cache motor max speed once (Motor only)
    motor_max_speed = None
    if motor is not None and hasattr(motor, "limits"):
        try:
            motor_max_speed, *_ = motor.limits()
        except Exception:
            motor_max_speed = None


def detect_remote():
    global remote
    try:
        remote = Remote()
    except Exception:
        remote = None

# ============================================================================
# Motor control
# ============================================================================

def is_dc_motor(m):
    return hasattr(m, "dc") and not hasattr(m, "run")


def stop_motor(stop_mode=Stop.BRAKE):
    global current_percent

    if motor is None:
        return

    try:
        motor.stop(stop_mode)
    except Exception:
        try:
            motor.stop()
        except Exception:
            try:
                motor.dc(0)
            except Exception:
                pass

    current_percent = 0


def apply_percent(percent):
    global current_percent

    if motor is None:
        return
    if stopped_by_button or stopped_by_color:
        return
    if current_percent == percent:
        return

    if is_dc_motor(motor):
        motor.dc(percent)
    else:
        max_speed = motor_max_speed if motor_max_speed is not None else 1000
        motor.run(int(max_speed * percent / 100))

    current_percent = percent

# ============================================================================
# UI / feedback
# ============================================================================

def all_lights(color):
    try:
        hub.light.on(color)
    except Exception:
        pass
    if remote:
        try:
            remote.light.on(color)
        except Exception:
            pass


def show_state():
    if stopped_by_button:
        all_lights(Color.ORANGE)
    elif stopped_by_color:
        all_lights(Color.RED)
    else:
        all_lights(Color.GREEN)

# ============================================================================
# State transitions
# ============================================================================

def toggle_run():
    global stopped_by_button

    if stopped_by_button:
        stopped_by_button = False
        apply_percent(requested_percent)
    else:
        stop_motor()
        stopped_by_button = True

    show_state()


def update_speed(delta_percent):
    global requested_percent

    requested_percent += delta_percent
    if requested_percent > MAX_PERCENT:
        requested_percent = MAX_PERCENT
    if requested_percent < -MAX_PERCENT:
        requested_percent = -MAX_PERCENT

    apply_percent(requested_percent)

# ============================================================================
# Input handling
# ============================================================================

def handle_remote():
    if not remote:
        return

    pressed = remote.buttons.pressed()

    if pressed == (Button.CENTER,):
        toggle_run()
        wait(250)

    if Button.LEFT_PLUS in pressed:
        update_speed(+SPEED_STEP_PERCENT)
        wait(200)

    if Button.LEFT_MINUS in pressed:
        update_speed(-SPEED_STEP_PERCENT)
        wait(200)


def handle_hub_button():
    global prev_hub_center_pressed, debounce_deadline_ms

    pressed = Button.CENTER in hub.buttons.pressed()

    if now_ms >= debounce_deadline_ms:
        if pressed and not prev_hub_center_pressed:
            toggle_run()
            debounce_deadline_ms = now_ms + HUB_BUTTON_DEBOUNCE_MS

    prev_hub_center_pressed = pressed


def handle_sensor():
    global stopped_by_color, red_count, nonred_count

    if not sensor:
        return

    c = sensor.color()

    if c == Color.RED:
        red_count += 1
        nonred_count = 0
    else:
        nonred_count += 1
        red_count = 0

    if not stopped_by_color and red_count >= RED_SAMPLES_TO_STOP:
        stopped_by_color = True
        stop_motor()
        show_state()

    if stopped_by_color and nonred_count >= NONRED_SAMPLES_TO_RESUME:
        stopped_by_color = False
        apply_percent(requested_percent)
        show_state()

# ============================================================================
# Main
# ============================================================================

detect_peripherals()
detect_remote()
show_state()

while True:
    now_ms += LOOP_MS

    handle_sensor()
    handle_remote()
    handle_hub_button()

    wait(LOOP_MS)

