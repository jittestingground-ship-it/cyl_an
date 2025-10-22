import sqlite3
import h5py
import random
import os

DB_PATH = "autoproto_data/OrderData.db"
EXT_PATH = "autoproto_data"

def generate(order_id):
    h5_path = os.path.join(EXT_PATH, f"{order_id}_test.h5")
    with h5py.File(h5_path, "w") as f:
        grp_data = f.create_group("data")
        times = [i*0.5 for i in range(141)]
        pres_a = [random.uniform(30, 70) for _ in times]
        pres_b = [random.uniform(28, 68) for _ in times]
        grp_data.create_dataset("pressure_a", data=pres_a)
        grp_data.create_dataset("pressure_b", data=pres_b)
        grp_data.create_dataset("timestamp", data=times)
        grp_meta = f.create_group("metadata")
        grp_meta.attrs["order_id"] = order_id
        grp_meta.attrs["set_pressure"] = 70.0
        grp_meta.attrs["avg_pressure_a"] = sum(pres_a)/len(pres_a)
        grp_meta.attrs["avg_pressure_b"] = sum(pres_b)/len(pres_b)
        grp_meta.attrs["max_leak_pressure"] = max(abs(a-b) for a,b in zip(pres_a,pres_b))
        grp_meta.attrs["cycle_count"] = 3
        grp_meta.attrs["test_time"] = 70.5
        grp_meta.attrs["samples"] = len(times)
        grp_meta.attrs["test_pass_fail"] = 1
        grp_meta.attrs["saved_at"] = "2025-10-08T15:30:22"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO orders (orderID, name, email, phone, address) VALUES (?, ?, ?, ?, ?)",
              (order_id, "Kane Industries", "kane@jitindustries.com", "555-1234", "123 Main St"))
    c.execute("INSERT INTO testing_files (order_id, file_path) VALUES (?, ?)", (order_id, h5_path))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    generate("J1002251127")
    generate("J1002251128")
    