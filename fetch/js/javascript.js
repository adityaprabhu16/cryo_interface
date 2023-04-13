function start() {
    fetch('/api/start', {
        method: 'POST'
    }).then(res=> res.json())
    .then(data => alert(data))
    .catch(err => {
        console.log(err);
    });
}

function stop() {
    fetch('/api/stop', {
        method: 'POST'
    }).then(res => res.json())
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
            alert("Successfully Connected!");
        }
        res.json()
    })
    .then(data =>{
        alert(data);
    })
    .catch(err => { 
        console.log("Failed to connect to USB device.");
    });
}

function connectVNA1() {
    const port = document.getElementById("vna1IP").value;
    const json = JSON.stringify(port);
    console.log(json)
    fetch('/api/connect_vna1', {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            "length": json.length.toString()
        },
        method: "POST",
        body: json
    })
    .then(res => res.json())
    .then(data =>{
        alert(data);
    })
    .catch(err => { 
        console.log("Failed to connect to VNA.");
    });
}

function connectVNA2() {
    const port = document.getElementById("vna2IP").value;
    const json = JSON.stringify(port);
    console.log(json)
    fetch('/api/connect_vna2', {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            "length": json.length.toString()
        },
        method: "POST",
        body: json
    })
    .then(res => res.json())
    .then(data =>{
        alert(data);
    })
    .catch(err => { 
        console.log("Failed to connect to VNA.");
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
        
        mdT1 = document.getElementById("metadata-temp1");
        mdT1.textContent = data.temp1;
        if(!document.getElementById("temp1").disabled && mdT1.textContent.length == 0){
            mdT1.textContent = "x";
        }
        // document.getElementById("metadata-temp1").textContent = data.temp1;
        mdT2 = document.getElementById("metadata-temp2");
        mdT2.textContent = data.temp2;
        if(!document.getElementById("temp2").disabled && mdT2.textContent.length == 0){
            mdT2.textContent = "x";
        }
        // document.getElementById("metadata-temp2").textContent = data.temp2;
        mdV1 = document.getElementById("metadata-vna1");
        mdV1.textContent = data.vna1;
        if(!document.getElementById("vna1").disabled && mdV1.textContent.length == 0){
            mdV1.textContent = "x";
        }
        // document.getElementById("metadata-vna1").textContent = data.vna1;
        mdV2 = document.getElementById("metadata-vna2");
        mdV2.textContent = data.vna2;
        if(!document.getElementById("vna2").disabled && mdV2.textContent.length == 0){
            mdV2.textContent = "x";
        }
        // document.getElementById("metadata-vna2").textContent = data.vna2;


    })
    .catch(err => console.log(err));
}

function loadPorts() {
    fetch('/api/devices')
    .then(res => res.json())
    .then(data => {
        const selector = document.querySelector("select");
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
        document.getElementById("datarate").value = data.period;
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

function ExpFrmHandler(event){
    event.preventDefault();
    // capture the form data
    const formData = new FormData(event.target);
    console.log(formData.entries());
    // convert the form data to JSON format
    const jsonObj = Object.fromEntries(formData.entries());
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

function vna1IPEventHandler(event){
    event.preventDefault();
    // capture the form data
    const formData = new FormData(event.target);
    console.log(formData.entries());
    // convert the form data to JSON format
    const jsonObj = Object.fromEntries(formData.entries());
    console.log(jsonObj);
    const jsonData = JSON.stringify(jsonObj);

    fetch('/api/connect_vna1', {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                "length": jsonData.length.toString()
            },
            method: "POST",
            body: jsonData
        })
        .then(res => {
            if (res.status == 200) {
                alert("Connection successful.");
            } else {
                console.log("Failed to connect to VNA.");
            }
        })
        .catch(err => { 
            console.log("Failed to connect to VNA.");
        });
}



function displayData(){
    var evtSource = new EventSource("api/stream_data");
    evtSource.addEventListener('temperature', (event) => {
        const data = JSON.parse(event.data);
        
        // Create a Date object using the timestamp.
        const t = new Date(data.time * 1000);

        Plotly.extendTraces('temp_plot', {x: [[t]], y: [[data.temp1]]}, [0]);
        Plotly.extendTraces('temp_plot', {x: [[t]], y: [[data.temp2]]}, [1]);
    });
}

function cfgRate(){
    var cfgJSON = {
        "period": getPeriodSeconds()
        // "period": document.getElementById("datarate").valueAsNumber,
    }   
    console.log(cfgJSON);
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
        console.log(data);
        // TODO: use values we got back to update the UI
    })
    .catch(err =>{
        alert("Failed to congifure data rate");
    });
}

function getPeriodSeconds(){
    var mins = document.getElementById("mins").valueAsNumber;
    var sec = document.getElementById("datarate").valueAsNumber;
    return (mins*60)+sec;
}

function init(){
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
        document.getElementById('temp1').disabled = !this.checked;
    };

    document.getElementById('temp2Checkbox').onchange = function() {
        document.getElementById('temp2').disabled = !this.checked;
    };

    document.getElementById('vna1Checkbox').onchange = function() {
        document.getElementById('vna1').disabled = !this.checked;
    };

    document.getElementById('vna2Checkbox').onchange = function() {
        document.getElementById('vna2').disabled = !this.checked;
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
            "width": 600,
            "height": 400,
            "title": "Temperature (Celsius)"},
        "type": "line"
    });

    loadMetadata();
    loadPorts();
    loadConfig();

    displayData();

    selectScreen();
}

document.addEventListener("DOMContentLoaded", init);
