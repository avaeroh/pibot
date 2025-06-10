log_buffer = []

def log(message):
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    log_buffer.append(entry)
    if len(log_buffer) > 50:
        log_buffer.pop(0)

def setup_logging(app):
    from flask import jsonify

    @app.route('/logs')
    def get_logs():
        return jsonify(log_buffer)
