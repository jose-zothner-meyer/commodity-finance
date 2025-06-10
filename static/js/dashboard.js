// API endpoints
const API_ENDPOINTS = {
    commodities: '/api/commodities',
    weather: '/api/weather',
    energy: '/api/energy',
    params: '/api/params',
    portfolio: {
        analyze: '/api/portfolio/analyze',
        simulate: '/api/portfolio/simulate',
        optimize: '/api/portfolio/optimize',
        sample: '/api/portfolio/sample'
    },
    eia: {
        electricity_generation: '/api/eia/electricity/generation/',
        electricity_prices: '/api/eia/electricity/prices/',
        natural_gas: '/api/eia/natural-gas/',
        renewable_energy: '/api/eia/renewable-energy/',
        petroleum: '/api/eia/petroleum/'
    },
    fred: {
        indicators: '/api/fred/economic-indicators/',
        series: '/api/fred/series/',
        multiple_series: '/api/fred/multiple-series/',
        search: '/api/fred/search/'
    }
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
    ],
    alpha_vantage: [
        // Energy Commodities
        { symbol: 'WTI', name: 'WTI Crude Oil' },
        { symbol: 'BRENT', name: 'Brent Crude Oil' },
        { symbol: 'NATURAL_GAS', name: 'Natural Gas' },
        { symbol: 'HEATING_OIL', name: 'Heating Oil' },
        { symbol: 'GASOLINE', name: 'Gasoline' },
        
        // Precious Metals
        { symbol: 'COPPER', name: 'Copper' },
        { symbol: 'ALUMINUM', name: 'Aluminum' },
        { symbol: 'ZINC', name: 'Zinc' },
        { symbol: 'NICKEL', name: 'Nickel' },
        { symbol: 'LEAD', name: 'Lead' },
        { symbol: 'TIN', name: 'Tin' },
        { symbol: 'GOLD', name: 'Gold' },
        { symbol: 'SILVER', name: 'Silver' },
        { symbol: 'PLATINUM', name: 'Platinum' },
        { symbol: 'PALLADIUM', name: 'Palladium' },
        
        // Agricultural Commodities
        { symbol: 'WHEAT', name: 'Wheat' },
        { symbol: 'CORN', name: 'Corn' },
        { symbol: 'COTTON', name: 'Cotton' },
        { symbol: 'SUGAR', name: 'Sugar' },
        { symbol: 'COFFEE', name: 'Coffee' },
        { symbol: 'COCOA', name: 'Cocoa' },
        { symbol: 'RICE', name: 'Rice' },
        { symbol: 'OATS', name: 'Oats' },
        { symbol: 'SOYBEANS', name: 'Soybeans' }
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
        
        const data = await response.json();
        
        if (!response.ok) {
            // Handle API errors with user-friendly messages
            if (data.error) {
                console.error('API Error:', data.error);
                showErrorMessage(data.error, endpoint);
            }
            throw new Error(`HTTP ${response.status}: ${data.error || 'Network response was not ok'}`);
        }
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        showErrorMessage(`Unable to fetch data: ${error.message}`, endpoint);
        return null;
    }
}

