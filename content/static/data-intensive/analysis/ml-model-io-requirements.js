const FLOPS_PER_SAMPLE = {
    "cosmoflow":  247.0 * 1024**3,
    "deepcam":   2887.0 * 1024**3,
    "resnet50":    31.0 * 1024**3,
};
const SAMPLE_SIZE_BYTES = {
    "cosmoflow":   16.0 * 1024**2,
    "deepcam":     27.0 * 1024**2,
    "resnet50":    0.14 * 1024**2,
};
const GPU_FLOPS = {
    "v100":  130.0 * 1000**4,
    "a100":  312.0 * 1000**4, // fp16
    "h100": 3958.0 * 1000**4, // fp8
    "8x-v100": 8 *  130.0 * 1000**4,
    "8x-a100": 8 * 312.0 * 1000**4, // fp16
    "8x-h100": 8 * 3958.0 * 1000**4, // fp8
    // from https://ieeexplore.ieee.org/document/9652793
    "v100-cosmoflow-lo": 35.0 * 1000**4,
    "v100-cosmoflow-hi": 50.0 * 1000**4,
};

function humanReadableBytes(qty, base=2) {
    const units = base === 2 ? ["bytes", "KiB", "MiB", "GiB", "TiB"] : ["bytes", "KB", "MB", "GB", "TB"];
    const divisor = base === 2 ? 1024 : 1000;

    let unit = 0;
    while (qty > divisor && unit < units.length - 1) {
        qty /= divisor;
        unit++;
    }
    return [qty, units[unit]];
}

function calculate() {
    const model = document.querySelector("#model").value;
    const gpu = document.querySelector("#gpu").value;
    const base = parseInt(document.querySelector("#base").value);
    const flopsPerSample = FLOPS_PER_SAMPLE[model];
    const sampleSizeBytes = SAMPLE_SIZE_BYTES[model];
    const gpuFlops = GPU_FLOPS[gpu];
    const ioThroughput = gpuFlops / flopsPerSample * sampleSizeBytes;
    const [qty, unit] = humanReadableBytes(ioThroughput, base);
    document.querySelector("#output").textContent = `I/O Throughput: ${qty.toFixed(2)} ${unit}/s`;
}

// Create options for the model dropdown
const modelDropdown = document.querySelector("#model");
for (const model of Object.keys(FLOPS_PER_SAMPLE)) {
    const option = document.createElement("option");
    option.value = model;
    option.textContent = model;
    modelDropdown.appendChild(option);
}
modelDropdown.onchange = calculate;

// Create options for the GPU dropdown
const gpuDropdown = document.querySelector("#gpu");
for (const gpu of Object.keys(GPU_FLOPS)) {
    const option = document.createElement("option");
    option.value = gpu;
    option.textContent = gpu;
    gpuDropdown.appendChild(option);
}
gpuDropdown.onchange = calculate;

const baseDropdown = document.querySelector("#base");
baseDropdown.onchange = calculate;