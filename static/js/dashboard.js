// API endpoints
const API_ENDPOINTS = {
    commodities: '/api/commodities',
    weather: '/api/weather',
    energy: '/api/energy',
    params: '/api/params'
};

// Asset mappings by data source
const ASSETS_BY_SOURCE = {
    fmp: [
        { symbol: 'GC', name: 'Gold' },
        { symbol: 'CL', name: 'Crude Oil' },
        { symbol: 'NG', name: 'Natural Gas' },
        { symbol: 'SI', name: 'Silver' },
        { symbol: 'PL', name: 'Platinum' }
    ],
    commodity_price_api: [
        { symbol: 'wheat', name: 'Wheat' },
        { symbol: 'corn', name: 'Corn' },
        { symbol: 'soybean', name: 'Soybean' },
        { symbol: 'coffee', name: 'Coffee' },
        { symbol: 'sugar', name: 'Sugar' }
    ],
    api_ninjas: [
        { symbol: 'copper', name: 'Copper' },
        { symbol: 'aluminum', name: 'Aluminum' },
        { symbol: 'zinc', name: 'Zinc' },
        { symbol: 'nickel', name: 'Nickel' },
        { symbol: 'lead', name: 'Lead' }
    ]
};

// Chart configurations
const chartConfigs = {
    commodities: {
        layout: {
            title: 'Commodity Prices',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Price' },
            showlegend: true,
            legend: { orientation: 'h', y: -0.2 }
        },
        config: {
            responsive: true,
            displayModeBar: true
        }
    },
    weather: {
        layout: {
            title: 'Weather Data',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Temperature (°C)' },
            showlegend: true
        },
        config: {
            responsive: true,
            displayModeBar: true
        }
    },
    energy: {
        layout: {
            title: 'Energy Market Prices',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Price (€/MWh)' },
            showlegend: true
        },
        config: {
            responsive: true,
            displayModeBar: true
        }
    }
};

// Utility functions
function getTimeRangeDates(range) {
    const end = new Date();
    const start = new Date();
    
    switch(range) {
        case '1d':
            start.setDate(end.getDate() - 1);
            break;
        case '1w':
            start.setDate(end.getDate() - 7);
            break;
        case '1m':
            start.setMonth(end.getMonth() - 1);
            break;
        case '3m':
            start.setMonth(end.getMonth() - 3);
            break;
        case '1y':
            start.setFullYear(end.getFullYear() - 1);
            break;
        default:
            start.setDate(end.getDate() - 7);
    }
    
    return {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0],
        interval: range
    };
}

