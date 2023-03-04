let timeToUpdate = 60000*30; //every 30 minutes

// window.addEventListener("DOMContentLoaded", loadGraphs);
var gnum;

function start()
{
  const form = document.getElementById("setup");
  const dropDown = document.getElementById("graphNum");

  dropDown.addEventListener("change", function(){
    gnum = dropDown.value;
    console.log(gnum);
  });

  form.addEventListener("submit", loadGraphs());

  form.addEventListener("submit", function(){
    const graphs = document.getElementById("container");
    graphs.style.display = "flex";
    form.style.display = "none";
    gnum = parseInt(document.getElementById("graphNum").value);
  });

  form.addEventListener("submit", function(){
    fetch('/api/metadata', {
      method: 'post',
      body: JSON.stringify({
        'random': 0,
        'junk': 1,
        'data': 2,
      }),
    }).catch((error) => {
      console.log(error);
    });
  });

  var select = document.getElementById("graphNum");

  // TODO: load available options here
  var options = ['a', 'b', 'c', 'd'];

  for (var i = 0; i < options.length; i++) {
    var opt = document.createElement("option");
    opt.value = i;
    opt.textContent = options[i];
    select.appendChild(opt);
  }

} // end function start

// on the window load event,call the start function
window.addEventListener( "load", start, false );






//provides an error
// window.setInterval({

// }, );

function loadGraphs() {
  // const gnum = parseInt(document.getElementById("graphNum").value);
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

  // if(gnum > 2){
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
  // }
  
  // if(gnum > 3){
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
  // }
  
  

}

