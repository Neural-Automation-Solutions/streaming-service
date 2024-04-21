from http.client import HTTPSConnection
import threading
import json
import paho.mqtt.client as mqtt

from videolib.video import Video

# Initialize video
vid = Video()

# Set up MQTT client
def on_connect(client, userdata, flags, rc, properties):
    print(f'Connected with result code {rc}')
    client.subscribe('vdc-1/streaming')

def on_message(client, userdata, msg):
    global vid
    
    message = json.loads(msg.payload.decode())
    command = message['command']
    
    if command == 'start-stream-bboxes':
        print('Starting stream...')
        vid = Video(port=5556)
    elif command == 'stop-stream-bboxes':
        print('Stopping stream...')
        vid = Video()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set('nas', 'apoel123')
client.connect('mqtt-broker.nas-ai.org', 1883, 60)

client.loop_start()

# Set up a persistent HTTPS connection
url = '/stream/test-stream'
headers = {'Content-Type': 'image/jpeg'}

# Stack to hold frames
frame_stack = []

# Lock to manage access to the frame stack
lock = threading.Lock()

def send_frame():
    conn = None

    def ensure_connection():
        nonlocal conn
        if conn is None or conn.sock is None:
            conn = HTTPSConnection('dashboard.nas-ai.org')

    while True:
        frame = None
        lock.acquire()
        if frame_stack:
            frame = frame_stack.pop()  # Get the most recent frame
        lock.release()

        if frame is not None:
            try:
                ensure_connection()
                conn.request('POST', url, frame, headers)
                response = conn.getresponse()
                if response.status == 200:
                    print('Frame sent successfully.')
                else:
                    print(f'Failed to send frame. Status code: {response.status}')
                response.read()  # Important to read response to free up the connection
            except Exception as e:
                print(f'Error occurred while sending frame to server: {e}')
                conn.close()
                conn = None  # Force reconnection on next iteration

# Start a thread for sending frames
thread = threading.Thread(target=send_frame)
thread.daemon = True
thread.start()

# Main loop to capture frames
while True:
    frame = vid.get_frame_bytes()
    lock.acquire()
    frame_stack = [frame]  # Reset the stack with the most recent frame
    lock.release()

client.loop_stop()
