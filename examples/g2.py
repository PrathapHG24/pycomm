#this is final working code using this we created Window service Cambro_PLC_Python2#
from pylogix import PLC
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import time
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PLC Configuration
plc_ip = '10.60.85.21'
MAX_WORKERS = 100
BATCH_SIZE = 50
RETRY_ATTEMPTS = 3  # Number of retries for failed writes
plc = PLC()
plc.IPAddress = plc_ip
is_connected = True  # Assume connected initially

# Function to write data to PLC in batch with retries
def batch_write_with_retry(batch):
    for attempt in range(RETRY_ATTEMPTS):
        try:
            for key, value in batch:
                plc.Write(key, str(value))  # Convert value to string before writing
            return True
        except Exception, e:  # Python 2.7 syntax
            logger.error("Attempt %d failed: %s" % (attempt + 1, str(e)))  # Python 2.7 string formatting
            time.sleep(1)  # Wait before retrying
    return False

# Function to check and establish PLC connection
def ensure_plc_connection():
    global is_connected
    if not is_connected:
        try:
            plc.IPAddress = plc_ip
            plc.Open()
            is_connected = True
            logger.info("PLC connection re-established.")
        except Exception, e:  # Python 2.7 syntax
            logger.error("Failed to re-establish PLC connection: %s" % str(e))  # Python 2.7 string formatting
            is_connected = False
    return is_connected

# Endpoint to insert data into PLC
@app.route('/insertDataToPlc', methods=['POST'])
@cross_origin()
def insert_data_to_plc():
    try:
        # Ensure PLC connection is active
        if not ensure_plc_connection():
            return jsonify({"message": "Unable to connect to PLC.", "error": "PLC connection failed"}), 500

        data_list = request.json
        if not data_list:
            return jsonify({"message": "No data provided.", "error": None}), 400

        write_operations = [(key, value) for item in data_list for key, value in item.items()]

        start_time = time.time()
        success_count = 0
        failure_count = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(batch_write_with_retry, write_operations[i:i + BATCH_SIZE])
                       for i in range(0, len(write_operations), BATCH_SIZE)]

            for future in as_completed(futures):
                if future.result():
                    success_count += 1
                else:
                    failure_count += 1

        end_time = time.time()
        execution_time = end_time - start_time

        if failure_count > 0:
            logger.warning("Partial failure: %d batches failed to write." % failure_count)  # Python 2.7 string formatting
            return jsonify({
                "message": "Partial success: %d batches written, %d batches failed." % (success_count, failure_count),
                "time": execution_time
            }), 207  # 207 Multi-Status

        logger.info("All data written successfully in %.2f seconds." % execution_time)  # Python 2.7 string formatting
        return jsonify({"message": "Data written successfully.", "time": execution_time}), 200

    except Exception, e:  # Python 2.7 syntax
        logger.error("Error in insert_data_to_plc: %s" % str(e))  # Python 2.7 string formatting
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
            logger.info("Connection to PLC closed.")
        return jsonify({"message": "Connection to PLC closed successfully.", "error": None}), 200
    except Exception, e:  # Python 2.7 syntax
        logger.error("Error closing PLC connection: %s" % str(e))  # Python 2.7 string formatting
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
    except Exception, e:  # Python 2.7 syntax
        logger.error("Error during ping: %s" % str(e))  # Python 2.7 string formatting
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
    except Exception, e:  # Python 2.7 syntax
        logger.error("Error during Wi-Fi ping: %s" % str(e))  # Python 2.7 string formatting
        return jsonify({"message": "Error during Wi-Fi ping.", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8083)