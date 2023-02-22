let timeToUpdate = 60000*30; //every 30 minutes

window.addEventListener("DOMContentLoaded", loadedHandler);
window.setInterval({

}, );

function loadedHandler() {
  //Render Charts:
  const thermocoupleTop = document.getElementById('thermocoupleTop');
  const thermocoupleBot = document.getElementById('thermocoupleBot');
  const rfTop = document.getElementById('rfsensorTop');
  const rfBot = document.getElementById('rfsensorBot');


  new Chart(thermocoupleTop, {
    type: 'line',
    data: {
      labels: ['9:00AM', '9:30AM', '10:00AM', '10:30AM', '11:00AM', '11:30AM'],
      datasets: [{
        label: 'Top Thermocouple',
        data: [12, 19, 3, 5, 2, 3],
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });

  new Chart(thermocoupleBot, {
    type: 'line',
    data: {
      labels: ['9:00AM', '9:30AM', '10:00AM', '10:30AM', '11:00AM', '11:30AM'],
      datasets: [{
        label: 'Bottom Thermocouple',
        data: [12, 19, 3, 5, 2, 3],
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });

  new Chart(rfTop, {
    type: 'line',
    data: {
      labels: ['9:00AM', '9:30AM', '10:00AM', '10:30AM', '11:00AM', '11:30AM'],
      datasets: [{
        label: 'Top RF Sensor',
        data: [12, 19, 3, 5, 2, 3],
        borderWidth: 1,
        pointBackgroundColor: 'red',
        borderColor: 'red'
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });

  new Chart(rfBot, {
    type: 'line',
    data: {
      labels: ['9:00AM', '9:30AM', '10:00AM', '10:30AM', '11:00AM', '11:30AM'],
      datasets: [{
        label: 'Bottom RF Sensor',
        data: [12, 19, 3, 5, 2, 3],
        borderWidth: 1,
        pointBackgroundColor: 'red',
        borderColor: 'red'
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });

}