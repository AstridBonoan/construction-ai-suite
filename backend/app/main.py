from flask import Flask
from flask_cors import CORS
from routes.project_delay import project_delay_bp  # <- matches blueprint name

app = Flask(__name__)
# Enable CORS so the frontend (running on a different origin/port) can call the API
CORS(app, resources={r"/*": {"origins": "*"}})
app.register_blueprint(project_delay_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
