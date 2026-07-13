#FastHTML implementation/prototype dashboard
from fasthtml.common import *
import urllib.request
import json
from datetime import datetime

# Pointers to FastAPI
LATEST = "http://localhost:8000/api/v1/telemetry/history?limit=1"
HISTORY = "http://localhost:8000/api/v1/telemetry/history?limit=50"

# app setup - pico, tailwind, chart.js
# https://www.fastht.ml/docs/ref/response_types.html
app, rt = fast_app(
    hdrs=(
        Script(src="https://cdn.tailwindcss.com"),
        Script(src="https://cdn.jsdelivr.net/npm/chart.js"),
        # Import premium fonts
        Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap", rel="stylesheet"),
        Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        # Apply the font to the whole body
        Style("body { font-family: 'Inter', sans-serif; } .font-mono { font-family: 'JetBrains Mono', monospace; }")
    )
)

# live telemetry
def get_sensor_data():
    data = {
        "ph": "--", "ec": "--", "temp": "--",
        "ph_60m": "--", "ec_60m": "--", "temp_60m": "--",
        "ph_1440m": "--", "ec_1440m": "--", "temp_1440m": "--",  # Added 1440m defaults
        "time": datetime.now().strftime("%H:%M:%S")
    }

    try:
        req = urllib.request.Request(LATEST)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode())

                if payload and len(payload) > 0:
                    last_row = payload[0]

                    data["ph"] = last_row.get("ph", "") or "--"
                    data["ph_60m"] = last_row.get("ph_avg_60m", "") or "--"
                    data["ph_1440m"] = last_row.get("ph_avg_1440m", "") or "--"  # Added

                    # Clean EC Live
                    ec_val = last_row.get("ec", "")
                    if ec_val:
                        try:
                            data["ec"] = str(int(float(ec_val)))
                        except ValueError:
                            data["ec"] = ec_val
                    else:
                        data["ec"] = "--"

                    # Clean EC Avg 60m
                    ec_avg_val = last_row.get("ec_avg_60m", "")
                    if ec_avg_val:
                        try:
                            data["ec_60m"] = str(int(float(ec_avg_val)))
                        except ValueError:
                            data["ec_60m"] = ec_avg_val
                    else:
                        data["ec_60m"] = "--"

                    # Clean EC Avg 1440m (Added)
                    ec_avg_1440_val = last_row.get("ec_avg_1440m", "")
                    if ec_avg_1440_val:
                        try:
                            data["ec_1440m"] = str(int(float(ec_avg_1440_val)))
                        except ValueError:
                            data["ec_1440m"] = ec_avg_1440_val
                    else:
                        data["ec_1440m"] = "--"

                    data["temp"] = last_row.get("temp", "") or "--"
                    data["temp_60m"] = last_row.get("temp_avg_60m", "") or "--"
                    data["temp_1440m"] = last_row.get("temp_avg_1440m", "") or "--"  # Added

                    timestamp = last_row.get("timestamp", "")
                    if timestamp and " " in timestamp:
                        data["time"] = timestamp.split(" ")[1]
    except Exception as e:
        print(f"FastAPI Offline or Error: {e}")

    return data

def MetricCard(title, value, unit, avg_60m, avg_1440m, status_color):
    color_map = {
        "pink": "bg-pink-500 shadow-[0_0_8px_rgba(236,72,153,0.8)]",
        "emerald": "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]",
        "cyan": "bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]"
    }
    dot_style = color_map.get(status_color, "bg-slate-500")

    return Div(
        # Header
        Div(
            Div(cls=f"w-2 h-2 rounded-full {dot_style} animate-pulse"),
            Div(title, cls="text-slate-400 text-xs font-semibold uppercase tracking-widest"),
            cls="flex items-center space-x-3 mb-4"
        ),
        # Main Live Value
        Div(
            Span(f"{value}", cls="text-4xl font-light text-slate-100 tracking-tight font-mono"),
            Span(f" {unit}", cls="text-sm text-slate-500 font-medium ml-1"),
            cls="flex items-baseline"
        ),
        # Footer / Stacked Averages
        Div(
            # 60m row
            Div(
                Span("60m Avg:", cls="text-slate-600"),
                Span(f"{avg_60m} {unit}", cls="text-slate-300 font-mono"),
                cls="flex justify-between w-full mb-1"
            ),
            # 24h (1440m) row
            Div(
                Span("24h Avg:", cls="text-slate-600"),
                Span(f"{avg_1440m} {unit}", cls="text-slate-500 font-mono text-[11px]"),
                cls="flex justify-between w-full"
            ),
            cls="text-xs mt-5 pt-4 border-t border-white/[0.05] flex flex-col"
        ),
        cls="bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-colors duration-300 rounded-2xl p-6 backdrop-blur-xl shadow-2xl"
    )

