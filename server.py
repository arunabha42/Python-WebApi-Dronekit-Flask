from flask import Flask, render_template
from flask_socketio import SocketIO
import dronekit
import sys
import socket
import threading
import time
import signal

connection_string = "tcp:127.0.0.1:5762"

socket.socket._bind = socket.socket.bind
def my_socket_bind(self, *args, **kwargs):
    self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return socket.socket._bind(self, *args, **kwargs)
socket.socket.bind = my_socket_bind
# okay, now that that's done...

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

def pyr(vehicle):
    
    @vehicle.on_message('VFR_HUD')
    def listener(self, name, message):
        print(f'Received VFR_HUD: {message}')
        socketio.emit('vfr_hud', {
                "airspeed": f'{round(message.airspeed, 1)} m/s',
                "groundspeed": f'{round(message.groundspeed, 1)} m/s',
                "heading": f'{message.heading}°',
                "throttle_percent": f'{message.throttle} %',
                "altitude_relative": f'{round(message.alt)} m',
                "climb_rate": f'{round(message.climb, 1)} m/s'
        })
    
    @vehicle.on_message('BATTERY_STATUS')
    def listener(self, name, message):
        print(f'Received BATTERY_STATUS: {message}')
        socketio.emit('battery_status', {
                "voltage": f'{round(message.voltages[0]/1000,2)} V',
                "current": message.current_battery,
                "capacity_used": f'{message.current_consumed} mAh',
                "percent_remaining": f'{str(message.battery_remaining)} %'
        })
    
    while True:
        time.sleep(.5)
        atti = vehicle.attitude
        if atti:
            socketio.emit('pyr_status', {
                "Pitch": atti.pitch,
                "Yaw": atti.yaw,
                "Roll": atti.roll,
                })
        else:
            socket.emit('pyr_status', None)

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) >= 2 else connection_string
    print ('Connecting to ' + target + '...')
    vehicle = dronekit.connect(target)
    vehiclethread2 = threading.Thread(target=pyr, args=(vehicle,))
    vehiclethread2.start()
    socketio.run(app, host="0.0.0.0", port=8080)


