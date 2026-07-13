// src/charts.js

//fixed: newest chart data is posted first (desc)
//fixed: draws left to right now
let telemetryChart;
let telemetryChart24h;

async function fetchChartData() {
    try {
        const apiHost = window.location.hostname;
        const res = await fetch(`http://${apiHost}:8000/api/v1/telemetry/history?limit=100`);
        let data = await res.json();

        data.reverse();

        const labels = data.map(d => {
            const timeParts = d.timestamp.split(' ');
            return timeParts.length > 1 ? timeParts[1] : d.timestamp;
        });

        // live data
        const phData = data.map(d => parseFloat(d.ph) || null);
        const ecData = data.map(d => parseFloat(d.ec) || null);
        const tempData = data.map(d => parseFloat(d.temp) || null);

        // 1h averages
        const phAvgData = data.map(d => parseFloat(d.ph_avg_60m) || null);
        const ecAvgData = data.map(d => parseFloat(d.ec_avg_60m) || null);
        const tempAvgData = data.map(d => parseFloat(d.temp_avg_60m) || null);

        //24h averages
        const phAvg1440Data = data.map(d => parseFloat(d.ph_avg_1440m) || null);
        const ecAvg1440Data = data.map(d => parseFloat(d.ec_avg_1440m) || null);
        const tempAvg1440Data = data.map(d => parseFloat(d.temp_avg_1440m) || null);

        // live vs 1h chart
        if (!telemetryChart) {
            const ctx = document.getElementById('telemetryChart').getContext('2d');
            telemetryChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Live pH', data: phData, borderColor: '#F472B6', yAxisID: 'y', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: '60m Avg pH', data: phAvgData, borderColor: '#DB2777', borderDash: [5, 5], yAxisID: 'y', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: 'Live EC', data: ecData, borderColor: '#34D399', yAxisID: 'y1', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: '60m Avg EC', data: ecAvgData, borderColor: '#047857', borderDash: [5, 5], yAxisID: 'y1', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: 'Live Temp', data: tempData, borderColor: '#22D3EE', yAxisID: 'y2', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: '60m Avg Temp', data: tempAvgData, borderColor: '#0E7490', borderDash: [5, 5], yAxisID: 'y2', borderWidth: 2, pointRadius: 0, tension: 0.2 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94A3B8' } } },
                    scales: {
                        x: { grid: { color: '#1E293B' }, ticks: { color: '#64748B' } },
                        y: { type: 'linear', display: true, position: 'right', grid: { color: '#1E293B' }, ticks: { color: '#F472B6' }, title: {display: true, text: 'pH'} },
                        y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false }, ticks: { color: '#34D399' }, title: {display: true, text: 'EC'} },
                        y2: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false }, ticks: { color: '#22D3EE' }, title: {display: true, text: 'Temp'} }
                    }
                }
            });
        } else {
            telemetryChart.data.labels = labels;
            telemetryChart.data.datasets[0].data = phData;
            telemetryChart.data.datasets[1].data = phAvgData;
            telemetryChart.data.datasets[2].data = ecData;
            telemetryChart.data.datasets[3].data = ecAvgData;
            telemetryChart.data.datasets[4].data = tempData;
            telemetryChart.data.datasets[5].data = tempAvgData;
            telemetryChart.update('none');
        }

        // 1h vs 24h chart
        if (!telemetryChart24h) {
            const ctx2 = document.getElementById('telemetryChart24h').getContext('2d');
            telemetryChart24h = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: '60m Avg pH', data: phAvgData, borderColor: '#DB2777', yAxisID: 'y', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: '24h Avg pH', data: phAvg1440Data, borderColor: '#831843', borderDash: [5, 5], yAxisID: 'y', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: '60m Avg EC', data: ecAvgData, borderColor: '#047857', yAxisID: 'y1', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: '24h Avg EC', data: ecAvg1440Data, borderColor: '#064E3B', borderDash: [5, 5], yAxisID: 'y1', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: '60m Avg Temp', data: tempAvgData, borderColor: '#0E7490', yAxisID: 'y2', borderWidth: 2, pointRadius: 0, tension: 0.2 },
                        { label: '24h Avg Temp', data: tempAvg1440Data, borderColor: '#164E63', borderDash: [5, 5], yAxisID: 'y2', borderWidth: 2, pointRadius: 0, tension: 0.2 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94A3B8' } } },
                    scales: {
                        x: { grid: { color: '#1E293B' }, ticks: { color: '#64748B' } },
                        y: { type: 'linear', display: true, position: 'right', grid: { color: '#1E293B' }, ticks: { color: '#DB2777' }, title: {display: true, text: 'pH'} },
                        y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false }, ticks: { color: '#047857' }, title: {display: true, text: 'EC'} },
                        y2: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false }, ticks: { color: '#0E7490' }, title: {display: true, text: 'Temp'} }
                    }
                }
            });
        } else {
            telemetryChart24h.data.labels = labels;
            telemetryChart24h.data.datasets[0].data = phAvgData;
            telemetryChart24h.data.datasets[1].data = phAvg1440Data;
            telemetryChart24h.data.datasets[2].data = ecAvgData;
            telemetryChart24h.data.datasets[3].data = ecAvg1440Data;
            telemetryChart24h.data.datasets[4].data = tempAvgData;
            telemetryChart24h.data.datasets[5].data = tempAvg1440Data;
            telemetryChart24h.update('none');
        }

    } catch (e) { console.error("Chart Fetch Error:", e); }
}

document.addEventListener("DOMContentLoaded", () => {
    fetchChartData();
    setInterval(fetchChartData, 5000);
});