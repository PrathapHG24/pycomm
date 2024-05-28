from pycomm.ab_comm.clx import Driver as ClxDriver
import logging
from time import sleep
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import json

app = Flask(__name__)
CORS(app)

# Create a ClxDriver instance
c = ClxDriver()
is_connected = False  # Flag to track connection status

@app.route('/insertDataToPlc', methods=['POST'])
@cross_origin()
def insert_data_to_plc():
    global is_connected  # Access the global flag

    try:
        if not is_connected:  # Check if connection needs to be established
            c.open('10.60.85.21')  # Open connection to the PLC (only once)
            print("Connection to PLC established.")
            is_connected = True

        c.forward_open()  # Initialize the session

        # Get the JSON data from the request
        data_list = request.json

        # Iterate through the data and process it
        for item in data_list:
            for key, value in item.items():
                print("Writing to PLC: Key:", type(key), "Value:", type(value))
                if isinstance(value, (int, float)):
                    value_type = 'REAL' if isinstance(value, float) else 'INT'
                    c.write_tag(key.encode('utf-8'), value, value_type)
                    print("Read tag value is", c.read_tag(key.encode('utf-8')))
                else:
                    key = key.encode('utf-8')
                    value = value.encode('utf-8')
                    try:
                        c.write_string(key, value)
                        print("Read String Value is", c.read_string(key))
                        print("Data written to PLC successfully for key:", key.decode('utf-8'))
                    except Exception as e:
                        print("Error writing string:", key.decode('utf-8'), ":", e)
                sleep(1)

        return "Data written to PLC successfully.", 200
    except Exception as e:
        print("Error:", e)
        return "Error occurred while writing data to PLC.", 500
    finally:
        if is_connected:
            c.close()
            is_connected = False
            print("Connection to PLC closed.")

@app.route('/closeConnection', methods=['GET'])
def close_connection():
    global is_connected
    if is_connected:
        c.close()
        is_connected = False
        print("Connection to PLC closed.")
    return "Connection to PLC closed successfully.", 200

if __name__ == '__main__':
    app.run(debug=True, port=8083)
