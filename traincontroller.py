# SPDX-License-Identifier: GPL-2.0-or-later
from pybricks.pupdevices import DCMotor, Motor
from pybricks.pupdevices import ColorDistanceSensor
from pybricks.pupdevices import Remote
from pybricks.parameters import Port, Color, Button, Stop
from pybricks.tools      import wait
from pybricks            import version

# Global Variables
hub   = None
motor = None
sensor= None

motor_port  = None
sensor_port = None

hub_type    = None
motor_type  = None # Supported types: DCMotor, Motor
sensor_type = None # Supported types: ColorDistanceSensor

ports = [Port.A, Port.B]

stop_color        = Color.RED
go_color          = Color.GREEN
hold_color        = Color.YELLOW
requested_speed   = 50
current_speed     = 0
stopped_by_button = True
stopped_by_color  = False
remote_timeout    = 5000
motor_multiplier  = 1
motor_max_speed   = 100
debounce_delay    = 200

def set_motor_speed(speed):
	global motor
	global current_speed
	global motor_multiplier

	if stopped_by_button or stopped_by_color:
		return

	# Set the internal speed before checking for a motor
	# This is so we can test the sensor and remote code without a motor
	current_speed=speed
	print("Setting current_speed = ", current_speed, "%")

	if motor == None:
		return

	if motor_type == "Motor":
		motor.run(speed*motor_multiplier)
	elif motor_type == "DCMotor":
		motor.dc(speed)
	else:
		print("Motor type", motor_type, "not supported")
		return

	all_lights(go_color)

	if (speed * motor_multiplier) == motor_max_speed:
		all_lights(Color.MAGENTA)
	elif (speed * motor_multiplier) == (motor_max_speed * -1):
		all_lights(Color.VIOLET)
	else:
		all_lights(go_color)

	# Add a delay to prevent the motor from being changed too quickly
	wait(debounce_delay)

def motor_is_stopped():
	if stopped_by_button == True or stopped_by_color == True:
		return True
	else:
		return False

def motor_is_running():
	#if current_speed != 0:
	if motor_is_stopped() == False:
		return True
	else:
		return False

def stop_button(source):
	global stopped_by_button
	global stopped_by_color

	if motor_is_stopped():
		print("We are not running and someone pressed the", source, "button, so I'll continue")
		stopped_by_button=False
		stopped_by_color=False
		set_motor_speed(requested_speed)
	else:
		print("We are running and someone pressed the", source, "button, so I'll stop")
		set_motor_speed(0)
		stopped_by_button=True
		all_lights(hold_color)

def all_lights(color):
	global remote

	if remote != None:
		remote.light.on(color)
	hub.light.on(color)

def handle_sensor():
	global sensor
	global stopped_by_color

	if sensor == None:
		return

	if sensor_type == "ColorDistanceSensor":
		color=sensor.color()
	else:
		print("Sensor type", sensor_type, "not supported")
		return

	if color == stop_color:
		if motor_is_running():
			print("We are running and I see", stop_color, "so I'm stopping")
			set_motor_speed(0)
			stopped_by_color=True
			all_lights(stop_color)
	else:
		if motor_is_stopped() and stopped_by_color == True:
			print("We are stopped and I no longer see", stop_color, "so I'll continue")
			stopped_by_color=False
			set_motor_speed(requested_speed)
			all_lights(go_color)

def handle_buttons():
	global remote
	global requested_speed
	global stopped_by_button

	# Check if the hub's center button is pressed
	if Button.CENTER in hub.buttons.pressed():
		stop_button("hub")

	if remote != None:
		pressed = remote.buttons.pressed()
		if Button.LEFT in pressed:
			print("LEFT stop pressed")
			stop_button("remote")
			wait(debounce_delay)
		elif Button.LEFT_PLUS in pressed:
			print("LEFT PLUS pressed")
			if motor_is_stopped() == True:
				wait(debounce_delay)
				return
			requested_speed += 10
			if requested_speed > 100:
				requested_speed = 100
			set_motor_speed(requested_speed)
		elif Button.LEFT_MINUS in pressed:
			print("LEFT MINUS pressed")
			if motor_is_stopped() == True:
				wait(debounce_delay)
				return
			requested_speed -= 10
			if requested_speed < -100:
				requested_speed = -100
			set_motor_speed(requested_speed)
		#else:
			#print("No useful buttons pressed")


def detect_peripherals():
	global hub_type
	global motor
	global motor_type
	global motor_port
	global motor_multiplier
	global sensor
	global sensor_port
	global sensor_type
	global motor_max_speed

	# Start with the basic set of ports available on all hubs
	if hub_type == "movehub":
		# MoveHub doesn't like you scanning Port.A or B
		ports = [Port.C, Port.D]
	else:
		ports = [Port.A, Port.B]

		# Add more ports if supported by the hub
		try:
			ports.append(Port.C)
			ports.append(Port.D)
			ports.append(Port.E)
			ports.append(Port.F)
		except AttributeError:
			pass

	print("Available ports:", ports)

	for port in ports:
		# Maybe we have a regular Motor?
		if hub_type != "movehub":
			# MoveHub crashes when you connect a Motor
			try:
				motor = Motor(port)
				motor_type="Motor"
				motor_port=port
				angle = motor.angle
				motor_max_speed, _, _ = motor.control.limits()
				motor_multiplier=motor_max_speed/100
				print(port, ":", motor_type,
					"max_speed=", motor_max_speed,
					"multiplier=", motor_multiplier)
				continue
			except OSError:
				pass

		# Maybe we have a DCMotor?
		try:
			motor = DCMotor(port)
			motor_type="DCMotor"
			motor_port=port
			motor_max_speed=100
			motor_multiplier=1
			print(port, ":", motor_type,
				"max_speed=", motor_max_speed,
				"multiplier=", motor_multiplier)
			continue
		except OSError:
			pass

		# Sensor Init
		try:
			sensor = ColorDistanceSensor(port)
			sensor_port=port
			sensor_type="ColorDistanceSensor"
			print(port, ":", sensor_type)
			continue
		except OSError:
			pass

		print(port, ": Nothing found")

def detect_remote():
	global remote

	print("Waiting", remote_timeout, "ms for remote...")
	remote = None
	try:
		remote=Remote(timeout=remote_timeout) # TODO: How to handle connecting the remote and timeouts??
		print("Remote name is", remote.name)
	except OSError:
		print("Could not find the remote. Never mind, continue without it")

def detect_hub():
	global hub
	global hub_type

	# Get the hardware type
	print("Hub type", version)
	hub_type, _, _ = version

	if hub_type == "cityhub":
		from pybricks.hubs       import CityHub
		hub = CityHub()
	elif hub_type == "technichub":
		from pybricks.hubs       import TechnicHub
		hub = TechnicHub()
	elif hub_type == "movehub":
		from pybricks.hubs       import MoveHub			# not tested
		hub = MoveHub()
	elif hub_type == "inventorhub":
		from pybricks.hubs       import InventorHub		# not tested
		hub = InventorHub()
	elif hub_type == "primehub":
		from pybricks.hubs       import PrimeHub
		hub = PrimeHub()
	elif hub_type == "essentialhub":
		from pybricks.hubs       import EssentialHub	# not tested
		hub = EssentialHub()
	else:
		print("No hub detected")


# The program starts here
print("Train Controller program")

detect_hub()
detect_peripherals()
detect_remote()

# The hub's center button usually stops the program
# Override that so we can use it ourselves
print("Claiming the hub stop button as our own")
hub.system.set_stop_button(None)

all_lights(hold_color)

print("Entering the main loop")
while True:
	handle_sensor()
	handle_buttons()
