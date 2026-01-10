var tableColumns = [
    { key: "model", label: "System", align: "left" },
    { key: "processor", label: "Processor", align: "left" },
    { key: "cores_and_clock", label: "Clock", align: "right", html: true },
    { key: "wall_secs", label: "Time (sec)", align: "right" },
    { key: "memreorder_secs", label: "Optimized Time (sec)", align: "right" }
];

function isNumber(value) {
    return typeof value === "number" && !isNaN(value);
}

function formatValue(value) {
    if (value === null || value === undefined || value === "") {
        return "";
    }
    if (isNumber(value)) {
        return value.toString();
    }
    return String(value);
}

function buildTable(rows) {
    var table = document.createElement("table");
    table.className = "table table-sm table-striped table-bordered table-responsive-md";

    var thead = document.createElement("thead");
    var headRow = document.createElement("tr");
    tableColumns.forEach(function(col) {
        var th = document.createElement("th");
        th.textContent = col.label;
        if (col.align) {
            th.style.textAlign = col.align;
        }
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = document.createElement("tbody");
    rows.forEach(function(row) {
        var tr = document.createElement("tr");
        tableColumns.forEach(function(col) {
            var td = document.createElement("td");
            var value = formatValue(row[col.key]);
            if (col.html) {
                td.innerHTML = value;
            } else {
                td.textContent = value;
            }
            if (col.align) {
                td.style.textAlign = col.align;
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    return table;
}

function renderTables(datasets) {
    var containers = document.querySelectorAll(".benchmark-table");
    containers.forEach(function(container) {
        var isa = container.getAttribute("data-isa");
        if (!isa || !datasets[isa]) {
            return;
        }
        var table = buildTable(datasets[isa]);
        container.innerHTML = "";
        container.appendChild(table);
    });
}

function loadTables() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var datasets = JSON.parse(this.responseText);
            renderTables(datasets);
        }
    };
    xhttp.open("GET", "benchmark-tables.json", true);
    xhttp.send();
}

loadTables();
