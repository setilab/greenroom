#!/usr/local/bin/python

import argparse
import socket
import threading
import socketserver
import time
import datetime
import os
from subprocess import call
import sys
import logging
import logging.handlers
import requests
import json

# App version
_VERSION_ = "1.5.3"

# HW Info
_TYPE_ = "controller"
_CAP_ = "temperature"
_VENDOR_ = "Robogaia"
_MODEL_ = "pi_tcp"

# Build num
_BUILD_ = os.getenv("GR_CNTRLR_BUILD", "X.xxx")

# API to register with
_API_ = os.getenv("GR_API_URL", "http://localhost:8080/controllers/register")

# Run as emulator or not
_EMULATOR_ = os.getenv("GR_EMULATOR_MODE", "False")

if _EMULATOR_ == "True":
    bus = "/mnt/bus.pseudo"
else:
    import smbus
    bus = smbus.SMBus(1)

# TCP server values
my_reg_name = socket.gethostname()
my_tcp_host = socket.gethostbyname(my_reg_name)
my_tcp_port = 12000

# Log/Config files
my_config_file = "config.json"
my_log_file = "grcntrlrd.log"

if _EMULATOR_ == "True":
    gpio22_file = "gpio22.psuedo"
    gpio27_file = "gpio27.psuedo"
else:
    gpio22_file = "/sys/class/gpio/gpio22/value"
    gpio27_file = "/sys/class/gpio/gpio27/value"

    #I2C addres
    address = 0x4d

# flow logic
shutdown = 0

# temps
heat_offset = t_heat_offset = 5
cool_offset = t_cool_offset = 2
coolTo = t_coolTo = 72
heatTo = t_heatTo = 68

# timers
tc_start_delay = t_tc_start_delay = 10
cool_start_delay = t_cool_start_delay = 15
state_change_delay = t_state_change_delay = 60

# commands
_GET_ = 3
_SET_ = 3
_APPLY_ = 5
_SHUTDOWN_ = 8
_REGISTER_ = 8
_SAVE_ = 4

