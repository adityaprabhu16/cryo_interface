
function start() {
    fetch('/api/start', {
        method: 'POST'
    }).then(res=>{
        if(res.status == 200){
            const state = document.getElementById("dataStatus");
            state.innerHTML = "Running";
            state.style.border = '2px solid green';
        }
        return res.json();
    })
    .then(data => alert(data))
    .catch(err => {
        console.log(err);
    });
}

function stop() {
    fetch('/api/stop', {
        method: 'POST'
    }).then(res =>{
        if(res.status == 200){
            const state = document.getElementById("dataStatus");
            state.innerHTML = "Stopped";
            state.style.border = '2px solid red';
        }
        return res.json();
    })
    .then(data => alert(data))
    .catch(err => {
        console.log(err);
    });
}

function connect() {
    const port = document.getElementById("port").value;
    const json = JSON.stringify(port);
    fetch('/api/connect', {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            "length": json.length.toString()
        },
        method: "POST",
        body: json
    })
    .then(res => {
        if(res.status == 200){
            const state = document.getElementById("tempStatus");
            state.innerHTML = "Connected";
            state.style.border = '2px solid green';
        }
        return res.json();
    })
    .then(data => {
        alert(data);
    })
    .catch(err => { 
        console.log(err);
        console.log("Failed to connect to USB device.");
    });
}

function connectVNA1() {
    const port = document.getElementById("vna1IP").value;
    const json = JSON.stringify(port);
    fetch('/api/connect_vna1', {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            "length": json.length.toString()
        },
        method: "POST",
        body: json
    })
    .then(res => {
        if(res.status == 200){
            const state = document.getElementById("vna1status");
            state.innerHTML = "Connected";
            state.style.border = '2px solid green';
            // alert("Successfully Connected");
        } else {
            const state = document.getElementById("vna1status");
            state.innerHTML = "Not Connected";
            state.style.border = '2px solid red';
        }
        return res.json();
    })
    .then(data => {
        // checkStatus();
        alert(data);
    })
    .catch(err => { 
        console.log("Failed to connect to VNA.");
        console.log(err);
    });
}

function connectVNA2() {
    const port = document.getElementById("vna2IP").value;
    const json = JSON.stringify(port);
    fetch('/api/connect_vna2', {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            "length": json.length.toString()
        },
        method: "POST",
        body: json
    })
    .then(res => {
        if(res.status == 200){
            const state = document.getElementById("vna2status");
            state.innerHTML = "Connected";
            state.style.border = '2px solid green';
            // alert("Successfully Connected");
        } else {
            const state = document.getElementById("vna2status");
            state.innerHTML = "Not Connected";
            state.style.border = '2px solid red';
        }
        return res.json();
    })
    .then(data => {
        // checkStatus();
        alert(data);
    })
    .catch(err => { 
        console.log("Failed to connect to VNA.");
        console.log(err);
    });
}

function loadMetadata() {
    fetch('/api/metadata')
    .then(res => res.json())
    .then(data => {
        document.getElementById("metadata-title").textContent = data.title;
        document.getElementById("metadata-name").textContent = data.name;
        document.getElementById("metadata-cpa").textContent = data.cpa;
        document.getElementById("metadata-date").textContent = data.date;

        document.getElementById("metadata-temp1").textContent = data.temp1 === null ? "[Not Selected]" : data.temp1;
        document.getElementById("metadata-temp2").textContent = data.temp2 === null ? "[Not Selected]" : data.temp2;
        document.getElementById("metadata-vna1").textContent = data.vna1 === null ? "[Not Selected]" : data.vna1;
        document.getElementById("metadata-vna2").textContent = data.vna2 === null ? "[Not Selected]" : data.vna2;
        document.getElementById("metadata-vna1_temp").textContent = data.vna1_temp === null ? "[Not Selected]" : data.vna1_temp;
        document.getElementById("metadata-vna2_temp").textContent = data.vna2_temp === null ? "[Not Selected]" : data.vna2_temp;
    })
    .catch(err => console.log(err));
}

function loadPorts() {
    fetch('/api/devices')
    .then(res => res.json())
    .then(data => {
        const selector = document.getElementById("port");
        const items = selector.length;
        for (var i = items-1; i >= 0; i--) {
            selector.remove(i);
        }
        for (const x of data) {
            const op = new Option(x, x);
            selector.add(op, undefined);
        }
    })
    .catch(err => console.log(err));
}

function refresh() {
    loadPorts();
}

function loadConfig() {
    fetch('/api/config')
    .then(res => res.json())
    .then(data => {
        const seconds = data.period % 60;
        const minutes = Math.floor(data.period / 60);
        document.getElementById('mins').value = minutes;
        document.getElementById('datarate').value = seconds;
    })
    .catch(err => console.log(err));
}