# Time series chart javascript
# We inject this script to independently poll the history endpoint and draw the grah
chart_js = Script("""
let telemetryChart;
let telemetryChart24h; // Added second chart instance

async function fetchChartData() {
    try {
        const apiHost = window.location.hostname;
        // Bumped limit to 100 to give the long-term graph more visual history (approx 8.3 hours)
        const res = await fetch(`http://${apiHost}:8000/api/v1/telemetry/history?limit=100`);
        const data = await res.json();

        const labels = data.map(d => {
            const timeParts = d.timestamp.split(' ');
            return timeParts.length > 1 ? timeParts[1] : d.timestamp;
        });

        // Live Data
        const phData = data.map(d => parseFloat(d.ph) || null);
        const ecData = data.map(d => parseFloat(d.ec) || null);
        const tempData = data.map(d => parseFloat(d.temp) || null);

        // 60m Averages
        const phAvgData = data.map(d => parseFloat(d.ph_avg_60m) || null);
        const ecAvgData = data.map(d => parseFloat(d.ec_avg_60m) || null);
        const tempAvgData = data.map(d => parseFloat(d.temp_avg_60m) || null);

        // 1440m (24h) Averages
        const phAvg1440Data = data.map(d => parseFloat(d.ph_avg_1440m) || null);
        const ecAvg1440Data = data.map(d => parseFloat(d.ec_avg_1440m) || null);
        const tempAvg1440Data = data.map(d => parseFloat(d.temp_avg_1440m) || null);

        // --- CHART 1: Live vs 60m ---
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

        // --- CHART 2: 60m vs 1440m ---
        if (!telemetryChart24h) {
            const ctx2 = document.getElementById('telemetryChart24h').getContext('2d');
            telemetryChart24h = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        // Using solid lines for 60m, dashed for the slower 24h trend
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
""")

@rt("/")
def get():
    data = get_sensor_data()
    return Titled("Hydroponics Telemetry",
                  Div(
                      # Header
                      Header(
                          H1("Hydroponics Telemetry", cls="text-2xl font-bold text-emerald-400"),
                          P("DATA DASHBOARD", cls="text-xs text-slate-400 font-mono"),
                          cls="mb-8 border-b border-slate-800 pb-4"
                      ),

                      # metrics w/ HTMX polling every 2 seconds
                      Div(
                          MetricCard("pH", data['ph'], "", data['ph_60m'], data['ph_1440m'], "pink"),
                          MetricCard("EC", data['ec'], "µS/cm", data['ec_60m'], data['ec_1440m'], "emerald"),
                          MetricCard("Temp", data['temp'], "°C", data['temp_60m'], data['temp_1440m'], "cyan"),
                          id="metrics-grid",
                          cls="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8",
                          hx_get="/update-metrics",
                          hx_trigger="every 2s"
                      ),

                      # Time series 1 (Live vs 60m)
                      Div(
                          Div(
                              H3("Short-Term Trends", cls="text-lg font-bold text-slate-200"),
                              P("Live data vs 60-minute rolling averages", cls="text-xs text-slate-400 mb-4"),
                          ),
                          # Canvas container
                          Div(Canvas(id="telemetryChart"), cls="w-full h-80 relative"),
                          cls="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8"
                      ),

                      # Time series 2 (60m vs 1440m)
                      Div(
                          Div(
                              H3("Long-Term Trends", cls="text-lg font-bold text-slate-200"),
                              P("60-minute vs 24-hour (1440m) rolling averages", cls="text-xs text-slate-400 mb-4"),
                          ),
                          # Canvas container
                          Div(Canvas(id="telemetryChart24h"), cls="w-full h-80 relative"),
                          cls="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8"
                      ),

                      chart_js,

                      cls="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#0a0a0a] to-black text-slate-100 p-4 md:p-8"
                  )
                  )

# --- Routes for HTMX Updates (Updates Top Cards Only) ---
@rt("/update-metrics")
def get():
    data = get_sensor_data()
    return (
        MetricCard("pH", data['ph'], "", data['ph_60m'], data['ph_1440m'], "pink"),
        MetricCard("EC", data['ec'], "µS/cm", data['ec_60m'], data['ec_1440m'], "emerald"),
        MetricCard("Temp", data['temp'], "°C", data['temp_60m'], data['temp_1440m'], "cyan")
    )

if __name__ == "__main__":
    serve(port=5001)