# misc
temp_scale = t_temp_scale = "F"

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        global coolTo, t_coolTo
        global heatTo, t_heatTo
        global cool_offset, t_cool_offset
        global heat_offset, t_heat_offset
        global tc_start_delay, t_tc_start_delay
        global cool_start_delay, t_cool_start_delay
        global state_change_delay, t_state_change_delay
        global temp_scale, t_temp_scale
        global shutdown

        data = self.request.recv(1024).decode()
        txt = data.strip()
        cmd = txt.upper()

        lmsg = "Got TCP connection from {}".format(self.client_address[0])
        logging.info(lmsg)

        lmsg = "Recv'd command: {}".format(cmd)
        logging.debug(lmsg)

        if cmd[:_SET_] == "SET":
            if cmd[4:11] == "COOL TO" :
                t_coolTo = int(cmd[12:])
                response = "Setting Cool to {}.".format(t_coolTo)
            elif cmd[4:11] == "HEAT TO" :
                t_heatTo = int(cmd[12:])
                response = "Setting Heat to {}.".format(t_heatTo)
            elif cmd[4:15] == "COOL OFFSET" :
                t_cool_offset = int(cmd[16:])
                response = "Setting Cool Offset to {}.".format(t_cool_offset)
            elif cmd[4:15] == "HEAT OFFSET" :
                t_heat_offset = int(cmd[16:])
                response = "Setting Heat Offset to {}.".format(t_heat_offset)
            elif cmd[4:18] == "TC START DELAY" :
                t_tc_start_delay = int(cmd[19:])
                response = "Setting TC Start Delay to {}.".format(t_tc_start_delay)
            elif cmd[4:20] == "COOL START DELAY" :
                t_cool_start_delay = int(cmd[21:])
                response = "Setting Cool Start Delay to {}.".format(t_cool_start_delay)
            elif cmd[4:22] == "STATE CHANGE DELAY" :
                t_state_change_delay = int(cmd[23:])
                response = "Setting State Change Delay to {}.".format(t_state_change_delay)
            elif cmd[4:14] == "TEMP SCALE" :
                t_temp_scale = cmd[15:]
                response = "Setting Temperature Scale to {}.".format(t_temp_scale)
            else:
                response = "Unknown command."

                self.request.sendall(bytes(response, 'utf-8'))
                logging.info(response)

        elif cmd[:_GET_] == "GET":

            if cmd[4:12] == "SETTINGS" :
                schema = "heatto,coolto,cool_offset,heat_offset,tc_start_delay,cool_start_delay,state_change_delay,temp_scale"
                values = "{},{},{},{},{},{},{},{}".format(heatTo,coolTo,cool_offset,heat_offset,tc_start_delay,cool_start_delay,state_change_delay,temp_scale)

                self.request.sendall(bytes(schema + "\n" + values, 'utf-8'))

            elif cmd[4:10] == "STATUS" :
                cold = temp_relay_status("cold")
                hot = temp_relay_status("hot")

                schema = "fan,heater"
                values = "{},{}".format(cold, hot)

                self.request.sendall(bytes(schema + "\n" + values, 'utf-8'))

            elif cmd[4:11] == "VERSION" :
                self.request.sendall(bytes("version\n" + _VERSION_, 'utf-8'))

            logging.debug("Replied to GET command from client.")

        elif cmd[:_APPLY_] == "APPLY":
            cool_offset = t_cool_offset
            heat_offset = t_heat_offset
            tc_start_delay = t_tc_start_delay
            cool_start_delay = t_cool_start_delay
            state_change_delay = t_state_change_delay
            response = "Settings applied."

            if t_coolTo >= t_heatTo :
                coolTo = t_coolTo
                heatTo = t_heatTo
                logging.info(response)
            else:
                response = "Cool to temperature must be greater than heat to temperature."
                logging.warn(response)

            if not temp_scale == t_temp_scale:
                set_scale(t_temp_scale)

            self.request.sendall(bytes(response, 'utf-8'))

        elif cmd[:_SAVE_] == "SAVE":
            response = "Saving configuration to file..."
            self.request.sendall(bytes(response, 'utf-8'))
            logging.info(response)

            rawdata1 = "heatto,coolto,cool_offset,heat_offset,tc_start_delay,cool_start_delay,state_change_delay,temp_scale"

            rawdata2 = "{},{},{},{},{},{},{},{}".format(heatTo,coolTo,cool_offset,heat_offset,tc_start_delay,cool_start_delay,state_change_delay,temp_scale)
            settings = {'settings': [dict(zip(tuple(rawdata1.split(",")),rawdata2.split(",")))]}

            rawdata1 = "api_url,my_reg_name,my_tcp_host,my_tcp_port"
            rawdata2 = "{},{},{},{}".format(api_url,my_reg_name,my_tcp_host,my_tcp_port)
            tcp_api = {'tcp/api': [dict(zip(tuple(rawdata1.split(",")),rawdata2.split(",")))]}

            rawdata1 = "my_log_file,gpio22_file,gpio27_file"
            rawdata2 = "{},{},{}".format(my_log_file,gpio22_file,gpio27_file)
            files = {'files': [dict(zip(tuple(rawdata1.split(",")),rawdata2.split(",")))]}

            formatd = {'config': [tcp_api,files,settings]}
            jdata = json.dumps(formatd, indent=4)

            try:
                f = open(my_config_file, "w")
                f.write(jdata)
                f.write("\n")
                f.close()
                logging.info("Config data saved.")
            except:
                logging.error("Unable to save config file.")

        elif cmd[:_SHUTDOWN_] == "SHUTDOWN":
            shutdown = 1
            response = "Shutting down server..."
            self.request.sendall(bytes(response, 'utf-8'))
            logging.info(response)

        elif cmd[:_REGISTER_] == "REGISTER":
            response = "Registering to API service..."
            self.request.sendall(bytes(response, 'utf-8'))
            register_api()
            logging.info(response)
        else:
            tempVal = str(get_temp())

            schema = "value,scale"
            values = "{},{}".format(tempVal,temp_scale)

            self.request.sendall(bytes(schema + "\n" + values, 'utf-8'))

            logging.debug("Supplied current temp: {}".format(values))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


filterArray = [0 , 0, 0 , 0 , 0, 0, 0, 0] #holds the filter values 

def filter(input_value):
    filterArray.append(input_value);
    filterArray.pop(0);
    result = (filterArray[0] + filterArray[1]+ filterArray[2]+ filterArray[3]+ filterArray[4]+ filterArray[5]+ filterArray[6]+ filterArray[7])/8 ;
    stringFilterArray = [str(a) for a in filterArray];
    return result;


def get_fahrenheit_val(): 
    if _EMULATOR_ == "True":
        with open(bus,'r') as f:
            val = int(f.read())
    else:
        data = bus.read_i2c_block_data(address, 1,2)
        val = (data[0] << 8) + data[1]

    return val/5.00*9.00/5.00+32.00


