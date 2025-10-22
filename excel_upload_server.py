from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Set the path to your external hard drive
EXTERNAL_DRIVE_PATH = "/mnt/external_drive/excel_data"

os.makedirs(EXTERNAL_DRIVE_PATH, exist_ok=True)

@app.route("/upload_excel", methods=["POST"])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        save_path = os.path.join(EXTERNAL_DRIVE_PATH, file.filename)
        file.save(save_path)
        return jsonify({"message": f"File saved to {save_path}"}), 200
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    