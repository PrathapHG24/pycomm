from pycomm.ab_comm.clx import Driver as ClxDriver
from time import sleep
from flask import Flask, request
from flask_cors import CORS, cross_origin
import json

app = Flask(__name__)
CORS(app)

c = ClxDriver()
is_connected = False

@app.route('/insertDataToPlc', methods=['POST'])
@cross_origin()
def insert_data_to_plc():
    global is_connected

    try:
        if not is_connected:
            c.open('10.60.85.21')
            print("Connection to PLC established.")
            is_connected = True

        c.forward_open()

        data_list = request.json

        for item in data_list:
            for key, value in item.items():
                print("Writing to PLC: Key:", type(key), "Value:", type(value))
                if isinstance(value, long):
                    # Clamp the value to fit within the range of DINT
                    clamped_value = max(min(value, 2147483647), -2147483648)
                    c.write_tag(key.encode('utf-8'), clamped_value, 'DINT')
                    print("Value written to PLC for key:", key)
                else:
                    print("Unsupported value type. Skipping...")

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
