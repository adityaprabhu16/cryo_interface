# Multi-Sensor Platform for Monitoring Cryoprotective Agents (CPAs)

**Course:** ECE Senior Design (EE 4951W) at University of Minnesota

**Project Advisor:** Professor Rhonda Franklin

**Students:**
* Aditya Prabhu
* Brett Duncan
* Jack Sellner
* Luke Lundell

## Setup

Install required Python packages:

`pip install -r requirements.txt`

## Run

`python main.py`

Note: The application has been tested using Python 3.9. Python 3.5 or newer is required.

Access the GUI by going to `localhost:4951` in your web browser.

## Application

File structure:
```
|- app_thread.py
|- config.py
|- handler.py
|- main.py
|- metadata.py
|- utils.py
|- vna.py
|- experiments/
   |- name_cpa_date/
   ...
```

**app_thread.py**

The `AppThread` class extends the built-in `Thread` class from the `threading` module. This class is responsible for collecting data concurrent to the web server running.

**handler.py**

The `build_response_handler` function takes in `app_thread` as its only argument and returns a class that extends `BaseHTTPRequestHandler`. This is done so the the returned handler class can interact with app_thread while serving HTTP requests. The purpose of the returned handler class is to implement the logic necessary to support the GUI on the server side.

## Microcontroller

We use a ESP32 microcontroller to communicate with MAX31856 thermocouple temperature measurement ICs over SPI. The source code for the microcontroller can be found in `temperature_measurement/`. This code was compiled and flashed to the microcontroller using the Arduino IDE (available here: https://www.arduino.cc/en/software).

### IDE Setup

The Arduino IDE does not natively support the ESP32 as a target to build for. To install the required packages go to:

`Tools` -> `Board` -> `Boards Manager` -> Search for "esp32" -> Install "esp32 by Espressif Systems" (We use version 2.0.7)

This will install the packages required for programming the ESP32.

For interfacing with the MAX31856 IC over SPI we use the Adafruit MAX31856 library. This library needs to be installed using the IDE's library manager. Got to:

`Sketch` -> `Include Library` -> `Manage Libraries...` -> Search for "MAX31856" -> Install "Adafruit MAX31856 library by Adafruit" (We use version 1.2.5)

When programming the ESP32 the target board should be set to "ESP32-WROOM-DA Module" (Note: this may change if you use a different version of the ESP32.)

## Web API

This API is used by the GUI to interact with the Python application.

### GET

**GET /api/metadata**

Get the metadata stored by the server.

`returns:` JSON dictionary of the metadata.

**GET /api/config**

Get the current configuration from the server.

`returns:` JSON dictionary of the current server configuration.

**GET /api/devices**

Detect available USB devices.

`returns:` JSON list of ports that have available USB devices.

**GET /api/stream_data**

Send all data to the client and stream it as it becomes available.

`returns:` Stream of JSON events.

**GET /api/running**

Whether or not an experiment is currently running.

`returns:` `true` if an experiment is running, `false` otherwise.

**GET /api/previous_experiments**

Get a list of previous experiments.

`returns:` JSON list containing previous experiments.

**GET /api/experiment_selected**

Whether or not the user has selected an experiment.

`returns:` `true` if an experiment has been selected, `false` otherwise.

### POST

**POST /api/config**

Update the data collection configuration (sampling frequency, etc.).

`send:` JSON containing the config as a dictionary.

**POST /api/start**

Signal to the application to begin collecting data.

**POST /api/stop**

Signal to the application to stop collecting data.

**POST /api/create_experiment**

Create a new experiment. This will create a new directory using fields from the metadata.

`send:` JSON dictionary containing metadata.

**POST /api/connect**

Connect to the USB device with the provided port.

`send:` Port of the device to connect to.

**POST /api/connect_vna1**

Connect to the VNA with the specified IP address.

`send:` IP address as a string.

**POST /api/connect_vna2**

Connect to the VNA with the specified IP address.

`send:` IP address as a string.
