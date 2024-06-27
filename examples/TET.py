from pycomm.ab_comm.clx import Driver as ClxDriver
from pylogix import PLC
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import time
import json

app = Flask(__name__)
CORS(app)

# Create instances for both libraries
clx_driver = ClxDriver()
pylogix_plc = PLC()
clx_is_connected = False  # Flag to track connection status for pycomm
pylogix_is_connected = False  # Flag to track connection status for pylogix

@app.route('/insertDataToPlc', methods=['POST'])
@cross_origin()
def insert_data_to_plc():
    global clx_is_connected  # Access the global flag

    try:
        if not clx_is_connected:  # Check if connection needs to be established
            if not clx_driver.open('192.168.12.5'):  # Open connection to the PLC
                raise Exception("Unable to open connection to PLC.")
            if not clx_driver.register_session():  # Register the session
                raise Exception("Unable to register session with PLC.")
            if not clx_driver.forward_open():  # Initialize the session
                raise Exception("Unable to forward open with PLC.")
            print("Connection to PLC established (pycomm).")
            clx_is_connected = True

        # Get the JSON data from the request
        data_list = request.json

        # Collect all the write operations
        write_operations = []
        for item in data_list:
            for key, value in item.items():
                # Convert value to string regardless of its type
                str_value = str(value)
                key = key.encode('utf-8')
                str_value = str_value.encode('utf-8')
                write_operations.append((key, str_value))

        # Measure time before writing starts
        start_time = time.time()

        # Perform all write operations
        for key, str_value in write_operations:
            try:
                clx_driver.write_string(key, str_value)
                print("Data written to PLC successfully for key: {key}".format(key=key.decode('utf-8')))
            except Exception as e:
                print("Error writing string: {key}: {error}".format(key=key.decode('utf-8'), error=e))

        # Measure time after all write operations complete
        end_time = time.time()
        time_taken = end_time - start_time
        print("Time taken to write to PLC: {:.4f} seconds".format(time_taken))

        return jsonify({"message": "Data written to PLC successfully.", "error": None}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Error occurred while writing data to PLC.", "error": str(e)}), 500
    finally:
        if clx_is_connected:
            clx_driver.close()
            clx_is_connected = False
            print("Connection to PLC closed (pycomm).")

@app.route('/closeConnection', methods=['GET'])
def close_connection():
    global clx_is_connected, pylogix_is_connected
    if clx_is_connected:
        clx_driver.close()
        clx_is_connected = False
        print("Connection to PLC closed (pycomm).")
    if pylogix_is_connected:
        pylogix_plc.Close()
        pylogix_is_connected = False
        print("Connection to PLC closed (pylogix).")
    return jsonify({"message": "Connections to PLC closed successfully.", "error": None}), 200

@app.route('/readDataTagsFromPlc', methods=['GET'])
@cross_origin()
def read_data_tags_from_plc():
    global pylogix_is_connected  # Access the global flag

    try:
        if not pylogix_is_connected:  # Check if connection needs to be established
            pylogix_plc.IPAddress = '192.168.12.5'  # Set PLC IP address
            pylogix_is_connected = True
            print("Connection to PLC established (pylogix).")

        # Read all available tags from the PLC
        tags_response = pylogix_plc.GetTagList()
        if tags_response is None or tags_response.Value is None:
            raise Exception("Failed to get tag list from PLC.")

        tag_names = [tag.TagName for tag in tags_response.Value]

        data = {}
        for tag in tags_response.Value:
            try:
                response = pylogix_plc.Read(tag.TagName)
                if response.Status == 'Success':
                    data[tag.TagName] = response.Value
                    print("Read from PLC: Key: {}, Value: {}".format(tag.TagName, response.Value))
                else:
                    print("Failed to read tag: {}, Status: {}".format(tag.TagName, response.Status))
            except Exception as e:
                print("Error reading value: {}: {}".format(tag.TagName, e))

        return jsonify({"tags": tag_names, "data": data}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Error occurred while reading data from PLC.", "error": str(e)}), 500
    finally:
        if pylogix_is_connected:
            pylogix_plc.Close()
            pylogix_is_connected = False
            print("Connection to PLC closed (pylogix).")

if __name__ == '__main__':
    app.run(debug=True, port=8083)