// Fetch data from API (backend Django endpoints)
async function fetchData(endpoint, params = {}) {
    try {
        const queryString = new URLSearchParams(params).toString();
        const url = `${endpoint}?${queryString}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        return null;
    }
}

// Update asset dropdown based on selected data source
async function updateAssetDropdown() {
    const assetSelect = document.getElementById('asset-select');
    const dataSource = document.getElementById('data-source').value;
    
    // Clear existing options except the first one
    while (assetSelect.options.length > 1) {
        assetSelect.remove(1);
    }
    
    // Get assets for selected source
    const assets = await fetchData(API_ENDPOINTS.params, { source: dataSource });
    
    // Add new options
    assets.forEach(asset => {
        const option = document.createElement('option');
        option.value = asset.symbol;
        option.textContent = asset.name;
        assetSelect.appendChild(option);
    });
    
    // Enable/disable the select based on whether we have options
    assetSelect.disabled = assets.length === 0;
    
    // If we have assets, trigger chart update
    if (assets.length > 0) {
        createAssetChart();
    }
}

async function createAssetChart() {
    const asset = document.getElementById('asset-select').value;
    const dataSource = document.getElementById('data-source').value;
    const timeRange = document.getElementById('commodity-time-range').value;
    console.log(timeRange);
    const oscillator = document.getElementById('oscillator-select').value;
    
    if (!asset || !dataSource) return;
    
    const { start, end } = getTimeRangeDates(timeRange);
    const endpoint = '/api/commodities';
    const params = { 
        name: asset, 
        start, 
        end, 
        source: dataSource, 
        oscillator 
    };
    
    try {
        const data = await fetchData(endpoint, params);
        if (!data) {
            console.error('No data received from API');
            return;
        }

        // Main price chart
        const traces = [{
            name: asset,
            x: data.dates,
            y: data.prices,
            type: 'scatter',
            mode: 'lines',
            line: { width: 2 },
            hovertemplate: '%{x}<br>Price: $%{y:.2f}<extra></extra>'
        }];

        const layout = {
            ...chartConfigs.commodities.layout,
            title: `${asset} Price Chart (${dataSource.toUpperCase()})`,
            height: 400,
            margin: { t: 50, b: 50, l: 50, r: 50 },
            xaxis: {
                ...chartConfigs.commodities.layout.xaxis,
                rangeslider: { visible: false },
                type: 'date'
            },
            yaxis: {
                ...chartConfigs.commodities.layout.yaxis,
                tickprefix: '$'
            }
        };

        Plotly.newPlot('commodity-chart', traces, layout, {
            ...chartConfigs.commodities.config,
            scrollZoom: true
        });

        // Oscillator chart
        const oscillatorChartDiv = document.getElementById('oscillator-chart');
        if (oscillator !== 'none' && data.oscillator && Array.isArray(data.oscillator.values)) {
            const oscTrace = {
                name: oscillator.toUpperCase(),
                x: data.oscillator.dates,
                y: data.oscillator.values,
                type: 'scatter',
                mode: 'lines',
                line: { width: 2, color: getOscillatorColor(oscillator) },
                hovertemplate: '%{x}<br>%{y:.2f}<extra></extra>'
            };

            const oscLayout = {
                title: `${oscillator.toUpperCase()} Oscillator`,
                height: 200,
                margin: { t: 30, b: 30, l: 50, r: 50 },
                xaxis: {
                    type: 'date',
                    rangeslider: { visible: false }
                },
                yaxis: {
                    title: oscillator.toUpperCase(),
                    ...getOscillatorYAxisConfig(oscillator)
                }
            };

            Plotly.newPlot(oscillatorChartDiv, [oscTrace], oscLayout, {
                ...chartConfigs.commodities.config,
                scrollZoom: true
            });
        } else {
            Plotly.purge(oscillatorChartDiv);
        }
    } catch (error) {
        console.error('Error creating asset chart:', error);
    }
}

function getOscillatorColor(oscillator) {
    const colors = {
        kama: '#FF6B6B',
        price_osc: '#4ECDC4',
        cci_enhanced: '#45B7D1',
        momentum: '#96CEB4',
        roc: '#FFEEAD',
        smi: '#DDA0DD',
        efficiency_ratio: '#98FB98'
    };
    return colors[oscillator] || '#FF6B6B';
}

function getOscillatorYAxisConfig(oscillator) {
    const configs = {
        kama: {
            tickprefix: '$'
        },
        price_osc: {
            tickprefix: '%',
            ticksuffix: ''
        },
        cci_enhanced: {
            tickprefix: ''
        },
        momentum: {
            tickprefix: '$'
        },
        roc: {
            tickprefix: '%',
            ticksuffix: ''
        },
        smi: {
            range: [-100, 100],
            tick0: -100,
            dtick: 50
        },
        efficiency_ratio: {
            range: [0, 1],
            tick0: 0,
            dtick: 0.2
        }
    };
    return configs[oscillator] || {};
}

// Create weather chart
async function createWeatherChart() {
    const city = document.getElementById('citySearch').value;
    if (!city) {
        alert('Please enter a city name');
        return;
    }
    try {
        const response = await fetchData(API_ENDPOINTS.weather, { city });
        if (!response || !response.data || response.data.length === 0) {
            throw new Error('No weather data available');
        }
        // Use only the first (current) data point
        const d = response.data[0];
        // Create temperature chart
        const tempData = [{
            x: [d.date],
            y: [d.temperature],
            type: 'bar',
            name: 'Temperature (°C)',
            marker: { color: '#ff7f0e' }
        }];
        const tempLayout = {
            title: `Current Temperature in ${response.city}`,
            xaxis: { title: 'Date' },
            yaxis: { title: 'Temperature (°C)' },
            showlegend: true,
            height: 400
        };
        Plotly.newPlot('weatherChart', tempData, tempLayout);
        // Create additional weather metrics chart
        const metricsData = [
            {
                x: [d.date],
                y: [d.humidity],
                type: 'bar',
                name: 'Humidity (%)',
                marker: { color: '#1f77b4' }
            },
            {
                x: [d.date],
                y: [d.pressure],
                type: 'bar',
                name: 'Pressure (hPa)',
                marker: { color: '#2ca02c' }
            },
            {
                x: [d.date],
                y: [d.wind_speed],
                type: 'bar',
                name: 'Wind Speed (m/s)',
                marker: { color: '#d62728' }
            }
        ];
        const metricsLayout = {
            title: `Current Weather Metrics in ${response.city}`,
            xaxis: { title: 'Date' },
            yaxis: { title: 'Value' },
            showlegend: true,
            height: 400
        };
        Plotly.newPlot('weatherMetricsChart', metricsData, metricsLayout);
    } catch (error) {
        console.error('Error fetching weather data:', error);
        alert('Error fetching weather data: ' + error.message);
    }
}

// document.getElementById('weather-search-btn').addEventListener('click', createWeatherChart);
// document.getElementById('weather-city').addEventListener('keypress', function(e) {
//     if (e.key === 'Enter') createWeatherChart();
// }
// );

// Create energy price chart
async function createEnergyChart() {
    const market = document.getElementById('energy-market').value;
    const timeRange = document.getElementById('energy-time-range').value;
    
    const { start, end } = getTimeRangeDates(timeRange);
    
    const data = await fetchData(API_ENDPOINTS.energy, {
        market,
        start,
        end
    });
    
    console.log('Energy data:', data);
    
    if (!data) return;

    const traces = [{
        name: 'Energy Price',
        x: data.dates,
        y: data.prices,
        type: 'scatter',
        mode: 'lines+markers'
    }];

    Plotly.newPlot('energy-chart', traces, chartConfigs.energy.layout, chartConfigs.energy.config);
}

// Update event listeners for the new logic
function setupEventListeners() {
    // Data source change handler
    document.getElementById('data-source').addEventListener('change', updateAssetDropdown);
    
    // Asset selection change handler
    document.getElementById('asset-select').addEventListener('change', createAssetChart);
    
    // Time range change handler
    document.getElementById('commodity-time-range').addEventListener('change', createAssetChart);
    
    // Oscillator change handler
    document.getElementById('oscillator-select').addEventListener('change', createAssetChart);
    
    // Weather controls
    // document.getElementById('weather-search-btn').addEventListener('click', createWeatherChart);
    // document.getElementById('weather-city').addEventListener('keypress', function(e) {
    //     if (e.key === 'Enter') createWeatherChart();
    // });
    
    // Energy controls
    document.getElementById('energy-market').addEventListener('change', createEnergyChart);
    document.getElementById('energy-time-range').addEventListener('change', createEnergyChart);
    
    // Tab change events
    document.querySelectorAll('a[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', (e) => {
            const target = e.target.getAttribute('href').substring(1);
            switch(target) {
                case 'commodities':
                    createAssetChart();
                    break;
                case 'weather':
                    createWeatherChart();
                    break;
                case 'energy':
                    createEnergyChart();
                    break;
            }
        });
    });
}

// Initialize all charts
function initializeCharts() {
    createAssetChart();
    createWeatherChart();
    createEnergyChart();
}

// Refresh data periodically
function startDataRefresh() {
    setInterval(() => {
        const activeTab = document.querySelector('.tab-pane.active');
        if (activeTab) {
            switch(activeTab.id) {
                case 'commodities':
                    createAssetChart();
                    break;
                case 'weather':
                    createWeatherChart();
                    break;
                case 'energy':
                    createEnergyChart();
                    break;
            }
        }
    }, 300000); // Refresh every 5 minutes
}

// Dark mode toggle logic
function setupDarkModeToggle() {
    const darkModeSwitch = document.getElementById('darkModeSwitch');
    // Load preference
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        darkModeSwitch.checked = true;
    }
    darkModeSwitch.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'enabled');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'disabled');
        }
    });
}

// On DOMContentLoaded, initialize everything
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    updateAssetDropdown(); // Initialize asset dropdown
    initializeCharts();
    startDataRefresh();
    setupDarkModeToggle();
}); 