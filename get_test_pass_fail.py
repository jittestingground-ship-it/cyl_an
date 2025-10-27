import h5py
import numpy as np
import os

def get_test_pass_fail(order_id, data_dir="/home/kw/cyl_a/test_data"):
    # Find the latest HDF5 file for the order
    files = [f for f in os.listdir(data_dir) if f.startswith(order_id) and f.endswith('.h5')]
    if not files:
        return None
    # Sort by timestamp in filename (assuming format: <order_id>_<timestamp>.h5)
    files.sort(reverse=True)
    file_path = os.path.join(data_dir, files[0])
    with h5py.File(file_path, "r") as f:
        meta = f["metadata"]
        if "test_pass_fail" in meta:
            value = meta["test_pass_fail"][()]
            # Decode if bytes
            if isinstance(value, bytes):
                value = value.decode()
            return value
    return None

# Example usage:
if __name__ == "__main__":
    order_id = "J1023251233"
    result = get_test_pass_fail(order_id)
    print(f"Test Pass/Fail for {order_id}: {result}")
