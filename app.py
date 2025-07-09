from flask import Flask, render_template, Response
import cv2
import RPi.GPIO as GPIO
from flask_socketio import SocketIO, emit
import threading
import time
import ssl

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a8b7c6d5e4f3g2h1i0j9k8l7m6n5o4p3q2r1s0t'  # Change this!
app.config['SSL_CONTEXT'] = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
app.config['SSL_CONTEXT'].load_cert_chain('cert.pem', 'key.pem')  # Replace with your cert/key paths

socketio = SocketIO(app, cors_allowed_origins="*", ssl_context=app.config['SSL_CONTEXT'])  # Enable SSL

# GPIO Pin Definitions (Adjust these to your wiring!)
ENA = 17  # Motor A Enable (PWM)
IN1 = 27  # Motor A Input 1
IN2 = 22  # Motor A Input 2
ENB = 23  # Motor B Enable (PWM)
IN3 = 24  # Motor B Input 3
IN4 = 25  # Motor B Input 4

GPIO.setmode(GPIO.BCM)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

pwm_A = GPIO.PWM(ENA, 100)  # 100 Hz PWM frequency
pwm_B = GPIO.PWM(ENB, 100)
pwm_A.start(0)  # Start with 0% duty cycle (stopped)
pwm_B.start(0)

current_speed_A = 0
current_speed_B = 0

# Video Stream
camera = cv2.VideoCapture(0)  # 0 is usually the default webcam

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# WebSocket Event Handlers
@socketio.on('connect')
def test_connect():
    print('Client connected')
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

@socketio.on('control_command')
def handle_control(data):
    action = data['action']

    if action == 'forward':
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        current_speed_A = 50
        current_speed_B = 50
        pwm_A.ChangeDutyCycle(current_speed_A)
        pwm_B.ChangeDutyCycle(current_speed_B)
    elif action == 'backward':
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        current_speed_A = 50
        current_speed_B = 50
        pwm_A.ChangeDutyCycle(current_speed_A)
        pwm_B.ChangeDutyCycle(current_speed_B)
    elif action == 'left':
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        current_speed_A = 50
        current_speed_B = 50
        pwm_A.ChangeDutyCycle(current_speed_A)
        pwm_B.ChangeDutyCycle(current_speed_B)
    elif action == 'right':
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        current_speed_A = 50
        current_speed_B = 50
        pwm_A.ChangeDutyCycle(current_speed_A)
        pwm_B.ChangeDutyCycle(current_speed_B)
    elif action == 'stop':
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.LOW)
        current_speed_A = 0
        current_speed_B = 0
        pwm_A.ChangeDutyCycle(0)
        pwm_B.ChangeDutyCycle(0)
    elif action == 'speed_up':
        current_speed_A = min(100, current_speed_A + 10)
        current_speed_B = min(100, current_speed_B + 10)
        pwm_A.ChangeDutyCycle(current_speed_A)
        pwm_B.ChangeDutyCycle(current_speed_B)
    elif action == 'speed_down':
        current_speed_A = max(0, current_speed_A - 10)
        current_speed_B = max(0, current_speed_B - 10)
        pwm_A.ChangeDutyCycle(current_speed_A)
        pwm_B.ChangeDutyCycle(current_speed_B)

    emit('rover_status', {'speed_a': current_speed_A, 'speed_b': current_speed_B}) # Send status back to client

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    # No need for GPIO.cleanup() here, socketio.run handles it on exit