function selectScreen() {
    loadMetadata();

    fetch('/api/experiment_selected')
    .then(res => res.json())
    .then(selected => {
        if (selected) {
            var el = document.getElementById("new_experiment");
            el.style.display = "none";
            el = document.getElementById("dashboard");
            el.style.display = "block";
        } else {
            var el = document.getElementById("new_experiment");
            el.style.display = "block";
            el = document.getElementById("dashboard");
            el.style.display = "none";
        }
    });
}

function ExpFrmHandler(event) {
    event.preventDefault();
    // capture the form data
    const formData = new FormData(event.target);
    // convert the form data to JSON format
    var jsonObj = Object.fromEntries(formData.entries());
    // We want these as null, not empty string.
    if (jsonObj.vna1_temp === "") {
        jsonObj.vna1_temp = null;
    }
    if (jsonObj.vna2_temp === "") {
        jsonObj.vna2_temp = null;
    }

    console.log(jsonObj);
    const jsonData = JSON.stringify(jsonObj);

    fetch('/api/create_experiment', {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                "length": jsonData.length.toString()
            },
            method: "POST",
            body: jsonData
        })
        .then(res => {
            selectScreen();
        })
        .catch(err => { 
            console.log("Failed to create experiment");
        });
}

// function vna1IPEventHandler(event) {
//     event.preventDefault();
//     // capture the form data
//     const formData = new FormData(event.target);
//     console.log(formData.entries());
//     // convert the form data to JSON format
//     const jsonObj = Object.fromEntries(formData.entries());
//     const jsonData = JSON.stringify(jsonObj);

//     fetch('/api/connect_vna1', {
//             headers: {
//                 'Accept': 'application/json',
//                 'Content-Type': 'application/json',
//                 "length": jsonData.length.toString()
//             },
//             method: "POST",
//             body: jsonData
//         })
//         .then(res => {
//             if (res.status == 200) {
//                 alert("Connection successful.");
//             } else {
//                 console.log("Failed to connect to VNA.");
//             }
//         })
//         .catch(err => { 
//             console.log("Failed to connect to VNA.");
//         });
// }

function displayData() {
    var evtSource = new EventSource("api/stream_data");
    evtSource.addEventListener('temperature', (event) => {
        const data = JSON.parse(event.data);
        
        // Create a Date object using the timestamp.
        const t = new Date(data.time * 1000);

        Plotly.extendTraces('temp_plot', {x: [[t]], y: [[data.temp1]]}, [0]);
        Plotly.extendTraces('temp_plot', {x: [[t]], y: [[data.temp2]]}, [1]);
    });
}

function cfgRate() {
    var cfgJSON = {
        "period": getPeriodSeconds(),
    };
    fetch('/api/config', {
        method:'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'length': JSON.stringify(cfgJSON).length.toString(),
        },
        body: JSON.stringify(cfgJSON),
    })
    .then(res => res.json())
    .then(data => {
        const seconds = data.period % 60;
        const minutes = Math.floor(data.period / 60);
        document.getElementById('mins').value = minutes;
        document.getElementById('datarate').value = seconds;
        alert("Configuration updated.");
    })
    .catch(err =>{
        console.log(err);
        alert("Failed to update configuration.");
    });
}

function getPeriodSeconds() {
    const mins = document.getElementById("mins").valueAsNumber;
    const sec = document.getElementById("datarate").valueAsNumber;
    return (mins*60)+sec;
}

var prev_data = null;

function checkStatus() {
    fetch('/api/devices_connected')
    .then(res =>{
        return res.json();
    })
    .then(data =>{
        if (data.temperature) {
            const state = document.getElementById("tempStatus");
            state.innerHTML = "Connected";
            state.style.border = '2px solid green';
        } else {
            const state = document.getElementById("tempStatus");
            state.innerHTML = "Not Connected";
            state.style.border = '2px solid red';
            if (prev_data?.temperature) {
                alert("Temperature sensor has disconnected.");
            }
        }

        if (data.vna1) {
            const state = document.getElementById("vna1status");
            state.innerHTML = "Connected";
            state.style.border = '2px solid green';
        } else {
            const state = document.getElementById("vna1status");
            state.innerHTML = "Not Connected";
            state.style.border = '2px solid red';
            if (prev_data?.vna1) {
                alert("VNA1 has disconnected.");
            }
        }

        if (data.vna2) {
            const state = document.getElementById("vna2status");
            state.innerHTML = "Connected";
            state.style.border = '2px solid green';
        } else {
            const state = document.getElementById("vna2status");
            state.innerHTML = "Not Connected";
            state.style.border = '2px solid red';
            if (prev_data?.vna2) {
                alert("VNA2 has disconnected.");
            }
        }

        prev_data = data;
    });

    fetch('/api/running')
    .then(res => res.json())
    .then(data => {
        if (data) {
            const state = document.getElementById("dataStatus");
            state.innerHTML = "Running";
            state.style.border = '2px solid green';
        } else {
            const state = document.getElementById("dataStatus");
            state.innerHTML = "Stopped";
            state.style.border = '2px solid red';
        }
    })
    .catch(err => console.log(err));
}

