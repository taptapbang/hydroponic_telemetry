#this script reads data from I2C sensors and writes the data to a data source
#currently CSV

import collections
import io
import os
import sys
import csv
import time
import fcntl
from datetime import datetime

#hardware setup
PH_ADDRESS = 0x63
EC_ADDRESS = 0x64
TEMP_ADDRESS = 0x66
I2C_SLAVE = 0x0703
I2C_BUS = 1

#time intervals
TIME_INT = 300 # read interval in seconds (300 = 5 mins)
AVG_INT_A = 60 #in mins, interval 1 (60 = 1 hr)
AVG_INT_B = 1440 #in mins, interval 2 (1440 = 24 hours)

#output
#Placeholder, we're going to do daily logs eventually
#We may have to keep interval data in memory, or a working cache.
#or some way to keep the average data in-tact in case of power-outage.
OUTPUT_FILE = "hydro_log.csv"

#ATLAS hardware communication
class AtlasComm:

    def __init__(self, address, bus=1):
        self.bus = bus
        self.address = address

        try:
            self.file_read = io.open(f"/dev/i2c-{bus}", "rb", buffering=0)
            self.file_write = io.open(f"/dev/i2c-{bus}", "wb", buffering=0)

        except Exception as e:
            print(e)
            sys.exit(1)

    # which sensor are we targeting
    def target_sensor(self):
        fcntl.ioctl(self.file_read, I2C_SLAVE, self.address)
        fcntl.ioctl(self.file_write, I2C_SLAVE, self.address)

    # send a string to the target sensor
    def write(self, command):
        self.target_sensor()
        command += "\0"
        self.file_write.write(command.encode('latin-1'))

    # reads target sensor and parses Atlas status code byte
    def read(self):
        self.target_sensor()

        try:
            data = self.file_read.read(31)
            status = data[0]

            if status == 1:
                return data[1:].decode('latin-1').rstrip('\x00')

            elif status == 254:
                return "Busy..."

            else:
                return f"Error code ({status})"

        except Exception as e:
            return str(e)

    def send(self, command, wait_time=1.0):
        try:
            self.write(command)
            time.sleep(wait_time)
            return self.read()
        except Exception as e:
            return str(e)

#data functions

#convert sensor output to float
def conv_float(sensor_output):
    try:
        return float(sensor_output)
    except (ValueError, TypeError):
        return None

#get avg from deque
def get_avg(history, sum_values):
    recent = list(history)[-sum_values:]
    if not recent:
        return "N/A"
    return round(sum(recent)/len(recent), 3)

#main
def main():
    print(f"Starting monitor on I2C bus {I2C_BUS}")

    sensor_ph = AtlasComm(address=PH_ADDRESS, bus=I2C_BUS)
    sensor_ec = AtlasComm(address=EC_ADDRESS, bus=I2C_BUS)
    sensor_temp = AtlasComm(address=TEMP_ADDRESS, bus=I2C_BUS)

    #period calc
    int_a = max(1, int((AVG_INT_A * 60) / TIME_INT))
    int_b = max(1, int((AVG_INT_B * 60) / TIME_INT))
    max_hist = max(int_a, int_b)

    #history deques
    temp_history = collections.deque(maxlen=max_hist)
    ph_history = collections.deque(maxlen=max_hist)
    ec_history = collections.deque(maxlen=max_hist)

    #output
    exists = os.path.isfile(OUTPUT_FILE)

    with open(OUTPUT_FILE, mode='a', newline='') as output_file:
        writer = csv.writer(output_file)
        if not exists:
            #create
            header = [
                "timestamp", "temp", "ph", "ec",
                f"temp_avg_{AVG_INT_A}m", f"ph_avg_{AVG_INT_A}m", f"ec_avg_{AVG_INT_A}m",
                f"temp_avg_{AVG_INT_B}m", f"ph_avg_{AVG_INT_B}m", f"ec_avg_{AVG_INT_B}m"
            ]
            writer.writerow(header)
            print(f"Log created: {OUTPUT_FILE}")

    print("logging started...")

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            #fetch block
            temp = sensor_temp.send('r')
            ph = sensor_ph.send('r')
            ec = sensor_ec.send('r')

            #build history
            t = conv_float(temp)
            if t is not None: temp_history.append(t)
            p = conv_float(ph)
            if p is not None: ph_history.append(p)
            e = conv_float(ec)
            if e is not None: ec_history.append(e)

            #interval A avgs
            ta = get_avg(temp_history, int_a)
            pa = get_avg(ph_history, int_a)
            ea = get_avg(ec_history, int_a)

            #interval B avgs
            tb = get_avg(temp_history, int_b)
            pb = get_avg(ph_history, int_b)
            eb = get_avg(ec_history, int_b)

            #console output verification
            print(f"\n[Time:{timestamp}|temp:{temp}|ph:{ph}|ec:{ec}]")

            with open(OUTPUT_FILE, mode='a', newline='') as output_file:
                writer = csv.writer(output_file)
                writer.writerow([
                    timestamp, temp, ph, ec, ta, pa, ea, tb, pb, eb
                ])

            time.sleep(max(0, TIME_INT - 3))
    except KeyboardInterrupt:
        print("\nlogging stopped...")

if __name__ == "__main__":
    main()