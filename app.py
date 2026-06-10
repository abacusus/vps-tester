from flask import Flask, jsonify, render_template_string
import psutil
import time
import math
import os
import tempfile

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>VPS Efficiency Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {
            font-family: Arial;
            margin: 40px;
        }
        .card {
            border: 1px solid #ccc;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
        }
        h1 {
            color: #333;
        }
    </style>
</head>
<body>
    <h1>VPS Efficiency Dashboard</h1>

    <div class="card">
        <h3>CPU Usage</h3>
        <p>{{ data['cpu_usage'] }}%</p>
    </div>

    <div class="card">
        <h3>RAM Usage</h3>
        <p>{{ data['ram_percent'] }}%
           ({{ data['ram_used'] }} GB / {{ data['ram_total'] }} GB)</p>
    </div>

    <div class="card">
        <h3>Disk Usage</h3>
        <p>{{ data['disk_percent'] }}%
           ({{ data['disk_used'] }} GB / {{ data['disk_total'] }} GB)</p>
    </div>

    <div class="card">
        <h3>CPU Benchmark</h3>
        <p>{{ data['cpu_benchmark'] }} seconds</p>
    </div>

    <div class="card">
        <h3>Disk Speed</h3>
        <p>Write: {{ data['write_speed'] }} MB/s</p>
        <p>Read: {{ data['read_speed'] }} MB/s</p>
    </div>

    <div class="card">
        <h2>Efficiency Score: {{ data['score'] }}/100</h2>
        <h3>{{ data['rating'] }}</h3>
    </div>

</body>
</html>
"""


def cpu_benchmark():
    start = time.time()

    for num in range(2, 30000):
        is_prime = True

        for i in range(2, int(math.sqrt(num)) + 1):
            if num % i == 0:
                is_prime = False
                break

    return round(time.time() - start, 2)


def disk_benchmark(size_mb=50):
    filename = tempfile.mktemp()

    data = os.urandom(1024 * 1024)

    start = time.time()
    with open(filename, "wb") as f:
        for _ in range(size_mb):
            f.write(data)

    write_time = time.time() - start

    start = time.time()
    with open(filename, "rb") as f:
        while f.read(1024 * 1024):
            pass

    read_time = time.time() - start

    os.remove(filename)

    return (
        round(size_mb / write_time, 2),
        round(size_mb / read_time, 2)
    )


def calculate_score(cpu_bench, ram_percent, disk_percent):
    score = 100

    if cpu_bench > 5:
        score -= 20

    if ram_percent > 80:
        score -= 20

    if disk_percent > 80:
        score -= 20

    return max(score, 0)


@app.route("/")
def dashboard():
    cpu_usage = psutil.cpu_percent(interval=1)

    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    cpu_time = cpu_benchmark()
    write_speed, read_speed = disk_benchmark()

    score = calculate_score(
        cpu_time,
        ram.percent,
        disk.percent
    )

    if score >= 90:
        rating = "Excellent "
    elif score >= 75:
        rating = "Good "
    elif score >= 50:
        rating = "Average "
    else:
        rating = "Poor "

    data = {
        "cpu_usage": cpu_usage,
        "ram_percent": ram.percent,
        "ram_used": round(ram.used / (1024 ** 3), 2),
        "ram_total": round(ram.total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "disk_used": round(disk.used / (1024 ** 3), 2),
        "disk_total": round(disk.total / (1024 ** 3), 2),
        "cpu_benchmark": cpu_time,
        "write_speed": write_speed,
        "read_speed": read_speed,
        "score": score,
        "rating": rating,
    }

    return render_template_string(HTML, data=data)


@app.route("/api")
def api():
    return jsonify({
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent
    })


if __name__ == "__main__":
    app.run()