function init() {
    document.getElementById('date').valueAsDate = new Date();

    // var experiment_selected = false;
    var formExp = document.getElementById("create_experiment");
    formExp.addEventListener("submit", ExpFrmHandler);

    document.getElementById("startup").addEventListener("click", start);
    document.getElementById("stop").addEventListener("click", stop);
    document.getElementById("connect").addEventListener("click", connect);
    document.getElementById("connectVNA1").addEventListener("click", connectVNA1);
    document.getElementById("connectVNA2").addEventListener("click", connectVNA2);
    document.getElementById("cfgRate").addEventListener("click", cfgRate);
    document.getElementById("refresh").addEventListener("click", refresh);

    document.getElementById('temp1Checkbox').onchange = function() {
        var t1box = document.getElementById('temp1');
        t1box.disabled = !this.checked;
        //TODO: the following code adds an option to a drop down menu
        var vna1opt1 = document.getElementById("vna1opt1");
        var vna2opt1 = document.getElementById("vna2opt1");
        var vna1select = document.getElementById("vna1_temp");
        var vna2select = document.getElementById("vna2_temp");
        if(t1box.disabled){
            vna1opt1.style.display = "none";
            vna2opt1.style.display = "none";
            if(vna1select.value == "temp1"){
                vna1select.value = null;
            }
            if(vna2select.value == "temp1"){
                vna2select.value = null;
            }
        }
        else{
            vna1opt1.style.display = "block";
            vna2opt1.style.display = "block";
        }
        
    };

    document.getElementById('temp2Checkbox').onchange = function() {
        var t2box = document.getElementById('temp2');
        t2box.disabled = !this.checked;
        var vna1opt2 = document.getElementById("vna1opt2");
        var vna2opt2 = document.getElementById("vna2opt2");
        var vna1select = document.getElementById("vna1_temp");
        var vna2select = document.getElementById("vna2_temp");
        if(t2box.disabled){
            vna1opt2.style.display = "none";
            vna2opt2.style.display = "none";
            if(vna1select.value == "temp2"){
                vna1select.value = null;
            }
            if(vna2select.value == "temp2"){
                vna2select.value = null;
            }
        }
        else{
            vna1opt2.style.display = "block";
            vna2opt2.style.display = "block";
        }
    };

    document.getElementById('vna1Checkbox').onchange = function() {
        var v1box = document.getElementById('vna1');
        v1box.disabled = !this.checked;
        var v1select = document.getElementById("vna1_temp");
        if(v1box.disabled){
            v1select.style.display = "none";
            if(v1select.hasAttribute("required")){
                v1select.removeAttribute("required");
            }
        }
        else{
            v1select.setAttribute("required", true);
            v1select.style.display = "block";
        }
    };

    document.getElementById('vna2Checkbox').onchange = function() {
        var v2box = document.getElementById('vna2')
        v2box.disabled = !this.checked;
        var v2select = document.getElementById("vna2_temp");
        if(v2box.disabled){
            v2select.style.display = "none";
            if(v2select.hasAttribute("required")){
                v2select.removeAttribute("required");
            }
        }
        else{
            v2select.setAttribute("required", true);
            v2select.style.display = "block";
        }
    };

    var tempPlot = Plotly.newPlot("temp_plot", {
        "data": [{
            "x": [],
            "y": [],
            "name": "Temp 1",
        }, {
            "x": [],
            "y": [],
            "name": "Temp 2",
        }],
        "layout": {
            "width": 800,
            "height": 500,
            "xaxis": {
                "title": {
                    "text": "Time",
                },
            },
            "yaxis": {
                "title": {
                    "text": "Temperature (Celcius)",
                },
            },
            "title": "Temperature vs Time"},
        "type": "line"
    });

    loadMetadata();
    loadPorts();
    loadConfig();

    displayData();

    selectScreen();

    checkStatus();

    setInterval(checkStatus, 10000);
}

document.addEventListener("DOMContentLoaded", init);
