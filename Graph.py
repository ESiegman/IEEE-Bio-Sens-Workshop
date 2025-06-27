import tkinter as tk
from tkinter import ttk
import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
import threading
import queue
import time

# --- Required Package Installs ---
# numpy
# pyserial
# matplotlib

# --- Configuration ---
# Set these values to match the setup
SERIAL_PORT = '/dev/COM4'  
BAUD_RATE = 9600
GRID_ROWS = 8  # Number of rows in your sensor grid
GRID_COLS = 8  # Number of columns in your sensor grid

class SensorGridVisualizer:
    """
    A GUI application to visualize real-time sensor data from an Arduino
    in a heatmap and a 3D surface plot.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Sensor Grid Visualizer")

        # --- Data Queue ---
        # A thread-safe queue to pass data from the serial reading thread
        # to the main GUI thread.
        self.data_queue = queue.Queue()

        # --- Setup Plots ---
        # Create a main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure the grid layout
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Heatmap Plot ---
        self.fig_heatmap = plt.Figure(figsize=(6, 5), dpi=100)
        self.ax_heatmap = self.fig_heatmap.add_subplot(111)
        self.heatmap_canvas = FigureCanvasTkAgg(self.fig_heatmap, master=main_frame)
        self.heatmap_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5)
        self.im = self.ax_heatmap.imshow(np.zeros((GRID_ROWS, GRID_COLS)), cmap='viridis', vmin=0, vmax=1023)
        self.fig_heatmap.colorbar(self.im, ax=self.ax_heatmap)
        self.ax_heatmap.set_title("Pressure Heatmap")
        self.ax_heatmap.set_xlabel("Sensor Column")
        self.ax_heatmap.set_ylabel("Sensor Row")


        # --- 3D Surface Plot ---
        self.fig_3d = plt.Figure(figsize=(6, 5), dpi=100)
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        self.surface_canvas = FigureCanvasTkAgg(self.fig_3d, master=main_frame)
        self.surface_canvas.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5)
        self.ax_3d.set_title("3D Pressure Surface")
        self.ax_3d.set_zlim(0, 1023) # Analog read range
        self.ax_3d.set_xlabel("Sensor Column")
        self.ax_3d.set_ylabel("Sensor Row")
        self.ax_3d.set_zlabel("Pressure Reading")


        # --- Start Serial Reader Thread ---
        self.serial_thread = threading.Thread(target=self.read_from_serial, daemon=True)
        self.serial_thread.start()

        # --- Start GUI Update Loop ---
        self.update_plots()

    def read_from_serial(self):
        """
        Reads data from the serial port in a separate thread.
        Expected format: "val1,val2,val3,...,valN\n"
        """
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            time.sleep(2) # Wait for connection to establish
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
        except serial.SerialException as e:
            print(f"Error: Could not open serial port {SERIAL_PORT}. {e}")
            print("Please check your SERIAL_PORT configuration and connection.")
            return

        while True:
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    # Parse the comma-separated values
                    values = [int(v) for v in line.split(',')]
                    num_expected_values = GRID_ROWS * GRID_COLS
                    if len(values) == num_expected_values:
                        # Reshape the 1D array into a 2D grid
                        grid_data = np.array(values).reshape((GRID_ROWS, GRID_COLS))
                        self.data_queue.put(grid_data)
                    else:
                        print(f"Warning: Received {len(values)} values, expected {num_expected_values}. Ignoring line.")
                except (ValueError, UnicodeDecodeError) as e:
                    # Catch potential errors if the line is not formatted correctly
                    # or contains non-UTF8 characters.
                    print(f"Could not parse line: {line}. Error: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")


    def update_plots(self):
        """
        Periodically checks the queue for new data and updates the plots.
        """
        try:
            # Process all available data in the queue
            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()

                # --- Update Heatmap ---
                self.im.set_data(data)
                self.im.set_clim(vmin=data.min(), vmax=data.max()) # Auto-adjust color scale

                # --- Update 3D Surface Plot ---
                self.ax_3d.clear() # Clear previous surface
                X = np.arange(0, GRID_COLS, 1)
                Y = np.arange(0, GRID_ROWS, 1)
                X, Y = np.meshgrid(X, Y)
                self.ax_3d.plot_surface(X, Y, data, cmap='viridis', edgecolor='none')
                self.ax_3d.set_zlim(0, 1023) # Reset z-limit after clearing
                self.ax_3d.set_title("3D Pressure Surface")
                self.ax_3d.set_xlabel("Sensor Column")
                self.ax_3d.set_ylabel("Sensor Row")
                self.ax_3d.set_zlabel("Pressure Reading")


            # Redraw the canvases
            self.heatmap_canvas.draw()
            self.surface_canvas.draw()

        except queue.Empty:
            # No new data, just wait for the next call.
            pass
        finally:
            # Schedule the next update
            self.root.after(100, self.update_plots) # Update every 100ms

if __name__ == '__main__':
    root = tk.Tk()
    app = SensorGridVisualizer(root)
    root.mainloop()
