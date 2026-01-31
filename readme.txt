# SPDX-License-Identifier: GPL-2.0-or-later
Train Controller

This program controls a CityHub, TechnicHub or MoveHub (other hubs are untested).
e.g. 6370369: HUB NO. 4
     https://brickset.com/parts/6370369/hub-no-4
     6142536: HUB, NO. 2
     https://brickset.com/parts/6142536/hub-no-2
     6283413: LPF2 HUB MOTOR 6X16X4 NO. 1
     https://brickset.com/parts/6283413/lpf2-hub-motor-6x16x4-no-1

note: MoveHub does not support devices from the Motor() class.

When the hub powers on (when not paired to a phone/tablet/computer) the
hub light will flash blue. Pressing the green button will start the
program.

On program startup, the hub light with follow default behaviour and fade
in and out in blue.

First, it scans the available ports for a motor and a color sensor.

Once it completes the port scan, it will wait for 5 seconds (5000ms) for a
remote.

Once the remote search times out or is found, the hub and remote lights
change to yellow, the "hold" color.

From here, the program loop is running.

- start/stop the motor by
  - Pressing the hub green button
  - Pressing the remote red button

When the motor is running, the hub and remote light will be:

- Green
      This means the motor is running. The train should be moving.
- Magenta
      As with Green, except we're at maximum speed
- Violet
      As with Green, except we're at minimum speed

When the color sensor detects Red (stop_color), it will stop the motor
and set the lights Red.

While the motor is stopped at Red, pressing the hub's green button or
the remote's red button will tell the motor to run again.

Or, once the color sensor no longer detects red, the motor will continue
automatically.

Supported peripherals:
- "Normal" Powered Up motors that work with the Motor class, eg.
      6342598: MOTOR, NO. 2
      https://brickset.com/parts/6342598/motor-no-2
      6347365: MOTOR, NO. 3
      https://brickset.com/parts/6347365/motor-no-3
- "Train motor" that works with the DCMotor class, eg.
      6214559: MOTOR, NO. 4
      https://brickset.com/parts/6214559/motor-no-4
- ColorDistanceSensor
      6240610: LPF2 SENSOR 2X4X2, NO. 1
      https://brickset.com/parts/6240610