// Show error messages to user
function showErrorMessage(message, endpoint) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-warning alert-dismissible fade show';
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '80px';
    errorDiv.style.right = '20px';
    errorDiv.style.zIndex = '9999';
    errorDiv.style.maxWidth = '400px';
    
    let userMessage = message;
    if (endpoint.includes('energy')) {
        userMessage = 'Energy data is temporarily unavailable due to API authentication issues. Please try again later.';
    } else if (endpoint.includes('weather')) {
        userMessage = 'Weather data is temporarily unavailable. Please check your internet connection.';
    }
    
    errorDiv.innerHTML = `
        <strong>Notice:</strong> ${userMessage}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
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
    
    if (!assets || !Array.isArray(assets)) {
        console.error('Invalid assets response:', assets);
        assetSelect.disabled = true;
        return;
    }
    
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
    const oscillator = document.getElementById('oscillator-select').value;
    
    if (!asset || !dataSource) {
        return;
    }
    
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
        // Kaufman Oscillators
        kama: '#FF6B6B',
        price_osc: '#4ECDC4',
        cci_enhanced: '#45B7D1',
        momentum: '#96CEB4',
        roc: '#FFEEAD',
        smi: '#DDA0DD',
        efficiency_ratio: '#98FB98',
        // Ehlers DSP Oscillators
        fisher_transform: '#FF9500',
        stochastic_cg: '#9013FE',
        super_smoother: '#00E676',
        cycle_period: '#FF5722',
        mama: '#2196F3',
        sinewave: '#E91E63',
        hilbert_transform: '#795548'
    };
    return colors[oscillator] || '#FF6B6B';
}

function getOscillatorYAxisConfig(oscillator) {
    const configs = {
        // Kaufman Oscillators
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
        },
        // Ehlers DSP Oscillators
        fisher_transform: {
            range: [-3, 3],
            tick0: -3,
            dtick: 1,
            zeroline: true
        },
        stochastic_cg: {
            range: [-100, 100],
            tick0: -100,
            dtick: 50,
            zeroline: true
        },
        super_smoother: {
            tickprefix: '$'
        },
        cycle_period: {
            range: [10, 50],
            tick0: 10,
            dtick: 10,
            title: 'Cycle Period (bars)'
        },
        mama: {
            tickprefix: '$'
        },
        sinewave: {
            range: [-1, 1],
            tick0: -1,
            dtick: 0.5,
            zeroline: true
        },
        hilbert_transform: {
            range: [-1, 1],
            tick0: -1,
            dtick: 0.5,
            zeroline: true
        }
    };
    return configs[oscillator] || {};
}

// Create weather chart
async function createWeatherChart() {
    const city = document.getElementById('citySearch').value || 'London';
    
    // Show loading state
    const weatherChart = document.getElementById('weatherChart');
    const metricsChart = document.getElementById('weatherMetricsChart');
    
    weatherChart.innerHTML = '<div class="loading text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p>Loading weather data...</p></div>';
    metricsChart.innerHTML = '';
    
    try {
        const response = await fetchData(API_ENDPOINTS.weather, { city });
        if (!response || !response.data || response.data.length === 0) {
            weatherChart.innerHTML = '<div class="alert alert-info">No weather data available for this city. Please try a different city.</div>';
            return;
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
            title: `Weather Metrics for ${response.city}`,
            xaxis: { title: 'Date' },
            yaxis: { title: 'Value' },
            showlegend: true,
            height: 400
        };
        
        Plotly.newPlot('weatherMetricsChart', metricsData, metricsLayout);
        
    } catch (error) {
        console.error('Weather chart error:', error);
        weatherChart.innerHTML = '<div class="alert alert-danger">Failed to load weather data. Please try again later.</div>';
    }
}

// Create energy system chart for energy analysts
async function createEnergyChart() {
    const country = document.getElementById('energy-country').value;
    const dataType = document.getElementById('energy-data-type').value;
    const timeRange = document.getElementById('energy-time-range').value;
    
    const energyChart = document.getElementById('energy-chart');
    const sourceBadge = document.getElementById('energy-source-badge');
    
    // Clear previous content and show loading state
    energyChart.innerHTML = '';
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading text-center p-4';
    loadingDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Loading energy data...</p>';
    energyChart.appendChild(loadingDiv);
    
    // Calculate historical dates (APIs have publication delays)
    const end = new Date();
    end.setDate(end.getDate() - 2); // 2 days ago to ensure data availability
    const start = new Date(end);
    
    switch(timeRange) {
        case '1d':
            start.setDate(end.getDate() - 1);
            break;
        case '3d':
            start.setDate(end.getDate() - 3);
            break;
        case '1w':
            start.setDate(end.getDate() - 7);
            break;
        case '2w':
            start.setDate(end.getDate() - 14);
            break;
        default:
            start.setDate(end.getDate() - 7);
    }
    
    try {
        const data = await fetchData(API_ENDPOINTS.energy, {
            country,
            data_type: dataType,
            start: start.toISOString().split('T')[0],
            end: end.toISOString().split('T')[0]
        });
        
        console.log('Energy system data:', data);
        
        // Clear loading state
        energyChart.innerHTML = '';
        
        if (!data || !data.success) {
            energyChart.innerHTML = '<div class="alert alert-warning">Energy data is temporarily unavailable. Please try again later.</div>';
            return;
        }

        // Update source badge
        if (sourceBadge) {
            sourceBadge.textContent = data.api_source === 'entsoe' ? 'ENTSO-E' : 'Energy Charts';
            sourceBadge.className = `source-badge text-white ${data.api_source === 'entsoe' ? 'bg-info' : 'bg-success'}`;
        }

        // Handle different data types
        if (dataType === 'generation' && data.generation_by_source) {
            createGenerationMixChart(data, energyChart, country, start, end);
        } else if (dataType === 'renewable_share' && data.values) {
            createRenewableShareChart(data, energyChart, country, start, end);
        } else if (dataType === 'load' && data.values) {
            createLoadChart(data, energyChart, country, start, end);
        } else if (dataType === 'price' && data.values) {
            createPriceChart(data, energyChart, country, start, end);
        } else {
            energyChart.innerHTML = '<div class="alert alert-info">No data available for the selected parameters. Try different dates or data type.</div>';
        }
        
    } catch (error) {
        console.error('Energy chart error:', error);
        energyChart.innerHTML = '<div class="alert alert-danger">Failed to load energy data. Please try again later.</div>';
    }
}

// Specialized chart creation functions
function createPriceChart(data, container, country, start, end) {
    const traces = [{
        name: 'Electricity Price',
        x: data.dates,
        y: data.values,
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#007bff', width: 2 },
        marker: { color: '#007bff', size: 4 },
        hovertemplate: '%{x}<br>Price: €%{y:.2f}/MWh<extra></extra>'
    }];

    const layout = {
        title: `Electricity Prices - ${country} (${start.toISOString().split('T')[0]} to ${end.toISOString().split('T')[0]})`,
        xaxis: { title: 'Date & Time', type: 'date' },
        yaxis: { title: 'Price (€/MWh)' },
        showlegend: false,
        height: 500,
        margin: { t: 60, b: 60, l: 60, r: 40 }
    };

    Plotly.newPlot(container, traces, layout, { responsive: true, displayModeBar: true });
}

function createGenerationMixChart(data, container, country, start, end) {
    console.log('🔧 createGenerationMixChart called - Updated version 1.2');
    console.log('📊 Available energy sources:', Object.keys(data.generation_by_source || {}));
    
    const traces = [];
    const renewableSources = ['Solar', 'Wind onshore', 'Wind offshore', 'Biomass', 'Hydro Run-of-River', 'Hydro water reservoir'];
    const colors = {
        // Renewable sources
        'Solar': '#FFD700',                     // Gold
        'Wind onshore': '#87CEEB',              // Sky Blue
        'Wind offshore': '#4682B4',             // Steel Blue
        'Biomass': '#8FBC8F',                   // Dark Sea Green
        'Hydro Run-of-River': '#20B2AA',        // Light Sea Green
        'Hydro water reservoir': '#4169E1',     // Royal Blue
        'Geothermal': '#DC143C',                // Crimson
        'Waste': '#CD853F',                     // Peru
        
        // Fossil fuels
        'Fossil brown coal / lignite': '#8B4513',   // Saddle Brown
        'Fossil hard coal': '#2F4F4F',              // Dark Slate Gray
        'Fossil gas': '#FFA500',                     // Orange
        'Fossil oil': '#800080',                     // Purple
        'Fossil coal-derived gas': '#696969',       // Dim Gray
        
        // Storage and grid
        'Hydro pumped storage': '#9370DB',           // Medium Purple
        'Hydro pumped storage consumption': '#7B68EE', // Medium Slate Blue
        'Cross border electricity trading': '#20B2AA', // Light Sea Green
        
        // Others
        'Others': '#808080',                         // Gray
        'Load': '#FF4500',                          // Orange Red
        'Residual load': '#B22222',                 // Fire Brick
        'Renewable share of load': '#32CD32',       // Lime Green
        'Renewable share of generation': '#00FF00'   // Lime
    };

    for (const [source, values] of Object.entries(data.generation_by_source)) {
        if (values && values.length > 0) {
            const color = colors[source] || '#888888';
            console.log(`🎨 Energy source: "${source}" → Color: ${color}`);
            // Debug log for unmapped sources
            if (!colors[source]) {
                console.log(`Warning: No color mapping for energy source: "${source}"`);
            }
            traces.push({
                name: source,
                x: data.dates,
                y: values,
                type: 'scatter',
                mode: 'lines',
                stackgroup: 'one',
                line: { width: 0, color: color },
                fillcolor: color,
                hovertemplate: `${source}<br>%{x}<br>%{y:.0f} MW<extra></extra>`
            });
        }
    }

    const layout = {
        title: `Power Generation Mix - ${country} (${start.toISOString().split('T')[0]} to ${end.toISOString().split('T')[0]})`,
        xaxis: { title: 'Date & Time', type: 'date' },
        yaxis: { title: 'Generation (MW)' },
        showlegend: true,
        height: 500,
        margin: { t: 60, b: 60, l: 60, r: 120 },
        legend: { orientation: 'v', x: 1.02, y: 1 }
    };

    Plotly.newPlot(container, traces, layout, { responsive: true, displayModeBar: true });
}

function createRenewableShareChart(data, container, country, start, end) {
    const traces = [{
        name: 'Renewable Share',
        x: data.dates,
        y: data.values,
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#28a745', width: 3 },
        marker: { color: '#28a745', size: 4 },
        fill: 'tozeroy',
        fillcolor: 'rgba(40, 167, 69, 0.2)',
        hovertemplate: '%{x}<br>Renewable Share: %{y:.1f}%<extra></extra>'
    }];

    const layout = {
        title: `Renewable Energy Share - ${country} (${start.toISOString().split('T')[0]} to ${end.toISOString().split('T')[0]})`,
        xaxis: { title: 'Date & Time', type: 'date' },
        yaxis: { title: 'Renewable Share (%)', range: [0, 100] },
        showlegend: false,
        height: 500,
        margin: { t: 60, b: 60, l: 60, r: 40 }
    };

    Plotly.newPlot(container, traces, layout, { responsive: true, displayModeBar: true });
}

function createLoadChart(data, container, country, start, end) {
    const traces = [{
        name: 'Electricity Load',
        x: data.dates,
        y: data.values,
        type: 'scatter',
        mode: 'lines',
        line: { color: '#dc3545', width: 2 },
        hovertemplate: '%{x}<br>Load: %{y:.0f} MW<extra></extra>'
    }];

    const layout = {
        title: `Electricity Load - ${country} (${start.toISOString().split('T')[0]} to ${end.toISOString().split('T')[0]})`,
        xaxis: { title: 'Date & Time', type: 'date' },
        yaxis: { title: 'Load (MW)' },
        showlegend: false,
        height: 500,
        margin: { t: 60, b: 60, l: 60, r: 40 }
    };

    Plotly.newPlot(container, traces, layout, { responsive: true, displayModeBar: true });
}

// Create analytics dashboard with multiple charts
async function createAnalyticsDashboard() {
    const country = document.getElementById('analysis-country').value;
    const timeRange = document.getElementById('analysis-time-range').value;
    
    // Calculate dates
    const end = new Date();
    end.setDate(end.getDate() - 2);
    const start = new Date(end);
    
    switch(timeRange) {
        case '1d': start.setDate(end.getDate() - 1); break;
        case '3d': start.setDate(end.getDate() - 3); break;
        case '1w': start.setDate(end.getDate() - 7); break;
        case '2w': start.setDate(end.getDate() - 14); break;
        default: start.setDate(end.getDate() - 7);
    }

    const dateRange = {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0],
        country
    };

    // Load all data types in parallel
    const [priceData, loadData, generationData] = await Promise.all([
        fetchData(API_ENDPOINTS.energy, { ...dateRange, data_type: 'price' }),
        fetchData(API_ENDPOINTS.energy, { ...dateRange, data_type: 'load' }),
        fetchData(API_ENDPOINTS.energy, { ...dateRange, data_type: 'generation' })
    ]);

    // Create individual charts
    if (priceData && priceData.success) {
        createPriceChart(priceData, document.getElementById('analytics-price-chart'), country, start, end);
    }
    
    if (loadData && loadData.success) {
        createLoadChart(loadData, document.getElementById('analytics-load-chart'), country, start, end);
    }
    
    if (generationData && generationData.success) {
        createGenerationMixChart(generationData, document.getElementById('analytics-generation-chart'), country, start, end);
    }
}

// Create renewables dashboard
async function createRenewablesDashboard() {
    const country = document.getElementById('renewables-country').value;
    const timeRange = document.getElementById('renewables-time-range').value;
    
    // Calculate dates
    const end = new Date();
    end.setDate(end.getDate() - 2);
    const start = new Date(end);
    
    switch(timeRange) {
        case '1d': start.setDate(end.getDate() - 1); break;
        case '3d': start.setDate(end.getDate() - 3); break;
        case '1w': start.setDate(end.getDate() - 7); break;
        case '2w': start.setDate(end.getDate() - 14); break;
        default: start.setDate(end.getDate() - 7);
    }

    const dateRange = {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0],
        country
    };

    // Load renewable data
    const [renewableShareData, generationData] = await Promise.all([
        fetchData(API_ENDPOINTS.energy, { ...dateRange, data_type: 'renewable_share' }),
        fetchData(API_ENDPOINTS.energy, { ...dateRange, data_type: 'generation' })
    ]);

    // Create renewable share chart
    if (renewableShareData && renewableShareData.success) {
        createRenewableShareChart(renewableShareData, document.getElementById('renewables-share-chart'), country, start, end);
    }

    // Create renewable vs fossil chart
    if (generationData && generationData.success && generationData.renewable_total && generationData.fossil_total) {
        const traces = [
            {
                name: 'Renewable',
                x: generationData.dates,
                y: generationData.renewable_total,
                type: 'scatter',
                mode: 'lines',
                stackgroup: 'one',
                fillcolor: '#28a745',
                line: { color: '#28a745', width: 2 },
                hovertemplate: 'Renewable<br>%{x}<br>%{y:.0f} MW<extra></extra>'
            },
            {
                name: 'Fossil',
                x: generationData.dates,
                y: generationData.fossil_total,
                type: 'scatter',
                mode: 'lines',
                stackgroup: 'one',
                fillcolor: '#dc3545',
                line: { color: '#dc3545', width: 2 },
                hovertemplate: 'Fossil<br>%{x}<br>%{y:.0f} MW<extra></extra>'
            }
        ];

        const layout = {
            title: `Renewable vs Fossil Generation - ${country}`,
            xaxis: { title: 'Date & Time', type: 'date' },
            yaxis: { title: 'Generation (MW)' },
            showlegend: true,
            height: 400,
            margin: { t: 60, b: 60, l: 60, r: 60 }
        };

        Plotly.newPlot('renewables-vs-fossil-chart', traces, layout, { responsive: true, displayModeBar: true });
    }

    // Create renewable sources breakdown
    if (generationData && generationData.success && generationData.generation_by_source) {
        const renewableSources = ['Solar', 'Wind onshore', 'Wind offshore', 'Biomass', 'Hydro Run-of-River', 'Hydro water reservoir'];
        const traces = [];
        const colors = {
            'Solar': '#FFD700',           // Gold
            'Wind onshore': '#87CEEB',    // Sky Blue
            'Wind offshore': '#4682B4',   // Steel Blue
            'Biomass': '#8FBC8F',         // Dark Sea Green
            'Hydro Run-of-River': '#20B2AA', // Light Sea Green
            'Hydro water reservoir': '#4169E1', // Royal Blue
            'Geothermal': '#DC143C',      // Crimson
            'Other Renewable': '#32CD32'  // Lime Green
        };

        for (const source of renewableSources) {
            if (generationData.generation_by_source[source]) {
                const color = colors[source];
                traces.push({
                    name: source,
                    x: generationData.dates,
                    y: generationData.generation_by_source[source],
                    type: 'scatter',
                    mode: 'lines',
                    stackgroup: 'one',
                    line: { width: 0, color: color },
                    fillcolor: color,
                    hovertemplate: `${source}<br>%{x}<br>%{y:.0f} MW<extra></extra>`
                });
            }
        }

        const layout = {
            title: `Renewable Generation Sources - ${country}`,
            xaxis: { title: 'Date & Time', type: 'date' },
            yaxis: { title: 'Generation (MW)' },
            showlegend: true,
            height: 400,
            margin: { t: 60, b: 60, l: 60, r: 120 },
            legend: { orientation: 'v', x: 1.02, y: 1 }
        };

        Plotly.newPlot('renewables-sources-chart', traces, layout, { responsive: true, displayModeBar: true });
    }
}

// Helper functions for energy analyst dashboard
function getDataTypeName(dataType) {
    const names = {
        'load': 'Electricity Load',
        'generation': 'Generation',
        'flow': 'Cross-border Flow'
    };
    return names[dataType] || dataType;
}

function getDataTypeColor(dataType) {
    const colors = {
        'load': '#007bff',
        'generation': '#28a745',
        'flow': '#dc3545'
    };
    return colors[dataType] || '#007bff';
}

function getGenerationTypeName(genType) {
    const names = {
        'B01': 'Biomass',
        'B02': 'Fossil Brown coal/Lignite',
        'B03': 'Fossil Coal-derived gas',
        'B04': 'Fossil Gas',
        'B05': 'Fossil Hard coal',
        'B06': 'Fossil Oil',
        'B07': 'Fossil Oil shale',
        'B08': 'Fossil Peat',
        'B09': 'Geothermal',
        'B10': 'Hydro Pumped Storage',
        'B11': 'Hydro Run-of-river and poundage',
        'B12': 'Hydro Water Reservoir',
        'B13': 'Marine',
        'B14': 'Nuclear',
        'B15': 'Other renewable',
        'B16': 'Solar',
        'B17': 'Waste',
        'B18': 'Wind Offshore',
        'B19': 'Wind Onshore',
        'B20': 'Other'
    };
    return names[genType] || genType;
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
    
    // Energy controls
    document.getElementById('energy-country').addEventListener('change', createEnergyChart);
    document.getElementById('energy-data-type').addEventListener('change', createEnergyChart);
    document.getElementById('energy-time-range').addEventListener('change', createEnergyChart);
    
    // Analytics controls
    document.getElementById('analysis-country').addEventListener('change', createAnalyticsDashboard);
    document.getElementById('analysis-time-range').addEventListener('change', createAnalyticsDashboard);
    
    // Renewables controls
    document.getElementById('renewables-country').addEventListener('change', createRenewablesDashboard);
    document.getElementById('renewables-time-range').addEventListener('change', createRenewablesDashboard);
    
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
                case 'energy-analysis':
                    createAnalyticsDashboard();
                    break;
                case 'renewables':
                    createRenewablesDashboard();
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
    // Analytics and renewables dashboards will be loaded on demand
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
                case 'energy-analysis':
                    createAnalyticsDashboard();
                    break;
                case 'renewables':
                    createRenewablesDashboard();
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

// =====================================================
// PORTFOLIO ANALYTICS FUNCTIONS
// =====================================================

// Global portfolio data storage
let currentPortfolioData = null;

async function loadSamplePortfolio() {
    try {
        console.log('Loading sample portfolio...');
        const response = await fetch(API_ENDPOINTS.portfolio.sample);
        const data = await response.json();
        
        if (data.success && data.portfolio_data) {
            currentPortfolioData = data.portfolio_data;
            displayPortfolioComposition(currentPortfolioData);
            
            // Show success message
            showPortfolioMessage('Sample portfolio loaded successfully! Contains ' + 
                currentPortfolioData.length + ' commodities.', 'success');
        } else {
            showPortfolioMessage('Failed to load sample portfolio: ' + (data.error || 'Unknown error'), 'danger');
        }
    } catch (error) {
        console.error('Portfolio loading error:', error);
        showPortfolioMessage('Error loading sample portfolio: ' + error.message, 'danger');
    }
}

function displayPortfolioComposition(portfolioData) {
    const container = document.getElementById('portfolio-composition');
    
    if (!portfolioData || portfolioData.length === 0) {
        container.innerHTML = '<div class="alert alert-warning">No portfolio data available</div>';
        return;
    }
    
    // Create portfolio composition table
    let html = `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Name</th>
                        <th>Current Price</th>
                        <th>Data Points</th>
                        <th>Weight</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    portfolioData.forEach((commodity, index) => {
        const currentPrice = commodity.prices && commodity.prices.length > 0 ? 
            commodity.prices[commodity.prices.length - 1] : 'N/A';
        const dataPoints = commodity.prices ? commodity.prices.length : 0;
        
        html += `
            <tr>
                <td><strong>${commodity.symbol}</strong></td>
                <td>${commodity.name || commodity.symbol}</td>
                <td>$${typeof currentPrice === 'number' ? currentPrice.toFixed(2) : currentPrice}</td>
                <td>${dataPoints}</td>
                <td>
                    <input type="number" class="form-control form-control-sm" 
                           value="${commodity.weight}" step="0.1" min="0" max="10"
                           onchange="updateCommodityWeight(${index}, this.value)">
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="removeCommodityFromPortfolio(${index})">
                        <i class='bx bx-trash'></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

function updateCommodityWeight(index, newWeight) {
    if (currentPortfolioData && currentPortfolioData[index]) {
        currentPortfolioData[index].weight = parseFloat(newWeight) || 1.0;
        console.log(`Updated ${currentPortfolioData[index].symbol} weight to ${newWeight}`);
    }
}

function removeCommodityFromPortfolio(index) {
    if (currentPortfolioData && index >= 0 && index < currentPortfolioData.length) {
        const removed = currentPortfolioData.splice(index, 1);
        displayPortfolioComposition(currentPortfolioData);
        showPortfolioMessage(`Removed ${removed[0].symbol} from portfolio`, 'info');
    }
}

async function analyzePortfolio() {
    if (!currentPortfolioData || currentPortfolioData.length < 2) {
        showPortfolioMessage('Please load a portfolio with at least 2 commodities first', 'warning');
        return;
    }
    
    const analysisType = document.getElementById('portfolio-analysis-type').value;
    const riskTolerance = document.getElementById('portfolio-risk-tolerance').value;
    const timeHorizon = parseInt(document.getElementById('portfolio-time-horizon').value);
    
    try {
        // Show loading state
        showPortfolioMessage('Analyzing portfolio...', 'info');
        
        if (analysisType === 'overview' || analysisType === 'risk') {
            await runPortfolioAnalysis();
        }
        
        if (analysisType === 'simulation') {
            await runMonteCarloSimulation(timeHorizon);
        }
        
        if (analysisType === 'optimization') {
            await runPortfolioOptimization(riskTolerance);
        }
        
    } catch (error) {
        console.error('Portfolio analysis error:', error);
        showPortfolioMessage('Analysis failed: ' + error.message, 'danger');
    }
}

async function runPortfolioAnalysis() {
    try {
        const response = await fetch(API_ENDPOINTS.portfolio.analyze, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                commodities: currentPortfolioData
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.portfolio_metrics) {
            displayPortfolioMetrics(data.portfolio_metrics);
            showPortfolioResults('analysis');
            showPortfolioMessage('Portfolio analysis completed successfully', 'success');
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        throw new Error('Portfolio analysis failed: ' + error.message);
    }
}

async function runMonteCarloSimulation(timeHorizon) {
    try {
        const response = await fetch(API_ENDPOINTS.portfolio.simulate, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                commodities: currentPortfolioData,
                num_simulations: 1000,
                time_horizon_days: timeHorizon
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.simulation_results) {
            displaySimulationResults(data.simulation_results);
            showPortfolioResults('simulation');
            showPortfolioMessage('Monte Carlo simulation completed', 'success');
        } else {
            throw new Error(data.error || 'Simulation failed');
        }
        
    } catch (error) {
        throw new Error('Monte Carlo simulation failed: ' + error.message);
    }
}

async function runPortfolioOptimization(riskTolerance) {
    try {
        const response = await fetch(API_ENDPOINTS.portfolio.optimize, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                commodities: currentPortfolioData,
                risk_tolerance: riskTolerance
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.optimization_results) {
            displayOptimizationResults(data.optimization_results);
            showPortfolioResults('optimization');
            showPortfolioMessage('Portfolio optimization completed', 'success');
        } else {
            throw new Error(data.error || 'Optimization failed');
        }
        
    } catch (error) {
        throw new Error('Portfolio optimization failed: ' + error.message);
    }
}

function displayPortfolioMetrics(metrics) {
    // Display risk metrics
    const riskContainer = document.getElementById('portfolio-risk-metrics');
    riskContainer.innerHTML = `
        <div class="row">
            <div class="col-6">
                <div class="metric-item">
                    <div class="metric-label">Portfolio Volatility</div>
                    <div class="metric-value text-warning">${(metrics.portfolio_volatility * 100).toFixed(2)}%</div>
                </div>
            </div>
            <div class="col-6">
                <div class="metric-item">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value text-info">${metrics.sharpe_ratio.toFixed(3)}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="metric-item">
                    <div class="metric-label">VaR (95%)</div>
                    <div class="metric-value text-danger">${(metrics.var_95 * 100).toFixed(2)}%</div>
                </div>
            </div>
            <div class="col-6">
                <div class="metric-item">
                    <div class="metric-label">Max Drawdown</div>
                    <div class="metric-value text-danger">${(metrics.max_drawdown * 100).toFixed(2)}%</div>
                </div>
            </div>
        </div>
    `;
    
    // Display performance metrics
    const performanceContainer = document.getElementById('portfolio-performance-metrics');
    performanceContainer.innerHTML = `
        <div class="row">
            <div class="col-6">
                <div class="metric-item">
                    <div class="metric-label">Expected Return</div>
                    <div class="metric-value text-success">${(metrics.portfolio_return * 100).toFixed(2)}%</div>
                </div>
            </div>
            <div class="col-6">
                <div class="metric-item">
                    <div class="metric-label">Diversification Ratio</div>
                    <div class="metric-value text-primary">${metrics.diversification_ratio.toFixed(3)}</div>
                </div>
            </div>
            <div class="col-12">
                <div class="metric-item">
                    <div class="metric-label">Portfolio Composition</div>
                    <div class="metric-value">
                        ${metrics.symbols.map((symbol, i) => 
                            `${symbol}: ${(metrics.weights[i] * 100).toFixed(1)}%`
                        ).join(' | ')}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Create correlation matrix heatmap
    if (metrics.correlation_matrix) {
        createCorrelationMatrix(metrics.correlation_matrix, metrics.symbols);
    }
    
    // Create risk decomposition chart
    if (metrics.risk_decomposition) {
        createRiskDecompositionChart(metrics.risk_decomposition, metrics.symbols);
    }
}

function displaySimulationResults(results) {
    // Create simulation paths chart
    createSimulationPathsChart(results);
    
    // Create return distribution chart
    createReturnDistributionChart(results);
}

function displayOptimizationResults(results) {
    // Create optimal weights chart
    createOptimalWeightsChart(results);
    
    // Display weight changes
    displayWeightChanges(results.weight_changes);
}

function createCorrelationMatrix(correlationMatrix, symbols) {
    const z = [];
    const labels = symbols;
    
    for (let i = 0; i < symbols.length; i++) {
        const row = [];
        for (let j = 0; j < symbols.length; j++) {
            row.push(correlationMatrix[symbols[i]][symbols[j]]);
        }
        z.push(row);
    }
    
    const trace = {
        z: z,
        x: labels,
        y: labels,
        type: 'heatmap',
        colorscale: 'RdBu',
        zmid: 0,
        colorbar: {
            title: 'Correlation'
        }
    };
    
    const layout = {
        title: 'Asset Correlation Matrix',
        xaxis: { title: 'Assets' },
        yaxis: { title: 'Assets' },
        height: 400
    };
    
    Plotly.newPlot('portfolio-correlation-chart', [trace], layout, {responsive: true});
}

function createRiskDecompositionChart(riskDecomp, symbols) {
    const trace = {
        values: riskDecomp.percentage_contribution,
        labels: symbols,
        type: 'pie',
        textinfo: 'label+percent',
        textposition: 'outside'
    };
    
    const layout = {
        title: 'Risk Contribution by Asset',
        height: 400
    };
    
    Plotly.newPlot('portfolio-risk-chart', [trace], layout, {responsive: true});
}

function createSimulationPathsChart(results) {
    const traces = [];
    
    // Add first 20 simulation paths
    for (let i = 0; i < Math.min(20, results.simulation_paths.length); i++) {
        traces.push({
            y: results.simulation_paths[i],
            type: 'scatter',
            mode: 'lines',
            opacity: 0.3,
            line: { width: 1 },
            showlegend: false,
            hoverinfo: 'none'
        });
    }
    
    // Add percentile bands
    const numPoints = results.simulation_paths[0].length;
    const percentiles = {
        '5th': [],
        '50th': [],
        '95th': []
    };
    
    for (let day = 0; day < numPoints; day++) {
        const dayValues = results.simulation_paths.map(path => path[day]).sort((a, b) => a - b);
        percentiles['5th'].push(dayValues[Math.floor(dayValues.length * 0.05)]);
        percentiles['50th'].push(dayValues[Math.floor(dayValues.length * 0.5)]);
        percentiles['95th'].push(dayValues[Math.floor(dayValues.length * 0.95)]);
    }
    
    // Add percentile traces
    traces.push({
        y: percentiles['95th'],
        name: '95th Percentile',
        type: 'scatter',
        mode: 'lines',
        line: { color: 'green', width: 2 }
    });
    
    traces.push({
        y: percentiles['50th'],
        name: 'Median',
        type: 'scatter',
        mode: 'lines',
        line: { color: 'blue', width: 3 }
    });
    
    traces.push({
        y: percentiles['5th'],
        name: '5th Percentile',
        type: 'scatter',
        mode: 'lines',
        line: { color: 'red', width: 2 }
    });
    
    const layout = {
        title: `Monte Carlo Simulation (${results.num_simulations} paths)`,
        xaxis: { title: 'Days' },
        yaxis: { title: 'Portfolio Value' },
        height: 400
    };
    
    Plotly.newPlot('portfolio-simulation-chart', traces, layout, {responsive: true});
}

function createReturnDistributionChart(results) {
    const finalValues = [];
    for (let path of results.simulation_paths) {
        finalValues.push(path[path.length - 1]);
    }
    
    const trace = {
        x: finalValues,
        type: 'histogram',
        nbinsx: 30,
        opacity: 0.7
    };
    
    const layout = {
        title: 'Final Value Distribution',
        xaxis: { title: 'Final Portfolio Value' },
        yaxis: { title: 'Frequency' },
        height: 400
    };
    
    Plotly.newPlot('portfolio-distribution-chart', [trace], layout, {responsive: true});
}

function createOptimalWeightsChart(results) {
    const symbols = Object.keys(results.optimal_weights);
    const weights = Object.values(results.optimal_weights);
    
    const trace = {
        x: symbols,
        y: weights,
        type: 'bar',
        text: weights.map(w => (w * 100).toFixed(1) + '%'),
        textposition: 'auto'
    };
    
    const layout = {
        title: 'Optimal Portfolio Weights',
        xaxis: { title: 'Assets' },
        yaxis: { title: 'Weight', tickformat: '.1%' },
        height: 400
    };
    
    Plotly.newPlot('portfolio-optimization-chart', [trace], layout, {responsive: true});
}

function displayWeightChanges(weightChanges) {
    const container = document.getElementById('portfolio-weight-changes');
    
    let html = `
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Asset</th>
                        <th>Current</th>
                        <th>Optimal</th>
                        <th>Change</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    Object.entries(weightChanges).forEach(([symbol, changes]) => {
        const changeClass = changes.change > 0 ? 'text-success' : 'text-danger';
        html += `
            <tr>
                <td><strong>${symbol}</strong></td>
                <td>${(changes.current_weight * 100).toFixed(1)}%</td>
                <td>${(changes.optimal_weight * 100).toFixed(1)}%</td>
                <td class="${changeClass}">
                    ${changes.change > 0 ? '+' : ''}${(changes.change * 100).toFixed(1)}%
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

function showPortfolioResults(analysisType) {
    // Hide all result sections first
    document.getElementById('portfolio-analysis-results').style.display = 'none';
    document.getElementById('portfolio-charts-row').style.display = 'none';
    document.getElementById('portfolio-simulation-row').style.display = 'none';
    document.getElementById('portfolio-optimization-row').style.display = 'none';
    
    // Show relevant sections
    if (analysisType === 'analysis' || analysisType === 'risk') {
        document.getElementById('portfolio-analysis-results').style.display = 'block';
        document.getElementById('portfolio-charts-row').style.display = 'block';
    } else if (analysisType === 'simulation') {
        document.getElementById('portfolio-simulation-row').style.display = 'block';
    } else if (analysisType === 'optimization') {
        document.getElementById('portfolio-optimization-row').style.display = 'block';
    }
}

function showPortfolioMessage(message, type) {
    // Create and show a temporary alert message
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of portfolio composition
    const container = document.getElementById('portfolio-composition');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function addCommodityToPortfolio() {
    // This would open a modal to search and add commodities
    // For now, show a simple alert
    alert('Feature coming soon: Add individual commodities to your portfolio');
}

function getCsrfToken() {
    // Get CSRF token from meta tag or cookie
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// US ENERGY (EIA) FUNCTIONS

// US Energy chart instance (using Plotly.js)
let usEuropeComparisonChart = null;

// Initialize US Energy tab
function initializeUSEnergyTab() {
    console.log('🇺🇸 Initializing US Energy (EIA) tab');
    
    // Set default dates (last 12 months)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(endDate.getFullYear() - 1);
    
    document.getElementById('us-start-date').value = startDate.toISOString().slice(0, 7);
    document.getElementById('us-end-date').value = endDate.toISOString().slice(0, 7);
    
    // Setup event listeners
    document.getElementById('us-energy-type').addEventListener('change', updateUSEnergySubtypes);
    document.getElementById('fetch-us-energy').addEventListener('click', fetchUSEnergyData);
    
    // Initialize subtypes
    updateUSEnergySubtypes();
}

function updateUSEnergySubtypes() {
    const energyType = document.getElementById('us-energy-type').value;
    const subtypeSelect = document.getElementById('us-energy-subtype');
    
    // Clear existing options
    subtypeSelect.innerHTML = '';
    
    const subtypes = {
        'electricity_generation': [
            { value: '', text: 'All Sources' },
            { value: 'coal', text: 'Coal' },
            { value: 'natural_gas', text: 'Natural Gas' },
            { value: 'nuclear', text: 'Nuclear' },
            { value: 'hydro', text: 'Hydroelectric' },
            { value: 'wind', text: 'Wind' },
            { value: 'solar', text: 'Solar' },
            { value: 'geothermal', text: 'Geothermal' },
            { value: 'biomass', text: 'Biomass' }
        ],
        'electricity_prices': [
            { value: 'residential', text: 'Residential' },
            { value: 'commercial', text: 'Commercial' },
            { value: 'industrial', text: 'Industrial' },
            { value: 'wholesale', text: 'Wholesale' }
        ],
        'natural_gas': [
            { value: 'production', text: 'Production' },
            { value: 'consumption', text: 'Consumption' },
            { value: 'price', text: 'Price' }
        ],
        'renewable_energy': [
            { value: 'all', text: 'All Renewables' },
            { value: 'solar', text: 'Solar' },
            { value: 'wind', text: 'Wind' },
            { value: 'hydro', text: 'Hydroelectric' },
            { value: 'geothermal', text: 'Geothermal' },
            { value: 'biomass', text: 'Biomass' }
        ],
        'petroleum': [
            { value: 'crude_oil', text: 'Crude Oil' },
            { value: 'gasoline', text: 'Gasoline' },
            { value: 'heating_oil', text: 'Heating Oil' },
            { value: 'diesel', text: 'Diesel' }
        ]
    };
    
    const options = subtypes[energyType] || [];
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.value;
        optionElement.textContent = option.text;
        subtypeSelect.appendChild(optionElement);
    });
}

async function fetchUSEnergyData() {
    console.log('🔄 Fetching US Energy data from EIA...');
    
    const energyType = document.getElementById('us-energy-type').value;
    const state = document.getElementById('us-state').value;
    const subtype = document.getElementById('us-energy-subtype').value;
    const startDate = document.getElementById('us-start-date').value;
    const endDate = document.getElementById('us-end-date').value;
    
    // Show loading state
    const button = document.getElementById('fetch-us-energy');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i>';
    button.disabled = true;
    
    try {
        let endpoint = API_ENDPOINTS.eia[energyType];
        let params = new URLSearchParams();
        
        // Add common parameters
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        // Add type-specific parameters
        switch (energyType) {
            case 'electricity_generation':
                if (state) params.append('state', state);
                break;
            case 'electricity_prices':
                if (state) params.append('region', state);
                break;
            case 'natural_gas':
                if (subtype) params.append('data_type', subtype);
                break;
            case 'renewable_energy':
                if (subtype) params.append('source', subtype);
                break;
            case 'petroleum':
                if (subtype) params.append('product', subtype);
                const productType = document.getElementById('us-energy-subtype').selectedOptions[0].dataset.type || 'production';
                params.append('data_type', productType);
                break;
        }
        
        const url = `${endpoint}?${params.toString()}`;
        console.log('📡 EIA API URL:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch US energy data');
        }
        
        console.log('✅ EIA data received:', data);
        
        // Display the data
        displayUSEnergyData(data, energyType);
        
        // Show statistics
        calculateUSEnergyStats(data.data);
        
    } catch (error) {
        console.error('❌ Error fetching US energy data:', error);
        alert(`Error fetching US energy data: ${error.message}`);
    } finally {
        // Restore button state
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

function displayUSEnergyData(response, energyType) {
    console.log('📊 Displaying US Energy data...');
    
    const data = response.data;
    const region = response.region || 'National';
    
    // Update chart title
    const chartTitle = document.getElementById('us-energy-chart-title');
    chartTitle.textContent = `US ${energyType.replace('_', ' ').toUpperCase()} - ${region}`;
    
    // Prepare chart data based on energy type
    let traces = [];
    
    if (energyType === 'electricity_generation' && data.generation_by_source) {
        // Multiple series for generation by source
        const colors = {
            'COL': '#8B4513',      // Coal - Brown
            'NG': '#FFA500',       // Natural Gas - Orange
            'NUC': '#FF6B6B',      // Nuclear - Red
            'WAT': '#4ECDC4',      // Hydro - Teal
            'WND': '#45B7D1',      // Wind - Blue
            'SUN': '#FFD93D',      // Solar - Yellow
            'GEO': '#FF8C94',      // Geothermal - Pink
            'WOO': '#95E1D3',      // Biomass - Light Green
            'OTH': '#C7CEEA'       // Other - Light Purple
        };
        
        Object.entries(data.generation_by_source).forEach(([source, values]) => {
            traces.push({
                name: getEnergySourceName(source),
                x: data.dates,
                y: values,
                type: 'scatter',
                mode: 'lines',
                line: { color: colors[source] || '#6c757d', width: 2 },
                hovertemplate: `${getEnergySourceName(source)}<br>%{x}<br>%{y:.2f} ${getDataUnit(energyType)}<extra></extra>`
            });
        });
        
    } else if (data.renewable_by_source) {
        // Renewable energy by source
        const renewableColors = {
            'Solar': '#FFD93D',
            'Wind': '#45B7D1',
            'Hydro': '#4ECDC4',
            'Geothermal': '#FF8C94',
            'Biomass': '#95E1D3'
        };
        
        Object.entries(data.renewable_by_source).forEach(([source, values]) => {
            traces.push({
                name: source,
                x: data.dates,
                y: values,
                type: 'scatter',
                mode: 'lines',
                line: { color: renewableColors[source] || '#6c757d', width: 2 },
                hovertemplate: `${source}<br>%{x}<br>%{y:.2f} ${getDataUnit(energyType)}<extra></extra>`
            });
        });
        
    } else {
        // Single series data (prices, natural gas, petroleum)
        traces.push({
            name: getDataTypeLabel(energyType),
            x: data.dates,
            y: data.values,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#0d6efd', width: 2 },
            marker: { color: '#0d6efd', size: 4 },
            fill: 'tozeroy',
            fillcolor: 'rgba(13, 110, 253, 0.1)',
            hovertemplate: `%{x}<br>%{y:.2f} ${getDataUnit(energyType)}<extra></extra>`
        });
    }
    
    // Create layout
    const layout = {
        title: `US ${energyType.replace('_', ' ')} Data - ${region}`,
        xaxis: { 
            title: 'Date',
            type: 'date'
        },
        yaxis: { 
            title: getDataUnit(energyType)
        },
        showlegend: true,
        height: 400,
        margin: { t: 60, b: 60, l: 60, r: 60 },
        hovermode: 'x unified'
    };
    
    // Create chart using Plotly
    Plotly.newPlot('us-energy-chart', traces, layout, { responsive: true, displayModeBar: true });
    
    console.log('✅ US Energy chart created successfully');
}

function calculateUSEnergyStats(data) {
    if (!data || (!data.values && !data.generation_by_source)) {
        return;
    }
    
    let values = [];
    
    if (data.values) {
        values = data.values.filter(v => v != null && !isNaN(v)).map(v => parseFloat(v));
    } else if (data.generation_by_source) {
        // Sum all generation sources for total
        const dates = data.dates;
        values = dates.map((_, index) => {
            return Object.values(data.generation_by_source)
                .reduce((sum, sourceValues) => {
                    const val = sourceValues[index];
                    const numVal = val != null ? parseFloat(val) : 0;
                    return sum + (isNaN(numVal) ? 0 : numVal);
                }, 0);
        });
    }
    
    if (values.length === 0) return;
    
    // Calculate statistics
    const latest = parseFloat(values[values.length - 1]) || 0;
    const previous = parseFloat(values[values.length - 2]) || 0;
    const average = values.reduce((sum, val) => sum + (parseFloat(val) || 0), 0) / values.length;
    
    // Calculate period change
    let periodChange = 0;
    if (previous && previous !== 0 && !isNaN(previous) && !isNaN(latest)) {
        periodChange = ((latest - previous) / previous * 100);
    }
    // Ensure periodChange is a valid number
    if (isNaN(periodChange) || !isFinite(periodChange)) {
        periodChange = 0;
    }
    
    // Calculate trend (simple linear regression slope)
    const n = values.length;
    const sumX = n * (n - 1) / 2;
    const sumXY = values.reduce((sum, val, index) => sum + val * index, 0);
    const sumY = values.reduce((sum, val) => sum + val, 0);
    const sumXX = n * (n - 1) * (2 * n - 1) / 6;
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    
    // Update UI
    document.getElementById('us-latest-value').textContent = formatNumber(latest);
    document.getElementById('us-period-change').textContent = `${periodChange >= 0 ? '+' : ''}${periodChange.toFixed(2)}%`;
    document.getElementById('us-period-change').className = `card-text display-6 ${periodChange >= 0 ? 'text-success' : 'text-danger'}`;
    document.getElementById('us-average-value').textContent = formatNumber(average);
    document.getElementById('us-trend').textContent = slope > 0 ? '📈 Rising' : slope < 0 ? '📉 Falling' : '➡️ Stable';
    
    // Show statistics section
    document.getElementById('us-energy-stats').style.display = 'block';
}

function getEnergySourceName(code) {
    const sourceNames = {
        'COL': 'Coal',
        'NG': 'Natural Gas',
        'NUC': 'Nuclear',
        'WAT': 'Hydroelectric',
        'WND': 'Wind',
        'SUN': 'Solar',
        'GEO': 'Geothermal',
        'WOO': 'Biomass',
        'OTH': 'Other'
    };
    return sourceNames[code] || code;
}

function getDataTypeLabel(energyType) {
    const labels = {
        'electricity_generation': 'Generation (MWh)',
        'electricity_prices': 'Price (cents/kWh)',
        'natural_gas': 'Natural Gas',
        'renewable_energy': 'Renewable Generation (MWh)',
        'petroleum': 'Petroleum'
    };
    return labels[energyType] || energyType;
}

function getDataUnit(energyType) {
    const units = {
        'electricity_generation': 'MWh',
        'electricity_prices': 'Cents/kWh',
        'natural_gas': 'MMcf',
        'renewable_energy': 'MWh',
        'petroleum': 'Thousand Barrels'
    };
    return units[energyType] || 'Units';
}

function formatNumber(num) {
    // Ensure num is a valid number
    const numVal = parseFloat(num);
    if (isNaN(numVal) || !isFinite(numVal)) {
        return '0.00';
    }
    
    if (numVal >= 1000000) {
        return (numVal / 1000000).toFixed(1) + 'M';
    } else if (numVal >= 1000) {
        return (numVal / 1000).toFixed(1) + 'K';
    } else {
        return numVal.toFixed(2);
    }
}

// Initialize US Energy tab when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
    
    // Initialize US Energy tab
    initializeUSEnergyTab();
    
    // Initialize FRED Economic Data tab
    initializeFREDTab();
    
    console.log('🇺🇸 US Energy (EIA) integration initialized');
    console.log('📊 FRED Economic Data integration initialized');
});

// =====================================================
// FRED Economic Data Functions
// =====================================================

function initializeFREDTab() {
    // Set default dates
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(endDate.getFullYear() - 5); // Default to 5 years ago
    
    document.getElementById('fred-start-date').value = startDate.toISOString().split('T')[0];
    document.getElementById('fred-end-date').value = endDate.toISOString().split('T')[0];
    
    // Event listeners
    document.getElementById('fetch-fred-data').addEventListener('click', fetchFREDData);
    document.getElementById('search-fred-indicators').addEventListener('click', searchFREDIndicators);
    document.getElementById('fetch-fred-multiple').addEventListener('click', fetchFREDMultipleSeries);
    
    // Multi-series checkbox toggle
    document.getElementById('fred-multi-series').addEventListener('change', function() {
        const multiSection = document.getElementById('fred-multi-section');
        multiSection.style.display = this.checked ? 'block' : 'none';
    });
    
    // Enter key support for search
    document.getElementById('fred-search-text').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchFREDIndicators();
        }
    });
}

