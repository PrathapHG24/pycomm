from pylogix import PLC
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)

# IP Address of the PLC
plc_ip = '192.168.12.5'

# List of tags to read
tags_to_read = [f't{i}' for i in range(1, 1000)]  # Assuming t1, t2, ..., t1000

def batch_write(plc_ip, batch):
    try:
        with PLC() as plc:
            plc.IPAddress = plc_ip
            for key, value in batch:
                plc.Write(key, str(value))
                print(f"Data written to PLC successfully for key: {key}")
    except Exception as e:
        print(f"Error during batch write: {e}")

def read_tag(plc_ip, tag):
    try:
        with PLC() as plc:
            plc.IPAddress = plc_ip
            value = plc.Read(tag).Value
            print(f"Data read from PLC for tag {tag}: {value}")
            return tag, value
    except Exception as e:
        print(f"Error reading tag {tag}: {e}")
        return tag, None

def batch_read(plc_ip, tags, max_workers=50):
    try:
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(read_tag, plc_ip, tag) for tag in tags]
            for future in as_completed(futures):
                tag, value = future.result()
                if value is not None:
                    results[tag] = value
        return results
    except Exception as e:
        print(f"Error during batch read: {e}")
        return None

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
        batch_size = 10
        with ThreadPoolExecutor(max_workers=20) as executor:
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

@app.route('/readDataFromPlc', methods=['GET'])
@cross_origin()
def read_data_from_plc():
    try:
        # Measure time before reading starts
        start_time = time.time()

        # Perform read operations with increased number of threads
        results = batch_read(plc_ip, tags_to_read, max_workers=50)

        # Measure time after all read operations complete
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to read from PLC: {time_taken:.4f} seconds")

        if results is None:
            raise Exception("Error occurred during reading from PLC.")

        return jsonify({"message": "Data read from PLC successfully.", "data": results, "error": None}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "Error occurred while reading data from PLC.", "error": str(e)}), 500
 
if __name__ == '__main__':
    app.run(debug=True,port=8083)