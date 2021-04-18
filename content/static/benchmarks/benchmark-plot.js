var xhttp = new XMLHttpRequest();
var dataset;

xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        datasets = JSON.parse(this.responseText);

        var layout = {
            title: {
                text: "Benchmark Walltimes"
            },
            font: {
                family: "Roboto, Helvetica Neue, Helvetica, Arial, sans-serif",
                size: 14
            },
            showlegend: true,
            legend: {
                x: 1,
                y: 0.5,
                xanchor: 'right'
            },
            xaxis: {
                type: "log",
                autorange: true,
                title: {
                    text: "Walltime (secs)"
                }
            },
            yaxis: {
                tickfont: {
                }
            },
            margin: {
                l: 275,
                t: 30,
                b: 45
            },
            barmode: "overlay",
            bargap: 0.0,
            paper_bgcolor: "#FFFFFF00",
            plot_bgcolor: "#FFFFFF00"
        };

        Plotly.newPlot(
            document.getElementById('barchart'),
            {
                data: datasets,
                layout: layout,
                config: { responsive: true }
            }
        );
    }
};

xhttp.open("GET", "benchmark-results.json", true);
xhttp.send();
