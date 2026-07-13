# NFT Telemetry and Automation

A portfolio and special-interest project designed to collect environmental and visual data during hydroponic grow cycles.

## Hardware 

* **Edge Compute:** Raspberry Pi 5
* **Sensor Suite:** Atlas Scientific environmental monitoring kits
* **Peripherals:** Insta360 Link 2 with motorized gimble
* **Future:** Sensor expansion including ambient t*emp and humidity sensors, water level sensors.

##  Status

* **Repository has been comitted to GitHub.
* **Base hardware infrastructure has been tested and calibrated.
* **Updated from csv records to postgres database, with ability to download csv datasets
* **Abstracted bulky sql, js, and htmx code from main python codesets

## What's being worked on

* ** Sending Video4Linux2 command/control instructions to Insta360 Link 2 Camera for pan, tilt, and zoom
* ** Writing calibration tool that uses cv to tell the camera to find square markers, and record the gimbel coordinates
* ** Write daily script that takes a snapshot of each of the plants in the system
* ** Using marker pixels, measure plant growth/mass for rate calculation
* ** Dashboard tools for data insights. Sliders, data filtering, etc.

## Screenshots

To be added. For access to live system, please contact repository owner @ scott.pitcock@csuglobal.edu
