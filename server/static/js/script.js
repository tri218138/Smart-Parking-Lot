function updateSensorData() {
    fetch('/sensor_data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('temperature').textContent = data.temperature;
            document.getElementById('humidity').textContent = data.humidity;
            document.getElementById('wind').textContent = data.wind;
        });
}
setInterval(updateSensorData, 2000); // Call updateSensorData every 5 seconds