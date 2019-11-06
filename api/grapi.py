#!/usr/local/bin/python

import os
import socket
import sys
import web
import json
import redis

# Current self
_VERSION_ = "1.5.2"

# Build num
_BUILD_ = os.getenv("GR_API_BUILD", "X.xxx")

# Redis Host
_RHOST_ = os.getenv("GR_REDIS_HOST", "grredis.greenroom.svc.cluster.local")

# Redis Port
_RPORT_ = os.getenv("GR_REDIS_PORT", "6379")

registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

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
        '/controllers/([0-9]{1,3})/unregister','Unregister',
        '/controllers/([0-9]{1,3})/version','Version',
        '/version','MyVersion'
)

app = web.application(urls, globals())

def client(data, host, port):
    payload = ""
    HOST, PORT = host, int(port)

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(data.encode())

        # Receive data from the server and shut down
        while True:
            received = sock.recv(1024)
            if len(received) > 0:
                payload += "{}\n".format(received.decode())
            else:
                break
    finally:
        sock.close()
        return payload


class MyVersion():
    def GET(self):

        web.header('Content-Type', 'application/json')
        result = dict(version=_VERSION_,build=_BUILD_)
        return json.dumps(result, indent=4) + "\n"


class ControllerIDs():
    def GET(self):
        ids = []
        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        ididx = registry.zrange("ididx", 0, -1)
        for name in ididx:
            id = int(registry.zscore("ididx", name))
            ids.append(id)

        web.header('Content-Type', 'application/json')
        result = {'controllers': ids}
        return json.dumps(result, indent=4) + "\n"


class Controllers():
    def GET(self):
        controllers = []

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        ididx = registry.zrange("ididx", 0, -1)

        for name in ididx:
            controller = registry.hgetall(name)
            controllers.append(controller)

        web.header('Content-Type', 'application/json')
        result = {'data': [controllers]}
        return json.dumps(result, indent=4) + "\n"


class Controller():
    def GET(self, id):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        controller = registry.hgetall(name[0])

        web.header('Content-Type', 'application/json')
        result = {'data': [controller]}
        return json.dumps(result, indent=4) + "\n"


class Register():
    def POST(self):
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
        if not "type" in inputs:
            web.webapi.badrequest(message="Must supply port parameter.")
            return
        if not "capability" in inputs:
            web.webapi.badrequest(message="Must supply port parameter.")
            return
        if not "vendor" in inputs:
            web.webapi.badrequest(message="Must supply port parameter.")
            return
        if not "model" in inputs:
            web.webapi.badrequest(message="Must supply port parameter.")
            return

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        ididx = registry.zrange("ididx", 0, -1)
        if ididx:
            if len(ididx) >= 1 and inputs.name in ididx:
                web.webapi.conflict(message="Name already exists.")
                return

        result = client("GET VERSION", inputs.host, inputs.port)
        string = result.split("\n")

        if string[0] == "version" and len(string[1]) > 0:
            if not registry.exists("ididx"):
                mapping = {inputs.name:'0'}
                registry.zadd("ididx", mapping, nx=True, xx=False, ch=False, incr=False)
                registry.persist("ididx")
            else:
                name = registry.zrange("ididx", -1, -1)
                lastIdx = int(registry.zscore("ididx", name[0]))
                nextIdx = lastIdx + 1
                mapping = {inputs.name:nextIdx}
                registry.zadd("ididx", mapping, nx=True, xx=False, ch=False, incr=False)

            mapping = {'name':inputs.name, 'host':inputs.host, 'port':inputs.port, 'type':inputs.type, 'capability':inputs.capability, 'vendor':inputs.vendor, 'model':inputs.model}
            registry.hmset(inputs.name, mapping)
            registry.persist(inputs.name)

            web.header('Content-Type', 'application/json')
            result = {'data': [dict(zip(tuple([string[0]]),[string[1]]))]}
            return json.dumps(result, indent=4) + "\n"
        else:
            web.webapi.internalerror(message="Invalid response from remote controller {}.".format(inputs.host))


class Unregister():
    def POST(self, id):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        result = registry.zremrangebyscore("ididx", i, i)
        result = registry.delete(name[0])

        web.webapi.ok()


class Settings():
    def GET(self, id):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        controller = registry.hgetall(name[0])

        result = client("GET SETTINGS", controller['host'], controller['port'])
        string = result.split("\n")

        web.header('Content-Type', 'application/json')
        result = {'data': [dict(zip(tuple(string[0].split(",")),string[1].split(",")))]}
        return json.dumps(result, indent=4) + "\n"


class SettingName():
    def GET(self, id, setting):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        controller = registry.hgetall(name[0])

        result = client("GET SETTINGS", controller['host'], controller['port'])
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
            web.header('Content-Type', 'application/json')
            result = {'data': [dict(zip(tuple([setting]),[value]))]}
            return json.dumps(result, indent=4) + "\n"

    def POST(self, id, setting):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        controller = registry.hgetall(name[0])

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

        result = client(cmd, controller['host'], controller['port'])
        result = client("APPLY", controller['host'], controller['port'])

        web.webapi.ok()


class Save():
    def POST(self, id):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        controller = registry.hgetall(name[0])

        result = client("SAVE", controller['host'], controller['port'])

        web.webapi.ok()


class Shutdown():
    def POST(self, id):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        controller = registry.hgetall(name[0])

        result = client("SHUTDOWN", controller['host'], controller['port'])
        result = registry.zremrangebyscore("ididx", i, i)
        result = registry.delete(name[0])

        web.webapi.ok()

class Status():
    def GET(self, id):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        controller = registry.hgetall(name[0])

        result = client("GET STATUS", controller['host'], controller['port'])
        string = result.split("\n")

        web.header('Content-Type', 'application/json')
        result = {'data': [dict(zip(tuple(string[0].split(",")),string[1].split(",")))]}
        return json.dumps(result, indent=4) + "\n"


class Temp():
    def GET(self, id):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        controller = registry.hgetall(name[0])

        result = client("\n", controller['host'], controller['port'])
        string = result.split("\n")

        web.header('Content-Type', 'application/json')
        result = {'data': [dict(zip(tuple(string[0].split(",")),string[1].split(",")))]}
        return json.dumps(result, indent=4) + "\n"


class Version():
    def GET(self, id):
        i = int(id)

        global registry
        registry = redis.Redis(host=_RHOST_, port=_RPORT_, db=0, decode_responses=True)

        name = registry.zrangebyscore("ididx", i, i)
        if len(name) == 0:
            web.notfound()
            return

        controller = registry.hgetall(name[0])

        result = client("GET VERSION\n", controller['host'], controller['port'])
        string = result.split("\n")

        web.header('Content-Type', 'application/json')
        result = {'data': [dict(zip(tuple(string[0].split(",")),string[1].split(",")))]}
        return json.dumps(result, indent=4) + "\n"


if __name__ == '__main__':

    app.run()
