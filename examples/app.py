from pycomm.ab_comm.clx import Driver as ClxDriver
import logging
from time import sleep
from flask import Flask, request

app = Flask(__name__)

# Create a ClxDriver instance
c = ClxDriver()

@app.route('/insertDataToPlc', methods=['POST'])
def insert_data_to_plc():
    try:
        if not c.is_connected():  # Check if the connection is already open
            c.open('10.60.85.21')  # Open connection to the PLC
            print("Connection to PLC established.")

        c.forward_open()  # Initialize the session

        # Get the JSON data from the request
        data_list = request.json
        
        # Now iterate through the processed data and process it as before
        for item in data_list:
            for key, value in item.items():
                print("Writing to PLC: Key:", type(key), "Value:", type(value))
                if isinstance(value, (int, float)):
                    value_type = 'REAL' if isinstance(value, float) else 'INT'
                    c.write_tag(key.encode('utf-8'), value, value_type)
                else:
                    print("Value is",value)
                    key = key.encode('utf-8')
                    value = value.encode('utf-8')
                    print(c.write_string(key, value))
                    print("Read from PLC:", c.read_string(key))  # Optionally read the written string value
                sleep(1)

        return "Data written to PLC successfully.", 200
    except Exception as e:
        print("Error:", e)
        return "Error occurred while writing data to PLC.", 500

@app.route('/closeConnection', methods=['GET'])
def close_connection():
    c.close()
    return "Connection to PLC closed successfully.", 200

if __name__ == '__main__':
    app.run(debug=True, port=8083)