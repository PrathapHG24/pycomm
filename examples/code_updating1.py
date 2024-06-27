from pylogix import PLC
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)

# IP Address of the PLC
plc_ip = '192.168.12.5'

def convert_to_string(value):
    # Convert value to string based on its type
    if isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        return str(value)
    elif isinstance(value, bool):
        return '1' if value else '0'
    elif isinstance(value, str):
        return value  # No conversion needed for string
    else:
        raise ValueError(f"Unsupported data type: {type(value)}")

def batch_write(plc_ip, batch):
    try:
        with PLC() as plc:
            plc.IPAddress = plc_ip
            for key, value in batch:
                plc.Write(key, convert_to_string(value))
                print(f"Data written to PLC successfully for key: {key}")
    except Exception as e:
        print(f"Error during batch write: {e}")

@app.route('/insertDataToPlc', methods=['POST'])
@cross_origin()
def insert_data_to_plc():
    try:
        # Get the JSON data from the request
        data_list = request.json

        # Prepare write operations
        write_operations = []
        for item in data_list:
            for key, value in item.items():
                write_operations.append((key, value))

        # Measure time before writing starts
        start_time = time.time()

        # Perform write operations using multithreading
        batch_size = 50  # Number of tags to write in each batch
        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(0, len(write_operations), batch_size):
                batch = write_operations[i:i + batch_size]
                futures.append(executor.submit(batch_write, plc_ip, batch))
            
            for future in as_completed(futures):
                future.result()

        # Measure time after all write operations complete
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to write to PLC: {time_taken:.4f} seconds")

        if time_taken > 2:
            raise Exception("Writing to PLC took longer than 2 seconds.")

        return jsonify({"message": "Data written to PLC successfully.", "error": None}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "Error occurred while writing data to PLC.", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8083)
