function updateSensorData() {
    fetch("/data/sensor")
        .then((response) => response.json())
        .then((data) => {
            document.getElementById("temperature").textContent = data.temperature;
            document.getElementById("humidity").textContent = data.humidity;
            document.getElementById("wind").textContent = data.wind;
            document.getElementById("pump").textContent = data.pump;
        });
}

function updateVehicleParkedData() {
    fetch("/data/vehicle_park")
        .then((response) => response.json())
        .then((data) => {
            var tableBody = document.getElementById("vehicle-park-body");
            tableBody.innerHTML = "";
            data.reverse();
            // Loop over the data and populate the table rows
            data.forEach(function (item) {
                var row = document.createElement("tr");
                var keyCell = document.createElement("td");
                var idCell = document.createElement("td");
                var posCell = document.createElement("td");
                var timeCell = document.createElement("td");

                // Set the cell values
                keyCell.textContent = item.key;
                idCell.textContent = item.id;
                posCell.textContent = item.pos;
                timeCell.textContent = item.time;

                // Append the cells to the row
                row.appendChild(keyCell);
                row.appendChild(idCell);
                row.appendChild(posCell);
                row.appendChild(timeCell);

                // Append the row to the table body
                tableBody.appendChild(row);
            });
        });
}
function updateRangesData() {
    fetch("/data/ranges")
        .then((response) => response.json())
        .then((data) => {
            var tableBody = document.getElementById("range-state-body");
            tableBody.innerHTML = "";
            // Loop over the data and populate the table rows
            data.forEach(function (item) {
                var row = document.createElement("tr");
                var idCell = document.createElement("td");
                var emptyCell = document.createElement("td");

                // Set the cell values
                idCell.textContent = item.id;
                emptyCell.textContent = item.empty ? "còn trống" : "đã đầy";

                if (emptyCell.textContent === "còn trống") {
                    emptyCell.style.backgroundColor = "rgb(88, 222, 88)"; //green
                } else {
                    emptyCell.style.backgroundColor = "rgb(243, 135, 135)"; //red
                }

                // Append the cells to the row
                row.appendChild(idCell);
                row.appendChild(emptyCell);

                // Append the row to the table body
                tableBody.appendChild(row);
            });
        });
}

setInterval(updateVehicleParkedData, 2000);
setInterval(updateSensorData, 2000);
setInterval(updateRangesData, 2000);

function preprocessInput() {
    // Get the input element
    var inputElement = document.getElementById("inputVehicleId");

    // Get the input value and remove leading/trailing spaces and tabs
    var inputValue = inputElement.value.trim();

    // Update the input value
    inputElement.value = inputValue;
}
