from pylogix import PLC
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import time
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)

# PLC Configuration
plc_ip = '10.60.85.21'
MAX_WORKERS = 100
BATCH_SIZE = 50
plc = PLC()
plc.IPAddress = plc_ip
is_connected = True  # Assume connected initially

# Function to write data to PLC in batch
def batch_write(batch):
    try:
        for key, value in batch:
            plc.Write(key, str(value))  # Convert value to string before writing
        return True
    except Exception as e:
        print("Error during batch write: {}".format(str(e)))
        return False

# Endpoint to insert data into PLC
@app.route('/insertDataToPlc', methods=['POST'])
@cross_origin()
def insert_data_to_plc():
    try:
        global is_connected
        if not is_connected:
            plc.IPAddress = plc_ip
            is_connected = True

        data_list = request.json
        write_operations = [(key, value) for item in data_list for key, value in item.items()]

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(batch_write, write_operations[i:i + BATCH_SIZE])
                       for i in range(0, len(write_operations), BATCH_SIZE)]

            for future in as_completed(futures):
                if not future.result():
                    return jsonify({"message": "Error writing data to PLC."}), 500

        end_time = time.time()
        execution_time = end_time - start_time
        print("Time taken: {:.2f} seconds".format(execution_time))

        return jsonify({"message": "Data written successfully.", "time": execution_time}), 200
    except Exception as e:
        return jsonify({"message": "Error writing data to PLC.", "error": str(e)}), 500

# Endpoint to close PLC connection
@app.route('/closeConnection', methods=['GET'])
@cross_origin()
def close_connection():
    global is_connected
    try:
        if is_connected:
            plc.Close()
            is_connected = False
            print("Connection to PLC closed.")
        return jsonify({"message": "Connection to PLC closed successfully.", "error": None}), 200
    except Exception as e:
        return jsonify({"message": "Error closing connection.", "error": str(e)}), 500

# Endpoint to check if an IP address is reachable
@app.route('/ping', methods=['GET'])
def ping():
    ip_address = request.args.get('ip')
    if not ip_address:
        return jsonify({"message": "No IP address provided.", "error": None}), 400

    try:
        command = ['ping', '-n', '1', ip_address] if platform.system().lower() == "windows" else ['ping', '-c', '1', ip_address]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return jsonify({"ip": ip_address, "reachable": True}), 200
        else:
            return jsonify({"ip": ip_address, "reachable": False}), 200
    except Exception as e:
        return jsonify({"message": "Error during ping.", "error": str(e)}), 500

# Endpoint to check Wi-Fi connectivity
@app.route('/pingWifi', methods=['GET'])
def ping_wifi():
    wifi_ip_address = request.args.get('wifi_ip_address')
    if not wifi_ip_address:
        return jsonify({"message": "No Wi-Fi IP address provided.", "error": None}), 400

    try:
        command = ['ping', '-n', '1', wifi_ip_address] if platform.system().lower() == "windows" else ['ping', '-c', '1', wifi_ip_address]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if "destination host unreachable" in stdout.decode('utf-8').lower():
            return jsonify({"ip": wifi_ip_address, "reachable": False, "message": "Internet connection is not active."}), 200
        elif process.returncode == 0:
            return jsonify({"ip": wifi_ip_address, "reachable": True}), 200
        else:
            return jsonify({"ip": wifi_ip_address, "reachable": False}), 200
    except Exception as e:
        return jsonify({"message": "Error during Wi-Fi ping.", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8083)