def get_celsius_val(): 
    if _EMULATOR_ == "True":
        with open(bus,'r') as f:
            val = int(f.read())
    else:
        data = bus.read_i2c_block_data(address, 1,2)
        val = (data[0] << 8) + data[1]

    return val/5.00


def toggle_temp_relay(relay, state):
    #port 22 is the hot relay
    #port 27 is the cold relay 

    if relay == "cold" :
        fname = gpio27_file
    elif relay == "hot" :
        fname = gpio22_file
    else:
        return

    if state == "on" :
        val = 1
    else:
        val = 0

    str = "{}\n".format(val)
    with open(fname,'w') as f:
        f.write(str)

    lmsg = "Toggled {} relay to {}".format(relay, state)
    logging.debug(lmsg)


def temp_relay_status(relay):
    #port 22 is the hot relay
    #port 27 is the cold relay 

    if relay == "cold" :
        fname = gpio27_file
        label = "Fan"
    elif relay == "hot" :
        fname = gpio22_file
        label = "Heater"
    else:
        return

    with open(fname,'r') as f:
        state = int(f.read())

    if state == 1 :
        status = "on"
        lmsg = "{}: On".format(label) 
    else:
        status = "off"
        lmsg = "{}: Off".format(label) 

    logging.info(lmsg)
    return status


def set_cold():
    toggle_temp_relay("cold", "on")
    toggle_temp_relay("hot", "off")


def set_hot():
    toggle_temp_relay("cold", "off")
    toggle_temp_relay("hot", "on")


def set_close():
    toggle_temp_relay("cold", "off")
    toggle_temp_relay("hot", "off")


def get_status():
    cold = temp_relay_status("cold")
    hot = temp_relay_status("hot")


def get_temp():
    #get the temperature from sensor
    if temp_scale == "F":
        temperature_raw =get_fahrenheit_val()
    else:
        temperature = get_celsius_val()

    temperature = filter(temperature_raw);

    return int(temperature + 0.5)


def set_scale(new_scale):
    global temp_scale
    global coolTo, t_coolTo
    global heatTo, t_heatTo

    temp_scale = new_scale
    if new_scale == "F":
        coolTo = t_coolTo = convert_c(coolTo)
        heatTo = t_heatTo = convert_c(heatTo)
    else:
        coolTo = t_coolTo = convert_f(coolTo)
        heatTo = t_heatTo = convert_f(heatTo)


def convert_f(f):
    c = (f - 32) * 5.0/9.0
    return int(c)


def convert_c(c):
    f = (9.0/5.0 * c) + 32
    return int(f + 0.5)


def init_phat():
    f1 = f2 = 0
    gpio22 = os.path.exists(gpio22_file)
    if gpio22:
        f1 = 1
    gpio27 = os.path.exists(gpio27_file)
    if gpio27:
        f2 = 1

    if f1 == 1 and f2 == 1 :
        return
    else:
        if _EMULATOR_ == "False":
            call(["sudo", "temperature_controller_init"])	
        lmsg = "Initializing hardware..."
        logging.info(lmsg)


