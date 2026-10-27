import os
import sys
import json
import pandas as pd

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.dashboard.data_access import load_data

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "netlify_dist")
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "index.html")


def build_static_dashboard():
    print("Loading dashboard dataset...")
    df = load_data()

    # Clean records for JSON serialization
    records = []
    for _, row in df.iterrows():
        price = float(row["price"]) if pd.notna(row.get("price")) else 0.0
        area = float(row["area"]) if pd.notna(row.get("area")) else 0.0
        year = int(row["year"]) if pd.notna(row.get("year")) else 2026
        listing_id = str(row.get("listing_id", "N/A"))
        prop_type = str(row.get("type", "Commercial")) if pd.notna(row.get("type")) else "Commercial"
        title = str(row.get("title", f"Property {listing_id}")) if pd.notna(row.get("title")) else f"Property {listing_id}"
        desc = str(row.get("description", "")) if pd.notna(row.get("description")) else ""

        records.append({
            "listing_id": listing_id,
            "price": round(price, 2),
            "area": round(area, 2),
            "type": prop_type,
            "year": year,
            "title": title,
            "description": desc
        })

    data_json = json.dumps(records)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Real Estate Market Monitor Dashboard</title>
    <!-- Cyborg Dark Theme (Bootswatch / Bootstrap 5) -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/cyborg/bootstrap.min.css" />
    <!-- Google Fonts: Outfit -->
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" />
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        body {{
            background-color: #0b0c10;
            color: #e0e0e0;
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        .dashboard-header h1 {{
            color: #00f2fe;
            font-weight: 800;
            letter-spacing: 2px;
            text-align: center;
            margin-top: 24px;
            text-shadow: 0 0 10px rgba(0, 242, 254, 0.5);
        }}
        .dashboard-header p {{
            color: #a2a2a2;
            text-align: center;
            font-size: 1.1rem;
            margin-bottom: 30px;
        }}
        .glass-card {{
            background: rgba(25, 25, 35, 0.78);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }}
        .glass-card .card-header {{
            background: transparent;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            color: #00f2fe;
            font-weight: 700;
            padding: 12px 18px;
        }}
        .kpi-title {{
            font-size: 0.75rem;
            letter-spacing: 1px;
            color: #9e9e9e;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .kpi-value {{
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 0;
        }}
        .type-pill {{
            cursor: pointer;
            user-select: none;
            padding: 6px 14px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.05);
            color: #aaa;
            font-size: 0.88rem;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .type-pill.active {{
            background: rgba(0, 242, 254, 0.18);
            border-color: #00f2fe;
            color: #fff;
            box-shadow: 0 0 8px rgba(0, 242, 254, 0.3);
        }}
        .type-dot {{
            width: 9px;
            height: 9px;
            border-radius: 50%;
            display: inline-block;
        }}
        .form-control-dark {{
            background-color: #15161e !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            color: #ffffff !important;
        }}
        .form-control-dark:focus {{
            border-color: #00f2fe !important;
            box-shadow: 0 0 0 0.2rem rgba(0, 242, 254, 0.2) !important;
        }}
        .chart-box {{
            min-height: 380px;
            width: 100%;
        }}
        .ticker-box {{
            min-height: 300px;
            width: 100%;
        }}
    </style>
</head>
<body>
    <div class="container-fluid px-4 pb-4">
        <!-- Header -->
        <div class="row">
            <div class="col-12 dashboard-header">
                <h1>REAL ESTATE MARKET MONITOR</h1>
                <p>Interactive Analytics &amp; Live Streaming Pipeline Dashboard</p>
            </div>
        </div>

        <!-- KPI Row -->
        <div class="row g-3 mb-4">
            <div class="col-md-3 col-sm-6">
                <div class="card glass-card h-100">
                    <div class="card-body">
                        <div class="kpi-title">Total Listings</div>
                        <h3 id="kpi-total-listings" class="kpi-value text-info">0</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3 col-sm-6">
                <div class="card glass-card h-100">
                    <div class="card-body">
                        <div class="kpi-title">Average Price</div>
                        <h3 id="kpi-avg-price" class="kpi-value text-primary">$0</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3 col-sm-6">
                <div class="card glass-card h-100">
                    <div class="card-body">
                        <div class="kpi-title">Average Area</div>
                        <h3 id="kpi-avg-area" class="kpi-value text-success">0 sqft</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3 col-sm-6">
                <div class="card glass-card h-100">
                    <div class="card-body">
                        <div class="kpi-title">Avg Price / Sqft</div>
                        <h3 id="kpi-avg-price-sqft" class="kpi-value text-warning">$0/sqft</h3>
                    </div>
                </div>
            </div>
        </div>

        <!-- Search & Filter Controls -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card glass-card">
                    <div class="card-header">Search &amp; Filter Controls</div>
                    <div class="card-body">
                        <div class="row g-3 align-items-center">
                            <!-- Property Type Multi-Select Pills -->
                            <div class="col-lg-5 col-md-12">
                                <label class="text-muted mb-2 d-block">Property Type:</label>
                                <div id="property-type-pills" class="d-flex flex-wrap gap-2"></div>
                            </div>

                            <!-- Year Range Controls -->
                            <div class="col-lg-3 col-md-6">
                                <label class="text-muted mb-2 d-block">
                                    Collection Year Range: <span id="year-range-label" class="text-info fw-bold"></span>
                                </label>
                                <div class="d-flex align-items-center gap-2">
                                    <input type="range" id="year-min" class="form-range" />
                                    <input type="range" id="year-max" class="form-range" />
                                </div>
                            </div>

                            <!-- Search Input -->
                            <div class="col-lg-4 col-md-6">
                                <label for="filter-search" class="text-muted mb-2 d-block">Search Listings (Title/Desc):</label>
                                <input
                                    type="text"
                                    id="filter-search"
                                    class="form-control form-control-dark"
                                    placeholder="Enter keyword (e.g. Office, Retail, warehouse, 2020)..."
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row 1 -->
        <div class="row g-4 mb-4">
            <div class="col-md-6 col-12">
                <div class="card glass-card h-100">
                    <div class="card-header">Top Listings by Price</div>
                    <div class="card-body">
                        <div id="chart-price-bar" class="chart-box"></div>
                    </div>
                </div>
            </div>
            <div class="col-md-6 col-12">
                <div class="card glass-card h-100">
                    <div class="card-header">Market Composition by Property Type</div>
                    <div class="card-body">
                        <div id="chart-type-pie" class="chart-box"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row 2 -->
        <div class="row g-4 mb-4">
            <div class="col-md-6 col-12">
                <div class="card glass-card h-100">
                    <div class="card-header">Price Distribution by Property Type</div>
                    <div class="card-body">
                        <div id="chart-price-violin" class="chart-box"></div>
                    </div>
                </div>
            </div>
            <div class="col-md-6 col-12">
                <div class="card glass-card h-100">
                    <div class="card-header">Property Area (sqft) Distribution</div>
                    <div class="card-body">
                        <div id="chart-area-hist" class="chart-box"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Live Streaming Ticker -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card glass-card">
                    <div class="card-header">
                        <span style="color: #ff007f; font-weight: bold;">🔴 Live Real-Time Property Price Stream</span>
                        <span class="text-muted" style="font-size: 0.85rem;"> (Updates every 3 seconds)</span>
                    </div>
                    <div class="card-body">
                        <div id="chart-live-ticker" class="ticker-box"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="row">
            <div class="col-12">
                <hr style="border-color: rgba(255,255,255,0.1);" />
                <p class="text-muted text-center mb-2" style="font-size: 0.9rem;">
                    &copy; 2026 Real Estate Market Monitor. Built with Plotly &amp; Bootstrap Cyborg.
                </p>
            </div>
        </div>
    </div>

    <script>
        const ALL_DATA = {data_json};

        const COLOR_MAP = {{
            "Multi-Family": "#00f2fe",
            "Retail": "#ff007f",
            "Office": "#39ff14",
            "Industrial": "#ffaa00",
            "Commercial": "#a855f7"
        }};

        // Extract unique types & years
        const allTypes = Array.from(new Set(ALL_DATA.map(d => d.type))).sort();
        const selectedTypes = new Set(allTypes);

        const years = ALL_DATA.map(d => d.year);
        const rawMinYr = Math.min(...years);
        const rawMaxYr = Math.max(...years);
        const sliderMin = rawMinYr === rawMaxYr ? rawMinYr - 5 : rawMinYr;
        const sliderMax = rawMaxYr;

        // Initialize Year Sliders
        const yearMinInput = document.getElementById("year-min");
        const yearMaxInput = document.getElementById("year-max");
        const yearLabel = document.getElementById("year-range-label");

        yearMinInput.min = sliderMin;
        yearMinInput.max = sliderMax;
        yearMinInput.value = rawMinYr;

        yearMaxInput.min = sliderMin;
        yearMaxInput.max = sliderMax;
        yearMaxInput.value = rawMaxYr;

        function updateYearLabel() {{
            const low = Math.min(Number(yearMinInput.value), Number(yearMaxInput.value));
            const high = Math.max(Number(yearMinInput.value), Number(yearMaxInput.value));
            yearLabel.textContent = `${{low}} - ${{high}}`;
        }}
        updateYearLabel();

        // Initialize Property Type Pills
        const pillsContainer = document.getElementById("property-type-pills");
        allTypes.forEach(type => {{
            const pill = document.createElement("div");
            pill.className = "type-pill active";
            const dotColor = COLOR_MAP[type] || "#00f2fe";
            pill.innerHTML = `<span class="type-dot" style="background:${{dotColor}}"></span><span>${{type}}</span>`;
            pill.addEventListener("click", () => {{
                if (selectedTypes.has(type)) {{
                    selectedTypes.delete(type);
                    pill.classList.remove("active");
                }} else {{
                    selectedTypes.add(type);
                    pill.classList.add("active");
                }}
                renderDashboard();
            }});
            pillsContainer.appendChild(pill);
        }});

        yearMinInput.addEventListener("input", () => {{ updateYearLabel(); renderDashboard(); }});
        yearMaxInput.addEventListener("input", () => {{ updateYearLabel(); renderDashboard(); }});
        document.getElementById("filter-search").addEventListener("input", () => renderDashboard());

        function getFilteredData() {{
            const lowYr = Math.min(Number(yearMinInput.value), Number(yearMaxInput.value));
            const highYr = Math.max(Number(yearMinInput.value), Number(yearMaxInput.value));
            const query = document.getElementById("filter-search").value.trim().toLowerCase();

            return ALL_DATA.filter(d => {{
                if (!selectedTypes.has(d.type)) return false;
                if (d.year < lowYr || d.year > highYr) return false;
                if (query) {{
                    const hay = `${{d.title}} ${{d.description}} ${{d.listing_id}} ${{d.type}}`.toLowerCase();
                    if (!hay.includes(query)) return false;
                }}
                return true;
            }});
        }}

        function renderEmptyChart(divId, message) {{
            Plotly.react(divId, [], {{
                template: "plotly_dark",
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                xaxis: {{ showgrid: false, zeroline: false, showticklabels: false }},
                yaxis: {{ showgrid: false, zeroline: false, showticklabels: false }},
                annotations: [{{
                    text: message,
                    xref: "paper",
                    yref: "paper",
                    x: 0.5,
                    y: 0.5,
                    showarrow: false,
                    font: {{ size: 16, color: "#a2a2a2" }}
                }}]
            }}, {{ responsive: true }});
        }}

        function renderDashboard() {{
            const filtered = getFilteredData();
            const n = filtered.length;

            // 1. Update KPIs
            document.getElementById("kpi-total-listings").textContent = n.toLocaleString();
            if (n > 0) {{
                const avgPrice = filtered.reduce((acc, r) => acc + r.price, 0) / n;
                const avgArea = filtered.reduce((acc, r) => acc + r.area, 0) / n;
                const validSqft = filtered.filter(r => r.area > 0 && r.price > 0);
                const avgPriceSqft = validSqft.length > 0
                    ? validSqft.reduce((acc, r) => acc + (r.price / r.area), 0) / validSqft.length
                    : 0;

                document.getElementById("kpi-avg-price").textContent = "$" + Math.round(avgPrice).toLocaleString();
                document.getElementById("kpi-avg-area").textContent = Math.round(avgArea).toLocaleString() + " sqft";
                document.getElementById("kpi-avg-price-sqft").textContent = "$" + avgPriceSqft.toFixed(2) + "/sqft";
            }} else {{
                document.getElementById("kpi-avg-price").textContent = "$0";
                document.getElementById("kpi-avg-area").textContent = "0 sqft";
                document.getElementById("kpi-avg-price-sqft").textContent = "$0/sqft";
            }}

            if (n === 0) {{
                renderEmptyChart("chart-price-bar", "No matching property listings found.");
                renderEmptyChart("chart-type-pie", "No matching property listings found.");
                renderEmptyChart("chart-price-violin", "No matching property listings found.");
                renderEmptyChart("chart-area-hist", "No matching property listings found.");
                return;
            }}

            // 2. Top 10 Listings by Price (Horizontal Bar)
            const top10 = [...filtered]
                .sort((a, b) => b.price - a.price)
                .slice(0, 10)
                .reverse();

            const barTraces = [];
            const top10Types = Array.from(new Set(top10.map(d => d.type)));
            top10Types.forEach(t => {{
                const sub = top10.filter(d => d.type === t);
                barTraces.push({{
                    type: "bar",
                    orientation: "h",
                    name: t,
                    x: sub.map(d => d.price),
                    y: sub.map(d => d.title || `Property ${{d.listing_id}}`),
                    marker: {{ color: COLOR_MAP[t] || "#00f2fe" }},
                    customdata: sub.map(d => [d.area, d.listing_id]),
                    hovertemplate: "<b>%{{y}}</b><br>Price: $%{{x:,.0f}}<br>Area: %{{customdata[0]:,.0f}} sqft<br>ID: %{{customdata[1]}}<extra></extra>"
                }});
            }});

            Plotly.react("chart-price-bar", barTraces, {{
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                font: {{ color: "#e0e0e0", family: "Outfit, sans-serif" }},
                margin: {{ l: 150, r: 20, t: 30, b: 40 }},
                xaxis: {{ title: "Price (USD)", gridcolor: "rgba(255,255,255,0.05)", tickformat: "$,.0f" }},
                yaxis: {{ title: "", categoryorder: "array", categoryarray: top10.map(d => d.title || `Property ${{d.listing_id}}`) }},
                legend: {{ orientation: "h", yanchor: "bottom", y: 1.02, xanchor: "right", x: 1 }}
            }}, {{ responsive: true }});

            // 3. Market Composition Pie Chart
            const typeCounts = {{}};
            filtered.forEach(d => {{ typeCounts[d.type] = (typeCounts[d.type] || 0) + 1; }});
            const pieLabels = Object.keys(typeCounts);
            const pieValues = pieLabels.map(k => typeCounts[k]);

            Plotly.react("chart-type-pie", [{{
                type: "pie",
                labels: pieLabels,
                values: pieValues,
                hole: 0.4,
                pull: pieLabels.map(() => 0.04),
                textinfo: "percent+label",
                marker: {{ colors: pieLabels.map(t => COLOR_MAP[t] || "#00f2fe") }}
            }}], {{
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                font: {{ color: "#e0e0e0", family: "Outfit, sans-serif" }},
                margin: {{ l: 20, r: 20, t: 20, b: 20 }},
                legend: {{ orientation: "h", yanchor: "bottom", y: -0.1, xanchor: "center", x: 0.5 }}
            }}, {{ responsive: true }});

            // 4. Price Distribution Violin Plot
            const violinTraces = pieLabels.map(t => {{
                const sub = filtered.filter(d => d.type === t);
                return {{
                    type: "violin",
                    name: t,
                    x: sub.map(d => d.type),
                    y: sub.map(d => d.price),
                    box: {{ visible: true }},
                    meanline: {{ visible: true }},
                    points: "all",
                    line: {{ color: COLOR_MAP[t] || "#00f2fe" }},
                    customdata: sub.map(d => [d.listing_id, d.area]),
                    hovertemplate: "Type: %{{x}}<br>Price: $%{{y:,.0f}}<br>ID: %{{customdata[0]}}<br>Area: %{{customdata[1]:,.0f}} sqft<extra></extra>"
                }};
            }});

            Plotly.react("chart-price-violin", violinTraces, {{
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                font: {{ color: "#e0e0e0", family: "Outfit, sans-serif" }},
                margin: {{ l: 55, r: 20, t: 20, b: 40 }},
                xaxis: {{ title: "Property Type" }},
                yaxis: {{ title: "Price (USD)", gridcolor: "rgba(255,255,255,0.05)", tickformat: "$,.0f" }},
                showlegend: false
            }}, {{ responsive: true }});

            // 5. Property Area Distribution Histogram
            const histTraces = pieLabels.map(t => {{
                const sub = filtered.filter(d => d.type === t);
                return {{
                    type: "histogram",
                    name: t,
                    x: sub.map(d => d.area),
                    marker: {{ color: COLOR_MAP[t] || "#00f2fe" }},
                    opacity: 0.78
                }};
            }});

            Plotly.react("chart-area-hist", histTraces, {{
                barmode: "stack",
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                font: {{ color: "#e0e0e0", family: "Outfit, sans-serif" }},
                margin: {{ l: 50, r: 20, t: 30, b: 40 }},
                xaxis: {{ title: "Area (sqft)", gridcolor: "rgba(255,255,255,0.05)" }},
                yaxis: {{ title: "Count", gridcolor: "rgba(255,255,255,0.05)" }},
                legend: {{ orientation: "h", yanchor: "bottom", y: 1.02, xanchor: "right", x: 1 }}
            }}, {{ responsive: true }});
        }}

        // 6. Live Streaming Ticker (3-second interval)
        const tickerTimestamps = [];
        const tickerPrices = [];
        const now = Date.now();
        for (let i = 0; i < 20; i++) {{
            tickerTimestamps.push(new Date(now - (20 - i) * 3000));
            tickerPrices.push(Math.floor(250000 + Math.random() * 1250000));
        }}

        function renderTicker() {{
            Plotly.react("chart-live-ticker", [{{
                type: "scatter",
                mode: "lines+markers",
                x: tickerTimestamps.map(d => d.toTimeString().split(" ")[0]),
                y: tickerPrices,
                line: {{ color: "#ff007f", width: 2 }},
                marker: {{ size: 8, color: "#ff007f" }},
                name: "Live Transaction Price",
                hovertemplate: "Time: %{{x}}<br>Price: $%{{y:,.0f}}<extra></extra>"
            }}], {{
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                font: {{ color: "#e0e0e0", family: "Outfit, sans-serif" }},
                margin: {{ l: 60, r: 20, t: 10, b: 40 }},
                xaxis: {{ gridcolor: "rgba(255,255,255,0.05)", title: "Time" }},
                yaxis: {{ title: "Transaction Price (USD)", gridcolor: "rgba(255,255,255,0.05)", tickformat: "$,.0f" }},
                height: 300
            }}, {{ responsive: true }});
        }}

        setInterval(() => {{
            const lastPrice = tickerPrices[tickerPrices.length - 1];
            const delta = Math.floor(Math.random() * 85001) - 40000;
            const nextPrice = Math.max(100000, lastPrice + delta);
            tickerTimestamps.push(new Date());
            tickerPrices.push(nextPrice);
            if (tickerTimestamps.length > 20) {{
                tickerTimestamps.shift();
                tickerPrices.shift();
            }}
            renderTicker();
        }}, 3000);

        // Initial Render
        renderDashboard();
        renderTicker();
    </script>
</body>
</html>
"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Static Netlify dashboard successfully generated at: {OUTPUT_HTML}")
    print(f"Embedded {len(records)} property records.")


if __name__ == "__main__":
    build_static_dashboard()
