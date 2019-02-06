Welcome to the Greenroom Control System!

This package, and the code within, are part of a real-life proof-of-concept solution for controlling greenhouse fans and heaters.
The solution is supported by two discrete services. The first is an API that acts as a master control unit, and one or more temperature controllers.
Each controller consists of a Raspberry Pi B with a Robogaia Temperature Control Plane pi-HAT attached. Every controller runs a TCP socket server to listen for remote commands.
These remote commands can come from either the API, or the CLI client utility, and are used to alter the runtime or even persistent settings and configs for the controllers.

To get started...

Installation
------------
1. Run the temperature_controller_install script located in the install folder. This will install the init.d boot script, a GPIO init script, along with a udev rule. The init script is executed by the server process at start up, if needed.

2. The server process uses a configuration file, config.json for persistent parameters and settings. You can edit this file and set your own parameters and initialization settings. Most of them are pretty self-explanatory, and don't need to be changed initially. You will want to make sure the api_url points to the correct url for which your api is servicing.

3. The API must start up first, followed by one or more servers (controllers). This is so the servers can register to the API with their name, IP, and port. Both the API and server process can be run on the same controller unit, if desired.


API Examples
------------

List registered controllers:

	curl http://localhost:8080/controllers

List only the controller IDs:

	curl http://localhost:8080/controllers/ids

Register a controller:

	curl http://localhost:8080/controllers/register --data-urlencode "name=controller1" \
							--data-urlencode "host=localhost" \
							--data-urlencode "port=12000"
List controller 0 configuration:

	curl http://localhost:8080/controllers/0

Fetch current temperature from controller 0:

	curl http://localhost:8080/controllers/0/temp

List all settings from controller 0 or 1:

	curl http://localhost:8080/controllers/0/settings
	curl http://localhost:8080/controllers/1/settings

Update a setting on controller 0:

	curl http://localhost:8080/controllers/0/settings/cool_offset --data-urlencode "setTo=5"
	curl http://localhost:8080/controllers/0/settings/cool_start_delay --data-urlencode "setTo=15"
	curl http://localhost:8080/controllers/0/settings/cool_start_delay --data-urlencode "setTo=30"
	curl http://localhost:8080/controllers/0/settings/coolto --data-urlencode "setTo=78"
	curl http://localhost:8080/controllers/0/settings/heat_offset --data-urlencode "setTo=2"
	curl http://localhost:8080/controllers/0/settings/heatto --data-urlencode "setTo=74"
	curl http://localhost:8080/controllers/0/settings/state_change_delay --data-urlencode "setTo=120"
	curl http://localhost:8080/controllers/0/settings/tc_start_delay --data-urlencode "setTo=15"
	curl http://localhost:8080/controllers/0/settings/tc_start_delay --date-urlencode "setTo=15"

Save configuration and settings to file:

	curl http://localhost:8080/controllers/0/save -d save 

Shutdown the server running on controller 0:

	curl http://localhost:8080/controllers/0/shutdown -d shutdown

	NOTE: This will also unregister the server from the API.

Display the current relay states:

	curl http://localhost:8080/controllers/0/status

Unregister controller 0:

	curl http://localhost:8080/controllers/0/unregister --data-urlencode "name=controller1"

	NOTE: This doesn't shutdown the server process, rather only removes it from the API.


Client Examples
---------------

Fetches the current temp:
	grclient.py 

Applies any changed settings:
	grclient.py apply

Fetches current settings:
	grclient.py get settings

Displays current relay states:
	grclient.py get status

Set cool offset in degrees:
	grclient.py set cool offset 1

Set cool offset in degrees:
	grclient.py set heat offset 2

Set cool or heat in degrees:
	grclient.py set cool to 68
	grclient.py set heat to 64

Change the temperature scale from Celcius to Fahrenheit or vice versa:
	grclient.py set temp scale c
	grclient.py set temp scale f

Shutdown the server process:
	grclient.py shutdown


Utilities
---------

There are a collection of shell scripts located in the utils folder. These scripts do much of what the server is capable of providing, but from the command line. They were provided as part of the source package from which this package was derived.
