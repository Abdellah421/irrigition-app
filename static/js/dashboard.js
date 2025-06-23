// This file will contain the dashboard-specific JavaScript logic.
document.addEventListener('DOMContentLoaded', () => {
  // Check if we are on the dashboard page and run the init function
  if (document.getElementById('chartHum')) {
    // Parse the data from the script tag
    const flaskDataElement = document.getElementById('flask-data');
    const flaskData = JSON.parse(flaskDataElement.textContent);
    initializeDashboard(flaskData);
  }
});

function initializeDashboard(flaskData) {
  // --- DOM Elements ---
  const esp32Temp = document.getElementById('esp32-temp');
  const esp32Hum = document.getElementById('esp32-hum');
  const esp32Sol = document.getElementById('esp32-sol');
  const esp32LastUpdate = document.getElementById('esp32-last-update');
  const esp32StatusText = document.getElementById('esp32-status-text');
  const esp32StatusIcon = document.getElementById('esp32-status');
  const latestImageElem = document.getElementById('latest-plant-image');
  const noImageText = document.getElementById('no-image-text');
  const voiceCommandBtn = document.getElementById('voice-command-btn');
  const voiceFeedback = document.getElementById('voice-feedback');
  const startIrrigationBtn = document.getElementById('start-irrigation-btn');
  const stopIrrigationBtn = document.getElementById('stop-irrigation-btn');

  // --- Socket.IO Connection ---
  const socket = io();

  socket.on('connect', () => {
    console.log('Connected to server via WebSocket');
    showNotification(flaskData.translations.connected || 'تم الاتصال في الوقت الحقيقي');
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from server');
    showNotification(flaskData.translations.disconnected || 'تم قطع الاتصال بالخادم', true);
  });

  socket.on('sensor_update', (data) => {
    console.log('Received sensor update:', data);
    updateSensorDisplay(data);
    updateChart(data);
  });

  socket.on('esp32_status', (data) => {
    console.log('Received ESP32 status:', data);
    updateESP32Status(data.status);
  });
  
  socket.on('irrigation_command', (data) => {
    console.log('Received irrigation command:', data);
    showNotification(data.message);
  });

  socket.on('new_image', (data) => {
    console.log('New image uploaded:', data);
    showNotification(flaskData.translations.new_image_notification || 'تم استلام صورة جديدة');
    updateLatestImage();
  });
  
  socket.on('current_data', (data) => {
    console.log('Received current data:', data);
    updateSensorDisplay(data);
  });

  // --- Functions ---
  function updateSensorDisplay(data) {
    if (data.temperature !== undefined) esp32Temp.textContent = data.temperature || '-';
    if (data.humidite !== undefined) esp32Hum.textContent = data.humidite || '-';
    if (data.sol !== undefined) esp32Sol.textContent = data.sol || '-';
    if (data.last_update) esp32LastUpdate.textContent = data.last_update;
  }

  function updateESP32Status(status) {
    if (status === 'online') {
      esp32StatusText.textContent = flaskData.translations.connected || 'متصل';
      esp32StatusIcon.style.color = '#43a047';
    } else {
      esp32StatusText.textContent = flaskData.translations.disconnected || 'غير متصل';
      esp32StatusIcon.style.color = '#f44336';
    }
  }

  // --- Chart.js ---
  const ctx = document.getElementById('chartHum').getContext('2d');
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: flaskData.chartLabels,
      datasets: [{
        label: flaskData.humidityLabel,
        data: [], // Start with empty data
        fill: true,
        borderColor: '#43a047',
        backgroundColor: 'rgba(76,175,80,0.10)',
        tension: 0.4,
        pointBackgroundColor: '#43a047',
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: false } }
    }
  });

  function updateChart(data) {
    if (data.humidite && chart) {
      const newHumidity = parseFloat(data.humidite);
      if (!isNaN(newHumidity)) {
        chart.data.labels.push(new Date().toLocaleTimeString());
        chart.data.datasets[0].data.push(newHumidity);
        if (chart.data.labels.length > 15) {
          chart.data.labels.shift();
          chart.data.datasets[0].data.shift();
        }
        chart.update('none');
      }
    }
  }

  // --- Image Handling ---
  function updateLatestImage() {
    fetch('/get_latest_image')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success' && data.latest_image_url) {
          latestImageElem.src = data.latest_image_url;
          latestImageElem.style.display = 'block';
          noImageText.style.display = 'none';
        } else {
          latestImageElem.style.display = 'none';
          noImageText.style.display = 'block';
        }
      })
      .catch(error => console.error('Error fetching latest image:', error));
  }
  
  // --- Manual & Voice Control ---
  function sendIrrigationCommand(command) {
      fetch('/voice-command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: command })
      })
      .then(res => res.json())
      .then(data => showNotification(data.message))
      .catch(err => console.error('Error sending command:', err));
  }

  startIrrigationBtn.addEventListener('click', () => sendIrrigationCommand('start irrigation'));
  stopIrrigationBtn.addEventListener('click', () => sendIrrigationCommand('stop irrigation'));

  // --- Initial Load ---
  updateLatestImage();
} 