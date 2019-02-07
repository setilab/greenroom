#!/usr/bin/python

import socket
import sys
import web.py
import json

urls = ('/controllers','Controllers',
        '/controllers/ids','ControllerIDs',
        '/controllers/register','Register',
        '/controllers/([0-9]{1,3})','Controller',
        '/controllers/([0-9]{1,3})/save','Save',
        '/controllers/([0-9]{1,3})/settings','Settings',
        '/controllers/([0-9]{1,3})/settings/([a-z_]{2,})','SettingName',
        '/controllers/([0-9]{1,3})/shutdown','Shutdown',
        '/controllers/([0-9]{1,3})/status','Status',
        '/controllers/([0-9]{1,3})/temp','Temp',
        '/controllers/([0-9]{1,3})/unregister','Unregister'
)

# Format example { "name":"controller1", "host":"localhost", "port":"12000" },
controllers = []

app = web.application(urls, globals())

def client(data, host, port):
    payload = ""
    HOST, PORT = host, int(port)

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(data)

        # Receive data from the server and shut down
        while True:
            received = sock.recv(1024)
            if len(received) > 0:
                payload += "{}\n".format(received)
            else:
                break
    finally:
        sock.close()
        return payload


class ControllerIDs():
    def GET(self):
        string = ""
        i = 0
        for cntrlr in controllers:
            if i < 1:
                string += "{}".format(i)
            else:
                string += ", {}".format(i)
            i += 1

        result = {'controllers': [string]}
        return result + "\n"


class Controllers():
    def GET(self):
        result = {'data': [controllers]}
        return json.dumps(result, indent=4) + "\n"


class Controller():
    def GET(self, cntrlr):
        i = int(cntrlr)
        if (i + 1) > len(controllers):
            web.notfound()
            return

        result = {'data': [controllers[i]]}
        return json.dumps(result, indent=4) + "\n"


class Register():
    def POST(self):
        global controllers
        inputs = web.input()
        if not "name" in inputs:
            web.webapi.badrequest(message="Must supply name parameter.")
            return
        if not "host" in inputs:
            web.webapi.badrequest(message="Must supply host parameter.")
            return
        if not "port" in inputs:
            web.webapi.badrequest(message="Must supply port parameter.")
            return

        for cntrlr in controllers:
            if inputs.name in cntrlr.values():
                web.webapi.badrequest(message="name already exists.")
                return

        result = client("GET VERSION", inputs.host, inputs.port)
        string = result.split("\n")

        if string[0] == "version" and len(string[1]) > 0:
            controllers.append(dict(name="{}".format(inputs.name),
                                    host="{}".format(inputs.host),
                                    port="{}".format(inputs.port)))

            result = {'data': [dict(zip(tuple([string[0]]),[string[1]]))]}
            return json.dumps(result, indent=4) + "\n"
        else:
            web.notfound()


class Unregister():
    def POST(self, cntrlr):
        i = int(cntrlr)
        controllers.pop(i)


class Settings():
    def GET(self, cntrlr):
        i = int(cntrlr)
        if (i + 1) > len(controllers):
            web.notfound()
            return

        result = client("GET SETTINGS", controllers[i]['host'], controllers[i]['port'])
        string = result.split("\n")
        result = {'data': [dict(zip(tuple(string[0].split(",")),string[1].split(",")))]}
        return json.dumps(result, indent=4) + "\n"


class SettingName():
    def GET(self, cntrlr, setting):
        i = int(cntrlr)
        if (i + 1) > len(controllers):
            web.notfound()
            return

        result = client("GET SETTINGS", controllers[i]['host'], controllers[i]['port'])
        string = result.split("\n")
        settings = string[0].split(",")
        values = string[1].split(",")
        value = ""
        i = 0
        for item in settings:
            if item == setting:
                value = values[i]
                break
            i += 1

        if not len(value) > 0:
            web.notfound()
        else:
            result = {'data': [dict(zip(tuple([setting]),[value]))]}
            return json.dumps(result, indent=4) + "\n"

    def POST(self, cntrlr, setting):
        i = int(cntrlr)
        if (i + 1) > len(controllers):
            web.notfound()
            return

        inputs = web.input()
        if not "setTo" in inputs:
            web.webapi.badrequest(message="Must supply setTo parameter.")
            return

        if len(inputs.setTo) > 0:
            if setting == "coolto":
                cmd = "SET COOL TO {}".format(inputs.setTo)
            elif setting == "heatto":
                cmd = "SET HEAT TO {}".format(inputs.setTo)
            elif setting == "cool_offset":
                cmd = "SET COOL OFFSET {}".format(inputs.setTo)
            elif setting == "heat_offset":
                cmd = "SET HEAT OFFSET {}".format(inputs.setTo)
            elif setting == "tc_start_delay":
                cmd = "SET TC START DELAY {}".format(inputs.setTo)
            elif setting == "cool_start_delay":
                cmd = "SET COOL START DELAY {}".format(inputs.setTo)
            elif setting == "state_change_delay":
                cmd = "SET STATE CHANGE DELAY {}".format(inputs.setTo)
            elif setting == "temp_scale":
                cmd = "SET TEMP SCALE {}".format(inputs.setTo)

        result = client(cmd, controllers[i]['host'], controllers[i]['port'])
        result = client("APPLY", controllers[i]['host'], controllers[i]['port'])


class Save():
    def POST(self, cntrlr):
        i = int(cntrlr)
        if (i + 1) > len(controllers):
            web.notfound()
            return

        result = client("SAVE", controllers[i]['host'], controllers[i]['port'])


class Shutdown():
    def POST(self, cntrlr):
        i = int(cntrlr)
        if (i + 1) > len(controllers):
            web.notfound()
            return

        result = client("SHUTDOWN", controllers[i]['host'], controllers[i]['port'])
        controllers.pop(i)


class Status():
    def GET(self, cntrlr):
        i = int(cntrlr)
        if (i + 1) > len(controllers):
            web.notfound()
            return

        result = client("GET STATUS", controllers[i]['host'], controllers[i]['port'])
        string = result.split("\n")
        result = {'data': [dict(zip(tuple(string[0].split(",")),string[1].split(",")))]}
        return json.dumps(result, indent=4) + "\n"


class Temp():
    def GET(self, cntrlr):
        i = int(cntrlr)
        if (i + 1) > len(controllers):
            web.notfound()
            return

        result = client("\n", controllers[i]['host'], controllers[i]['port'])
        string = result.split("\n")
        result = {'data': [dict(zip(tuple(string[0].split(",")),string[1].split(",")))]}
        return json.dumps(result, indent=4) + "\n"


if __name__ == '__main__':
     app.run()
