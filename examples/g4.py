from pylogix import PLC
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import time
import subprocess
import platform
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PLC Configuration
plc_ip = '10.60.85.21'
plc = PLC()
plc.IPAddress = plc_ip
is_connected = True  # Assume connected initially

# Define the tags you want to read from the PLC
tags_to_read = [
      "Cape2",
        "Case_GTIN_Barcode2",
        "Case_GTIN_Readable2",
        "Case_GTIN_Text2",
        "Case_Qty2",
        "Color_Description2",
        "Comment_Line_1_2",
        "Comment_Line_2_2",
        "Comment_Line_3_2",
        "Gross_Weight_Kgs2",
        "Gross_Weight_Lbs2",
        "Item_UPC2",
        "Item_UPC_Text2",
        "Label_Identifier2",
        "Literal_Label_Name2",
        "Literal_SO_Number2",
        "Production_Code2",
        "Registered_Trademark2",
        "Resource_Item_Description2",
        "Resource_Item_Nu2",
        "Resource_Item_Number_Barcode2",
        "Result2",
        "ResultDescription2",
        "Schedule_Olsn_Release2",
        "Schedule_Olsn_Release_Barcode2",
        "SO_Number2",
        "SO_Number_Barcode2"
]  # Replace with actual tags

# Function to write data to PLC in batch with retries
def batch_write_with_retry(batch):
    for attempt in range(3):  # Retry up to 3 times
        try:
            for key, value in batch:
                plc.Write(key, str(value))  # Convert value to string before writing
            return True
        except Exception as e:
            logger.error("Attempt {} failed: {}".format(attempt + 1, str(e)))
            time.sleep(1)  # Wait before retrying
    return False

# Function to read data from PLC sequentially
def batch_read(tags):
    results = {}
    for tag in tags:
        try:
            logger.info("Reading tag: {}".format(tag))
            result = plc.Read(tag)
            logger.info("Read result for tag {}: {}".format(tag, result.Value))
            results[tag] = result.Value
        except Exception as e:
            logger.error("Error reading tag {}: {}".format(tag, str(e)))
            results[tag] = None
    return results

# Function to check and establish PLC connection
def ensure_plc_connection():
    global is_connected
    if not is_connected:
        try:
            plc.IPAddress = plc_ip
            plc.Open()
            is_connected = True
            logger.info("PLC connection re-established.")
        except Exception as e:
            logger.error("Failed to re-establish PLC connection: {}".format(str(e)))
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
        success = batch_write_with_retry(write_operations)
        end_time = time.time()
        execution_time = end_time - start_time

        if not success:
            logger.warning("Failed to write data to PLC.")
            return jsonify({"message": "Failed to write data to PLC.", "time": execution_time}), 500

        logger.info("All data written successfully in {:.2f} seconds.".format(execution_time))
        return jsonify({"message": "Data written successfully.", "time": execution_time}), 200

    except Exception as e:
        logger.error("Error in insert_data_to_plc: {}".format(str(e)))
        return jsonify({"message": "Error writing data to PLC.", "error": str(e)}), 500

# Endpoint to read data from PLC
@app.route('/readDataFromPlc', methods=['POST'])  # Change method to POST
@cross_origin()
def read_data_from_plc():
    try:
        # Ensure PLC connection is active
        if not ensure_plc_connection():
            return jsonify({"message": "Unable to connect to PLC.", "error": "PLC connection failed"}), 500

        # Get JSON payload from the request body
        payload = request.json
        if not payload or 'tags' not in payload:
            return jsonify({"message": "No tags provided in the payload.", "error": None}), 400

        tags_to_read = payload['tags']

        # Measure time before reading starts
        start_time = time.time()

        # Perform read operations sequentially
        results = batch_read(tags_to_read)

        # Measure time after all read operations complete
        end_time = time.time()
        time_taken = end_time - start_time
        logger.info("Time taken to read from PLC: {:.4f} seconds".format(time_taken))

        if results is None:
            raise Exception("Error occurred during reading from PLC.")

        return jsonify({"message": "Data read from PLC successfully.", "data": results, "error": None}), 200
    except Exception as e:
        logger.error("Error in read_data_from_plc: {}".format(str(e)))
        return jsonify({"message": "Error occurred while reading data from PLC.", "error": str(e)}), 500
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
    except Exception as e:
        logger.error("Error closing PLC connection: {}".format(str(e)))
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
        logger.error("Error during ping: {}".format(str(e)))
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
        logger.error("Error during Wi-Fi ping: {}".format(str(e)))
        return jsonify({"message": "Error during Wi-Fi ping.", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8083)