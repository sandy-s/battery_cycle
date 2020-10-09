# battery cycle testing utility
# uses Agilent 661xC series supply
# to charge and discharge

addr = 5

# Li-ion 1 cell
#charging_voltage = 4.2
#discharging_voltage_threshold = 2.8

# Li-ion 2 cell
#charging_voltage = 8.4
#discharging_voltage_threshold = 6.0

# Li-ion 4 cell
#charging_voltage = 16.8
#discharging_voltage_threshold = 12

# Li-ion 7 cell
charging_voltage = 29.4
discharging_voltage_threshold = 21

charging_current = 1.0
charging_current_threshold = 0.05
discharging_current = -0.8
discharge_voltage_step = 0.003

measure_interval_sec = 1
reporting_period_sec = 10

import gpib
import time
from datetime import datetime
import sys
import argparse

def query(handle, command):
  gpib.write(handle, command)
  time.sleep(0.03)
  response = gpib.read(handle, 200)
  return response.decode('ascii').rstrip()

def send(handle, command):
  gpib.write(handle, command)
  #time.sleep(0.02)

def charge():
  print('Charging battery: target voltage %.3f, current limit %.3f, stop current %.3f' % (charging_voltage, charging_current, charging_current_threshold))
  v = float(query(ps, 'measure:voltage?'))
  print('Starting voltage: %.3f' % (v))
  send(ps, 'voltage %.3f' % (charging_voltage))
  send(ps, 'current %.3f' % (charging_current))
  send(ps, 'output on')
  print('Charging started')
  start_charging = datetime.now()
  c = float(query(ps, 'measure:current?'))
  mah = 0
  wh = 0
  start_reporting = datetime.now()
  stop_iteration = datetime.now()
  while c > charging_current_threshold:
    start_iteration = stop_iteration
    time.sleep(measure_interval_sec)
    c = float(query(ps, 'measure:current?'))
    v = float(query(ps, 'measure:voltage?'))
    stop_iteration = datetime.now()
    iteration_duration = stop_iteration - start_iteration
    mah += c * iteration_duration.total_seconds() / 3.6
    wh += c * v * iteration_duration.total_seconds() / 3600
    if (stop_iteration - start_reporting).total_seconds() > reporting_period_sec:
      print('%.3f V %.3f A %d mAh %.3f Wh' % (v, c, mah, wh))
      start_reporting = stop_iteration
  send(ps, 'output off')
  stop_charging = datetime.now()
  duration = stop_charging - start_charging
  print('Charging done: %s' % (duration))

def discharge(ps):
  print('Discharging battery: current %.3f, stop voltage %.3f' % (discharging_current, discharging_voltage_threshold))
  start = datetime.now()
  mah = 0
  wh = 0
  v = float(query(ps, 'measure:voltage?'))
  print('Starting voltage: %.3f' % (v))
  send(ps, 'voltage %.3f' % (v))
  send(ps, 'output on')
  c = float(query(ps, 'measure:current?'))
  start_reporting = datetime.now()
  stop_iteration = datetime.now()
  while v > discharging_voltage_threshold:
    start_iteration = stop_iteration
    if c > discharging_current: # > because of negative current
      v -= discharge_voltage_step
      send(ps, 'voltage %.3f' % (v))
    time.sleep(measure_interval_sec)
    c = float(query(ps, 'measure:current?'))
    stop_iteration = datetime.now()
    iteration_duration = stop_iteration - start_iteration
    mah += c * iteration_duration.total_seconds() / -3.6
    wh += c * v * iteration_duration.total_seconds() / -3600
    if (stop_iteration - start_reporting).total_seconds() > reporting_period_sec:
      print('%.3f V %.3f A %d mAh %.3f Wh' % (v, c, mah, wh))
      start_reporting = stop_iteration
  send(ps, 'output off')
  stop = datetime.now()
  duration = stop - start
  print('Discharging done: %s' % (duration))
  print('Battery capacity: %d mAh %.3f Wh' % (mah, wh))

# init power supply
ps = gpib.dev(0, addr);
ps_id = query(ps, '*idn?')
print('Using power supply: ', ps_id)

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--charge', nargs = '?', const = True, default = False)
parser.add_argument('-d', '--discharge', nargs = '?', const = True, default = False)

args = parser.parse_args()

if args.charge:
  charge()

if args.discharge:
  discharge(ps)