def init_logging():
    logger = logging.getLogger()
    fh = logging.handlers.RotatingFileHandler(my_log_file, maxBytes=10240, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    logger.info('*** GREENROOM CONTROL SYSTEM (C) ***')


def register_api():
    logging.info("Registering to API service...")

    data = "name={}&host={}&port={}&type={}&capability={}&vendor={}&model={}".format(my_reg_name,my_tcp_host,my_tcp_port,_TYPE_,_CAP_,_VENDOR_,_MODEL_)

    try:
        response = requests.post(api_url, data=data)
        if(response.ok):
            logging.info("Successfully registered to API service.")
        else:
            logging.warn("API registration failed with HTTP Error {}".format(response.status_code))
    except:
        logging.warn("API registration failed with an unspecified HTTP Error.")

    finally:
        return


def init_config():
    global coolTo, t_coolTo
    global heatTo, t_heatTo
    global cool_offset, t_cool_offset
    global heat_offset, t_heat_offset
    global tc_start_delay, t_tc_start_delay
    global cool_start_delay, t_cool_start_delay
    global state_change_delay, t_state_change_delay
    global temp_scale, t_temp_scale
    global api_url
    global my_reg_name
    global my_tcp_host
    global my_tcp_port
    global my_log_file
    global gpio22_file
    global gpio27_file

    try:
        f = open(my_config_file, "r")
        jdata = ""
        for x in f:
            jdata += x
        f.close()
        configd = json.loads(jdata)

        config = configd["config"]
        tcp_api = config[0]["tcp/api"]
        files = config[1]["files"]
        settings = config[2]["settings"]

        #api_url = tcp_api[0]["api_url"]
        if _EMULATOR_ == "False":
            my_reg_name = tcp_api[0]["my_reg_name"]
            my_tcp_host = tcp_api[0]["my_tcp_host"]
        my_tcp_port = int(tcp_api[0]["my_tcp_port"])

        my_log_file = files[0]["my_log_file"]
        gpio22_file = files[0]["gpio22_file"]
        gpio27_file = files[0]["gpio27_file"]

        coolTo = t_coolTo = int(settings[0]["coolto"])
        heatTo = t_heatTo = int(settings[0]["heatto"])
        cool_offset = t_cool_offset = int(settings[0]["cool_offset"])
        heat_offset = t_heat_offset = int(settings[0]["heat_offset"])
        tc_start_delay = t_tc_start_delay = int(settings[0]["tc_start_delay"])
        cool_start_delay = t_cool_start_delay = int(settings[0]["cool_start_delay"])
        state_change_delay = t_state_change_delay = int(settings[0]["state_change_delay"])
        temp_scale = t_temp_scale = settings[0]["temp_scale"]
    except:
        print("Unable to open config file. Using default values...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', nargs='?',
                        help="Path to a JSON formatted config file.")
    args = parser.parse_args()
    if args.config_file:
        my_config_file=args.config_file

    init_config()
    init_logging()
    init_phat()
    set_close()

    if _EMULATOR_ == "True":
        lmsg = "Emulator mode enabled."
        logging.info(lmsg)

    HOST, PORT = "0.0.0.0", my_tcp_port

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    lmsg = "TCP Server started."
    logging.info(lmsg)

    register_api()

    isHeating = False
    isCooling = False
    delay = 1

    for sec in range(1,tc_start_delay + 1):
        t = get_temp()
        lmsg = "Waiting for thermocoupler...{}".format(sec)
        logging.info(lmsg)
        time.sleep(1.0)

    #main loop
    while not shutdown == 1 :

        temperature = get_temp()
        if isCooling == False :
            set_point = coolTo + cool_offset
        else:
            set_point = coolTo

        #verify if we need to cool or to heat
        if temperature > set_point :
            delay = 1
            if isCooling == False :
                lmsg = "Cooling to {}{} in {}s".format(coolTo, temp_scale, cool_start_delay)
                logging.info(lmsg)
                while delay < cool_start_delay:
                    if shutdown == 1:
                        break
                    delay += 1
                    time.sleep(1.0)
            set_cold()
            isCooling = True
            isHeating = False
            delay = 1
            lmsg = "Cooling to {}{} for {}s".format(coolTo, temp_scale, state_change_delay)
            logging.info(lmsg)
            while delay < state_change_delay:
                if shutdown == 1:
                    break
            delay += 1
            t = get_temp()
            time.sleep(1.0)

        elif temperature  <= (heatTo - heat_offset) :
            delay = 1
            lmsg = "Heat dropped below {}{}".format(heatTo - heat_offset, temp_scale)
            logging.info(lmsg)
            set_hot()
            isHeating = True
            isCooling = False
            lmsg = "Heating to {}{} in {}s".format(heatTo - heat_offset, temp_scale, state_change_delay)
            logging.info(lmsg)
            while delay < state_change_delay:
                if shutdown == 1:
                    break
            delay += 1
            t = get_temp()
            time.sleep(1.0)

        elif isHeating == True and temperature <= heatTo :
            delay = 1
            lmsg = "Heating to {}{} for {}s".format(heatTo, temp_scale, state_change_delay)
            logging.info(lmsg)
            set_hot()
            isCooling = False
            while delay < state_change_delay:
                if shutdown == 1:
                    break
            delay += 1
            t = get_temp()
            time.sleep(1.0)
        else:
            delay = 1
            lmsg = "Holding at {}{} for {}s".format(temperature, temp_scale, state_change_delay)
            logging.info(lmsg)
            set_close()
            isCooling = False
            isHeating = False
            while delay < state_change_delay:
                if shutdown == 1:
                    break
            delay += 1
            t = get_temp()
            time.sleep(1.0)

        time.sleep(1.0)
    #
    # shutdown 'signal' recv'd from client
    server.shutdown()
    server.server_close()
#
# EOF
#
