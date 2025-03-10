import serial
import matplotlib.pyplot as plt
import numpy as np
from collections import deque

# Initialize serial port
ser = serial.Serial('/dev/ttyACM0', 9600)

# Set up the plot
plt.ion()
fig, ax = plt.subplots()
ydata = deque([0]*100, maxlen=100)  # Store the last 100 data points
line, = ax.plot(ydata)
ax.set_ylim(0, 1024)  # Adjust based on the range of your EMG data

def update_plot():
    try:
        while True:
            data = ser.readline().decode('utf-8').strip()  # Read data from serial port
            if data.isdigit():
                ydata.append(int(data))
                line.set_ydata(ydata)
                ax.draw_artist(ax.patch)
                ax.draw_artist(line)
                fig.canvas.blit(ax.bbox)
                fig.canvas.flush_events()
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        ser.close()

if __name__ == "__main__":
    update_plot()
