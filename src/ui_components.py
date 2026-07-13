# src/components.py

# ui components file for fasthtml - keeps our code clear of big blocks of htmx
from fasthtml.common import *

def MetricCard(title, value, unit, avg_60m, avg_1440m, status_color):

    color_map = {
        "pink": "bg-pink-500 shadow-[0_0_8px_rgba(236,72,153,0.8)]",
        "emerald": "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]",
        "cyan": "bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.8)]"
    }
    dot_style = color_map.get(status_color, "bg-slate-500")

    return Div(
        # hdr
        Div(
            Div(cls=f"w-2 h-2 rounded-full {dot_style} animate-pulse"),
            Div(title, cls="text-slate-400 text-xs font-semibold uppercase tracking-widest"),
            cls="flex items-center space-x-3 mb-4"
        ),
        # body
        Div(
            Span(f"{value}", cls="text-4xl font-light text-slate-100 tracking-tight font-mono"),
            Span(f" {unit}", cls="text-sm text-slate-500 font-medium ml-1"),
            cls="flex items-baseline"
        ),
        # footer with stacked averages
        Div(
            # 1h row
            Div(
                Span("60m Avg:", cls="text-slate-600"),
                Span(f"{avg_60m} {unit}", cls="text-slate-300 font-mono"),
                cls="flex justify-between w-full mb-1"
            ),
            # 24h row
            Div(
                Span("24h Avg:", cls="text-slate-600"),
                Span(f"{avg_1440m} {unit}", cls="text-slate-500 font-mono text-[11px]"),
                cls="flex justify-between w-full"
            ),
            cls="text-xs mt-5 pt-4 border-t border-white/[0.05] flex flex-col"
        ),
        cls="bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-colors duration-300 rounded-2xl p-6 backdrop-blur-xl shadow-2xl"
    )


def DashboardHeader():
    return Header(
        Div(
            # Left side: Titles
            Div(
                H1("Hydroponics Telemetry", cls="text-2xl font-bold text-emerald-400"),
                P("DATA DASHBOARD", cls="text-xs text-slate-400 font-mono"),
            ),

            A(
                "📥 Download Crop Data (ZIP)",
                href="http://localhost:8000/api/v1/telemetry/export",
                download="true",
                cls="px-4 py-2 bg-slate-800 hover:bg-emerald-900 hover:text-emerald-400 text-slate-300 text-sm font-semibold rounded-lg border border-slate-700 hover:border-emerald-700 transition-all duration-300 shadow-lg"
            ),
            cls="flex justify-between items-center w-full"
        ),
        cls="mb-8 border-b border-slate-800 pb-4"
    )

def ChartCard(title, subtitle, canvas_id):
    return Div(
        Div(
            H3(title, cls="text-lg font-bold text-slate-200"),
            P(subtitle, cls="text-xs text-slate-400 mb-4"),
        ),
        Div(Canvas(id=canvas_id), cls="w-full h-80 relative"),
        cls="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8"
    )

def MetricsGroup(data):

    return (
        MetricCard("pH", data['ph'], "", data['ph_60m'], data['ph_1440m'], "pink"),
        MetricCard("EC", data['ec'], "µS/cm", data['ec_60m'], data['ec_1440m'], "emerald"),
        MetricCard("Temp", data['temp'], "°C", data['temp_60m'], data['temp_1440m'], "cyan")
    )

#master wrapper
def MainDashboard(data):

    return Titled("Hydroponics Telemetry",
                  Div(
                      DashboardHeader(),

                      # The HTMX Polling Grid
                      Div(
                          *MetricsGroup(data),
                          id="metrics-grid",
                          cls="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8",
                          hx_get="/update-metrics",
                          hx_trigger="every 2s"
                      ),

                      # The Chart Containers
                      ChartCard("Short-Term Trends", "Live data vs 60-minute rolling averages", "telemetryChart"),
                      ChartCard("Long-Term Trends", "60-minute vs 24-hour (1440m) rolling averages",
                                "telemetryChart24h"),

                      Script(src="/charts.js"),
                      cls="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#0a0a0a] to-black text-slate-100 p-4 md:p-8"
                  )
                  )