async function fetchFREDData() {
    const indicator = document.getElementById('fred-indicator').value;
    const frequency = document.getElementById('fred-frequency').value;
    const startDate = document.getElementById('fred-start-date').value;
    const endDate = document.getElementById('fred-end-date').value;
    const transform = document.getElementById('fred-transform').value;
    const chartType = document.getElementById('fred-chart-type').value;
    
    if (!indicator) {
        alert('Please select an economic indicator');
        return;
    }
    
    const fetchBtn = document.getElementById('fetch-fred-data');
    const originalText = fetchBtn.innerHTML;
    fetchBtn.innerHTML = '<i class="bx bx-loader bx-spin"></i> Loading...';
    fetchBtn.disabled = true;
    
    try {
        const params = new URLSearchParams({
            series_id: indicator,
            frequency: frequency,
            start_date: startDate,
            end_date: endDate,
            transform: transform
        });
        
        const response = await fetch(`${API_ENDPOINTS.fred.series}?${params}`);
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            displayFREDChart(data.data, indicator, chartType);
            displayFREDStats(data.data, indicator);
            document.getElementById('fred-stats').style.display = 'block';
        } else {
            console.error('FRED API Error:', data);
            alert(`Error fetching FRED data: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error fetching FRED data:', error);
        alert('Error fetching FRED data. Please try again.');
    } finally {
        fetchBtn.innerHTML = originalText;
        fetchBtn.disabled = false;
    }
}

async function searchFREDIndicators() {
    const searchText = document.getElementById('fred-search-text').value.trim();
    
    if (!searchText) {
        alert('Please enter search terms');
        return;
    }
    
    const searchBtn = document.getElementById('search-fred-indicators');
    const originalText = searchBtn.innerHTML;
    searchBtn.innerHTML = '<i class="bx bx-loader bx-spin"></i>';
    searchBtn.disabled = true;
    
    try {
        const params = new URLSearchParams({
            query: searchText,
            limit: 20
        });
        
        const response = await fetch(`${API_ENDPOINTS.fred.search}?${params}`);
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            displayFREDSearchResults(data.data);
            document.getElementById('fred-search-results').style.display = 'block';
        } else {
            console.error('FRED Search Error:', data);
            alert(`Error searching FRED indicators: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error searching FRED indicators:', error);
        alert('Error searching FRED indicators. Please try again.');
    } finally {
        searchBtn.innerHTML = originalText;
        searchBtn.disabled = false;
    }
}

async function fetchFREDMultipleSeries() {
    const seriesText = document.getElementById('fred-additional-series').value.trim();
    const frequency = document.getElementById('fred-frequency').value;
    const startDate = document.getElementById('fred-start-date').value;
    const endDate = document.getElementById('fred-end-date').value;
    const transform = document.getElementById('fred-transform').value;
    
    if (!seriesText) {
        alert('Please enter series IDs separated by commas');
        return;
    }
    
    const seriesIds = seriesText.split(',').map(s => s.trim()).filter(s => s);
    
    if (seriesIds.length === 0) {
        alert('Please enter valid series IDs');
        return;
    }
    
    const fetchBtn = document.getElementById('fetch-fred-multiple');
    const originalText = fetchBtn.innerHTML;
    fetchBtn.innerHTML = '<i class="bx bx-loader bx-spin"></i> Loading...';
    fetchBtn.disabled = true;
    
    try {
        const params = new URLSearchParams({
            series_ids: seriesIds.join(','),
            frequency: frequency,
            start_date: startDate,
            end_date: endDate,
            transform: transform
        });
        
        const response = await fetch(`${API_ENDPOINTS.fred.multiple_series}?${params}`);
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            displayFREDMultipleChart(data.data, seriesIds);
        } else {
            console.error('FRED Multiple Series Error:', data);
            alert(`Error fetching multiple FRED series: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error fetching multiple FRED series:', error);
        alert('Error fetching multiple FRED series. Please try again.');
    } finally {
        fetchBtn.innerHTML = originalText;
        fetchBtn.disabled = false;
    }
}

function displayFREDChart(data, indicator, chartType = 'line') {
    const chartDiv = document.getElementById('fred-chart');
    
    if (!data || !data.observations || data.observations.length === 0) {
        chartDiv.innerHTML = '<p class="text-center text-muted">No data available for the selected parameters.</p>';
        return;
    }
    
    const observations = data.observations;
    const dates = observations.map(obs => obs.date);
    const values = observations.map(obs => parseFloat(obs.value)).filter(val => !isNaN(val));
    
    if (values.length === 0) {
        chartDiv.innerHTML = '<p class="text-center text-muted">No valid data points found.</p>';
        return;
    }
    
    const title = getFREDIndicatorName(indicator);
    document.getElementById('fred-chart-title').textContent = title;
    
    let trace = {
        x: dates,
        y: values,
        name: title,
        line: { color: '#007bff', width: 2 }
    };
    
    switch (chartType) {
        case 'bar':
            trace.type = 'bar';
            trace.marker = { color: '#007bff' };
            delete trace.line;
            break;
        case 'scatter':
            trace.type = 'scatter';
            trace.mode = 'markers';
            trace.marker = { color: '#007bff', size: 6 };
            delete trace.line;
            break;
        default:
            trace.type = 'scatter';
            trace.mode = 'lines';
    }
    
    const layout = {
        title: {
            text: title,
            font: { size: 16 }
        },
        xaxis: {
            title: 'Date',
            type: 'date'
        },
        yaxis: {
            title: data.units || 'Value'
        },
        margin: { l: 60, r: 30, t: 60, b: 60 },
        showlegend: false
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d']
    };
    
    Plotly.newPlot(chartDiv, [trace], layout, config);
}

function displayFREDMultipleChart(data, seriesIds) {
    const chartDiv = document.getElementById('fred-multi-chart');
    
    if (!data || Object.keys(data).length === 0) {
        chartDiv.innerHTML = '<p class="text-center text-muted">No data available for the selected series.</p>';
        return;
    }
    
    const traces = [];
    const colors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6f42c1', '#e83e8c'];
    
    Object.keys(data).forEach((seriesId, index) => {
        const seriesData = data[seriesId];
        
        if (seriesData && seriesData.observations && seriesData.observations.length > 0) {
            const dates = seriesData.observations.map(obs => obs.date);
            const values = seriesData.observations.map(obs => parseFloat(obs.value)).filter(val => !isNaN(val));
            
            if (values.length > 0) {
                traces.push({
                    x: dates,
                    y: values,
                    type: 'scatter',
                    mode: 'lines',
                    name: getFREDIndicatorName(seriesId),
                    line: { 
                        color: colors[index % colors.length], 
                        width: 2 
                    }
                });
            }
        }
    });
    
    if (traces.length === 0) {
        chartDiv.innerHTML = '<p class="text-center text-muted">No valid data found for any series.</p>';
        return;
    }
    
    const layout = {
        title: {
            text: 'Multiple Economic Indicators Comparison',
            font: { size: 16 }
        },
        xaxis: {
            title: 'Date',
            type: 'date'
        },
        yaxis: {
            title: 'Value'
        },
        margin: { l: 60, r: 30, t: 60, b: 60 },
        showlegend: true,
        legend: {
            x: 0,
            y: 1,
            bgcolor: 'rgba(255,255,255,0.8)'
        }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d']
    };
    
    Plotly.newPlot(chartDiv, traces, layout, config);
}

function displayFREDStats(data, indicator) {
    if (!data || !data.observations || data.observations.length === 0) {
        return;
    }
    
    const observations = data.observations;
    const values = observations.map(obs => parseFloat(obs.value)).filter(val => !isNaN(val));
    
    if (values.length === 0) {
        return;
    }
    
    // Calculate statistics
    const latestValue = values[values.length - 1];
    const previousValue = values.length > 1 ? values[values.length - 2] : null;
    const average = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - average, 2), 0) / values.length;
    const volatility = Math.sqrt(variance);
    
    // Period change
    let periodChange = 0;
    if (previousValue !== null) {
        periodChange = ((latestValue - previousValue) / previousValue) * 100;
    }
    
    // Update display
    document.getElementById('fred-latest-value').textContent = formatFREDNumber(latestValue);
    document.getElementById('fred-period-change').textContent = `${periodChange >= 0 ? '+' : ''}${periodChange.toFixed(2)}%`;
    document.getElementById('fred-period-change').style.color = periodChange >= 0 ? '#28a745' : '#dc3545';
    document.getElementById('fred-average-value').textContent = formatFREDNumber(average);
    document.getElementById('fred-volatility').textContent = formatFREDNumber(volatility);
}

function displayFREDSearchResults(results) {
    const searchList = document.getElementById('fred-search-list');
    searchList.innerHTML = '';
    
    if (!results || results.length === 0) {
        searchList.innerHTML = '<p class="text-center text-muted">No results found.</p>';
        return;
    }
    
    results.forEach(result => {
        const listItem = document.createElement('a');
        listItem.className = 'list-group-item list-group-item-action';
        listItem.style.cursor = 'pointer';
        
        listItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${result.title}</h6>
                <small class="text-muted">${result.id}</small>
            </div>
            <p class="mb-1">${result.notes || 'No description available'}</p>
            <small class="text-muted">Units: ${result.units || 'N/A'} | Frequency: ${result.frequency || 'N/A'}</small>
        `;
        
        listItem.addEventListener('click', function() {
            // Update the indicator selector with this result
            const indicator = result.id;
            const indicatorSelect = document.getElementById('fred-indicator');
            
            // Check if this option already exists
            let optionExists = false;
            for (let option of indicatorSelect.options) {
                if (option.value === indicator) {
                    optionExists = true;
                    indicatorSelect.value = indicator;
                    break;
                }
            }
            
            // If option doesn't exist, add it
            if (!optionExists) {
                const newOption = document.createElement('option');
                newOption.value = indicator;
                newOption.textContent = `${result.title} (${indicator})`;
                indicatorSelect.appendChild(newOption);
                indicatorSelect.value = indicator;
            }
            
            // Hide search results
            document.getElementById('fred-search-results').style.display = 'none';
            
            // Clear search text
            document.getElementById('fred-search-text').value = '';
        });
        
        searchList.appendChild(listItem);
    });
}

function getFREDIndicatorName(indicator) {
    const names = {
        'GDP': 'Gross Domestic Product',
        'CPIAUCSL': 'Consumer Price Index',
        'UNRATE': 'Unemployment Rate',
        'FEDFUNDS': 'Federal Funds Rate',
        'TB3MS': '3-Month Treasury Rate',
        'DGS10': '10-Year Treasury Rate',
        'PAYEMS': 'Nonfarm Payrolls',
        'INDPRO': 'Industrial Production',
        'HOUST': 'Housing Starts',
        'DEXUSEU': 'USD/EUR Exchange Rate',
        'DCOILWTICO': 'WTI Oil Price',
        'GOLDAMGBD228NLBM': 'Gold Price'
    };
    return names[indicator] || indicator;
}

function formatFREDNumber(num) {
    if (Math.abs(num) >= 1000000000) {
        return (num / 1000000000).toFixed(1) + 'B';
    } else if (Math.abs(num) >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (Math.abs(num) >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    } else if (Math.abs(num) >= 1) {
        return num.toFixed(2);
    } else {
        return num.toFixed(4);
    }
}