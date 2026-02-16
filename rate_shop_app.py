import streamlit as st
import pandas as pd
import altair as alt
from google.cloud import bigquery
from datetime import datetime
import calendar

# --------------------------
# PAGE CONFIG & STYLING
# --------------------------

st.set_page_config(
    page_title="Golf Rate Shop Dashboard",
    page_icon="🏌️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Advanced custom CSS styling
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    .main {
        background: transparent;
        padding: 20px;
    }
    
    .stTitle {
        color: #fff !important;
        font-size: 2.5em !important;
        margin-bottom: 10px;
    }
    
    /* Calendar Grid Styling */
    .calendar-container {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 12px;
        margin: 30px 0;
    }
    
    .calendar-tile {
        aspect-ratio: 1;
        border-radius: 16px;
        padding: 12px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        border: 2px solid rgba(255,255,255,0.1);
        cursor: pointer;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(10px);
        font-weight: 600;
    }
    
    .calendar-tile:hover {
        transform: translateY(-8px) scale(1.05);
        border-color: rgba(255,255,255,0.3);
        box-shadow: 0 12px 40px rgba(255,255,255,0.1);
    }
    
    .tile-day {
        font-size: 0.9em;
        opacity: 0.9;
        margin-bottom: 4px;
    }
    
    .tile-price {
        font-size: 1.8em;
        margin: 4px 0;
        font-weight: 700;
    }
    
    .tile-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 0.75em;
        font-weight: 600;
        margin-bottom: 4px;
    }
    
    .tile-occ {
        font-size: 0.85em;
        opacity: 0.85;
    }
    
    /* Modal Overlay */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(4px);
        z-index: 9998;
        display: flex;
        justify-content: center;
        align-items: center;
        animation: fadeIn 0.3s ease-in-out;
    }
    
    .modal-content {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 20px;
        padding: 40px;
        width: 90%;
        max-width: 650px;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        position: relative;
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 2px solid #e0e0e0;
    }
    
    .modal-title {
        font-size: 1.8em;
        font-weight: 700;
        color: #1a1a2e;
    }
    
    .modal-close {
        background: #ff4757;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        font-size: 1.2em;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .modal-close:hover {
        background: #ff3838;
        transform: scale(1.1);
    }
    
    .price-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }
    
    .price-label {
        font-size: 0.95em;
        opacity: 0.9;
        margin-bottom: 8px;
    }
    
    .price-value {
        font-size: 2.5em;
        font-weight: 700;
    }
    
    .market-range {
        background: #f0f0f5;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
        border-left: 4px solid #667eea;
    }
    
    .market-range-label {
        font-size: 0.95em;
        font-weight: 600;
        color: #666;
        margin-bottom: 10px;
    }
    
    .market-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
    }
    
    .stat-box {
        background: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
    }
    
    .stat-label {
        font-size: 0.8em;
        color: #999;
        font-weight: 500;
    }
    
    .stat-value {
        font-size: 1.4em;
        font-weight: 700;
        color: #1a1a2e;
        margin-top: 4px;
    }
    
    .competitors-section h3 {
        color: #1a1a2e;
        margin-bottom: 15px;
        font-size: 1.2em;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    @keyframes slideUp {
        from {
            transform: translateY(30px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .calendar-tile {
            aspect-ratio: auto;
            min-height: 80px;
        }
        
        .modal-content {
            width: 95%;
            padding: 20px;
        }
        
        .market-stats {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

# --------------------------
# CONFIG
# --------------------------

PROJECT_ID = "tee-metrics-golf-tee-time"
TABLE_ID = "RateShop Query"

st.set_page_config(layout="wide")

def get_bq_client():
    """Returns a BigQuery client using Streamlit secrets."""
    from google.oauth2 import service_account
    
    # This works for both local .streamlit/secrets.toml AND Streamlit Cloud Secrets
    credentials_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    
    return bigquery.Client(credentials=credentials, project=credentials_info["project_id"])



# --------------------------
# LOAD DATA
# --------------------------

# @st.cache_data(ttl=120)
@st.cache_data
def load_data():
    try:
        # client = bigquery.Client.from_service_account_json(
        #     "golf_credential.json"
        # )

        # Then in your load_data() function:
        client = get_bq_client()


        query = f"""
            WITH normalized AS (
            SELECT
                CASE
                WHEN course_name IN ('thorntree_golf_club','thorntree_country_club')
                    THEN 'thorntree_golf_club'
                WHEN course_name IN (
                    'riverside_golf_club_-_dallas',
                    'riverside_golf_club',
                    'riverside_g.c.'
                ) THEN 'riverside_golf_club_dallas'
                WHEN course_name IN (
                    'bear_creek',
                    'bear_creek_golf_club_-_west',
                    'bear_creek_golf_club_-_west_course'
                ) THEN 'bear_creek_golf_club_west'
                ELSE course_name
                END AS course_name,
                source_channel,
                scrape_timestamp,
                tee_date,
                tee_time,
                price
            FROM `tee-metrics-golf-tee-time.golf_silver.tee_time_clean`
            WHERE tee_date >= '2026-02-03'
            ),

            daily_last_scrape AS (
            SELECT
                course_name,
                source_channel,
                tee_date,
                MAX(scrape_timestamp) AS last_scrape_of_day
            FROM normalized
            GROUP BY course_name, source_channel, tee_date
            ),

            slot_lifecycle AS (
            SELECT
                n.course_name,
                n.source_channel,
                n.tee_date,
                n.tee_time,
                MIN(n.scrape_timestamp) AS first_seen_at,
                MAX(n.scrape_timestamp) AS last_seen_at,
                COUNT(DISTINCT n.scrape_timestamp) AS scrape_count,
                AVG(n.price) AS avg_slot_price,
                MIN(n.price) AS min_slot_price,
                MAX(n.price) AS max_slot_price
            FROM normalized n
            GROUP BY
                n.course_name,
                n.source_channel,
                n.tee_date,
                n.tee_time
            ),

            occupancy_labeled AS (
            SELECT
                s.*,
                d.last_scrape_of_day,
                CASE
                WHEN s.last_seen_at < d.last_scrape_of_day THEN 'OCCUPIED'
                ELSE 'STILL_AVAILABLE'
                END AS occupancy_status,
                TIMESTAMP_DIFF(
                s.last_seen_at,
                s.first_seen_at,
                MINUTE
                ) AS minutes_available
            FROM slot_lifecycle s
            JOIN daily_last_scrape d
                ON s.course_name = d.course_name
            AND s.source_channel = d.source_channel
            AND s.tee_date = d.tee_date
            ),

            daily_course_summary AS (
            SELECT
                course_name,
                source_channel,
                tee_date,

                COUNT(*) AS total_slots,
                SUM(IF(occupancy_status = 'OCCUPIED', 1, 0)) AS occupied_slots,

                ROUND(
                100 * SAFE_DIVIDE(
                    SUM(IF(occupancy_status = 'OCCUPIED', 1, 0)),
                    COUNT(*)
                ),
                2
                ) AS occupancy_percent,

                ROUND(AVG(minutes_available), 1) AS avg_minutes_available,
                ROUND(AVG(avg_slot_price), 2) AS average_price,

                MIN(min_slot_price) AS min_price,
                MAX(max_slot_price) AS max_price

            FROM occupancy_labeled
            GROUP BY course_name, source_channel, tee_date
            ),

            market_summary AS (
            SELECT
                tee_date,
                MIN(average_price) AS market_min_price,
                AVG(average_price) AS market_avg_price,
                MAX(average_price) AS market_max_price
            FROM daily_course_summary
            GROUP BY tee_date
            )

            SELECT
            d.*,

            m.market_min_price,
            ROUND(m.market_avg_price, 2) AS market_avg_price,
            m.market_max_price,

            ROUND(
                SAFE_DIVIDE(
                d.average_price - m.market_avg_price,
                m.market_avg_price
                ) * 100,
                2
            ) AS price_gap_percent,

            CASE
                WHEN d.average_price >= m.market_max_price THEN 'HIGHEST_IN_MARKET'
                WHEN d.average_price <= m.market_min_price THEN 'LOWEST_IN_MARKET'
                WHEN d.average_price < m.market_avg_price THEN 'BELOW_AVERAGE'
                WHEN d.average_price = m.market_avg_price THEN 'MARKET_AVERAGE'
                ELSE 'ABOVE_AVERAGE'
            END AS price_position_flag,

            CASE
                WHEN d.occupancy_percent >= 90 THEN 'HIGH_DEMAND'
                WHEN d.occupancy_percent >= 60 THEN 'MEDIUM_DEMAND'
                ELSE 'LOW_DEMAND'
            END AS demand_pressure,

            ROUND(
                SAFE_DIVIDE(d.occupancy_percent, d.average_price),
                4
            ) AS revenue_efficiency_score

            FROM daily_course_summary d
            JOIN market_summary m
            USING (tee_date)

            ORDER BY tee_date, course_name;
        """
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("No data available. Please check your credentials.")
    st.stop()

# --------------------------
# INITIALIZE SESSION STATE
# --------------------------

if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

if "tile_modal_date" not in st.session_state:
    st.session_state.tile_modal_date = None

# --------------------------
# SIDEBAR CONTROLS
# --------------------------

with st.sidebar:
    st.markdown("### ⚙️ Controls")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    courses = sorted(df["course_name"].unique())
    selected_course = st.selectbox(
        "Select Your Course",
        courses,
        index=courses.index("coyote_ridge_golf_club") if "coyote_ridge_golf_club" in courses else 0
    )
    
    # Month and Year selection
    col1, col2 = st.columns(2)
    with col1:
        selected_month_num = st.selectbox(
            "Month",
            range(1, 13),
            index=1,  # February
            format_func=lambda x: datetime(2026, x, 1).strftime('%B')
        )
    with col2:
        selected_year = st.selectbox(
            "Year",
            range(2024, 2031),
            index=2  # 2026
        )
    
    selected_month = datetime(selected_year, selected_month_num, 1)

# --------------------------
# DATA FILTERING
# --------------------------

df["tee_date"] = pd.to_datetime(df["tee_date"])
year = selected_month.year
month = selected_month.month

month_df = df[
    (df["tee_date"].dt.month == month) &
    (df["tee_date"].dt.year == year)
]

# Select a single, consistent row per date for the chosen course
# Prioritize brand channel, otherwise take lowest price
my_df_raw = month_df[month_df["course_name"] == selected_course]

# # Debug: Show what we're working with
# if not my_df_raw.empty and selected_course == "coyote_ridge_golf_club":
#     st.sidebar.write("**Debug Info:**")
#     debug_date = pd.Timestamp("2026-02-13")
#     if debug_date in my_df_raw["tee_date"].values:
#         debug_rows = my_df_raw[my_df_raw["tee_date"] == debug_date][["tee_date", "source_channel", "average_price", "price_position_flag"]]
#         st.sidebar.dataframe(debug_rows, hide_index=True)

my_df = (
    my_df_raw
    .assign(channel_priority=lambda x: x["source_channel"].map({"brand": 0}).fillna(1))
    .sort_values(["tee_date", "channel_priority", "average_price", "source_channel"])
    .groupby("tee_date", as_index=False)
    .first()
    .drop(columns=["channel_priority"])
)

# --------------------------
# COLOR & STYLING FUNCTIONS
# --------------------------

def get_color(flag):
    # Flag color mapping used by the UI. Keep this constant near the color helper
    # so contributors can quickly see which flag maps to which color.
    FLAG_COLORS = {
        "LOWEST_IN_MARKET": "#10b981",
        "BELOW_AVERAGE": "#06b6d4",
        "MARKET_AVERAGE": "#f59e0b",
        "ABOVE_AVERAGE": "#f97316",
        "HIGHEST_IN_MARKET": "#ef4444",
    }

    return FLAG_COLORS.get(flag, "#6b7280")

def get_demand_opacity(occupancy):
    """Returns opacity based on demand intensity"""
    if occupancy >= 90:
        return 1.0
    elif occupancy >= 70:
        return 0.85
    elif occupancy >= 50:
        return 0.7
    elif occupancy >= 30:
        return 0.55
    else:
        return 0.4

def get_sell_speed_icon(minutes_available):
    """Returns icon based on how quickly slots are selling"""
    if minutes_available is None or minutes_available < 0:
        return "❄️"
    elif minutes_available >= 240:
        return "🐢"
    elif minutes_available >= 60:
        return "⚡"
    else:
        return "🔥"

# --------------------------
# PAGE HEADER
# --------------------------

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"# 🏌️ Golf Rate Shop")
    st.markdown(f"**{selected_month.strftime('%B %Y')}** • Course: **{selected_course.replace('_', ' ').title()}**")
    # Quick visual legend for price-position flags
    st.markdown(
            """
            <div style='display:flex; gap:12px; align-items:center; margin-top:8px;'>
                <div style='display:flex; gap:8px; align-items:center;'>
                    <span style='width:12px; height:12px; background:#10b981; display:inline-block; border-radius:3px;'></span>
                    <span style='color:#fff; opacity:0.9;'>LOWEST_IN_MARKET</span>
                </div>
                <div style='display:flex; gap:8px; align-items:center;'>
                    <span style='width:12px; height:12px; background:#06b6d4; display:inline-block; border-radius:3px;'></span>
                    <span style='color:#fff; opacity:0.9;'>BELOW_AVERAGE</span>
                </div>
                <div style='display:flex; gap:8px; align-items:center;'>
                    <span style='width:12px; height:12px; background:#f59e0b; display:inline-block; border-radius:3px;'></span>
                    <span style='color:#fff; opacity:0.9;'>MARKET_AVERAGE</span>
                </div>
                <div style='display:flex; gap:8px; align-items:center;'>
                    <span style='width:12px; height:12px; background:#f97316; display:inline-block; border-radius:3px;'></span>
                    <span style='color:#fff; opacity:0.9;'>ABOVE_AVERAGE</span>
                </div>
                <div style='display:flex; gap:8px; align-items:center;'>
                    <span style='width:12px; height:12px; background:#ef4444; display:inline-block; border-radius:3px;'></span>
                    <span style='color:#fff; opacity:0.9;'>HIGHEST_IN_MARKET</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
    )
# with col2:
#     st.metric(
#         "Available Days",
#         len(my_df)
#     )

st.markdown("---")

# --------------------------
# CALENDAR GRID
# --------------------------

cal = calendar.monthcalendar(year, month)

# Day headers
day_cols = st.columns(7)
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
for i, day in enumerate(days):
    with day_cols[i]:
        st.markdown(f"<p style='text-align:center; color:#999; font-weight:600; font-size:0.9em;'>{day}</p>", unsafe_allow_html=True)

# Calendar tiles
for week in cal:
    cols = st.columns(7, gap="small")
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.empty()
            else:
                day_date = datetime(year, month, day)
                row = my_df[my_df["tee_date"] == pd.Timestamp(day_date)]

                if not row.empty:
                    try:
                        price = row["average_price"].values[0]
                        flag = row["price_position_flag"].values[0]
                        occupancy = row["occupancy_percent"].values[0]
                        gap = row["price_gap_percent"].values[0]
                        minutes_available = row["avg_minutes_available"].values[0]
                        market_avg = row["market_avg_price"].values[0]

                        color = get_color(flag)
                        icon = get_sell_speed_icon(minutes_available)
                        gap_color = "#10b981" if gap < 0 else "#ef4444"

                        badge_style = f"""
                            background:{gap_color};
                            color:white;
                            padding:3px 8px;
                            border-radius:6px;
                            font-size:0.7em;
                            font-weight:700;
                        """

                        tile_html = f"""
                            <div style="
                                background-color:{color};
                                padding:14px;
                                border-radius:14px;
                                text-align:center;
                                transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
                                cursor:pointer;
                                border: 2px solid rgba(255,255,255,0.1);
                                min-height:100px;
                                display:flex;
                                flex-direction:column;
                                justify-content:center;
                                align-items:center;
                                color:white;
                            "
                            onmouseover="this.style.transform='translateY(-6px) scale(1.05)'; this.style.boxShadow='0 12px 30px rgba(0,0,0,0.3)'"
                            onmouseout="this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='none'"
                            title="Market Avg: ${market_avg:.0f} | Gap: {gap:.1f}%"
                            >
                                <div style="font-size:0.85em; opacity:0.9; margin-bottom:4px; font-weight:600;">{day}</div>
                                <div style="font-size:1.6em; margin:6px 0; font-weight:700;">${price:.0f}</div>
                                <div style="{badge_style}">{gap:+.1f}%</div>
                                <div style="font-size:0.8em; margin-top:6px; opacity:0.85;">{occupancy:.0f}% {icon}</div>
                            </div>
                        """
                        st.markdown(tile_html, unsafe_allow_html=True)

                        # Add clickable button for tile modal with distinct label
                        if st.button("📊 Analytics", key=f"tile_open_{day}", use_container_width=True):
                            st.session_state.tile_modal_date = day_date

                        if st.button("View Details", key=f"btn_{day}", use_container_width=True):
                            st.session_state.selected_date = day_date
                    except Exception as e:
                        st.warning(f"Error rendering day {day}: {str(e)}")
                else:
                    st.empty()

# ================================
# NEW TILE POPUP MODAL
# ================================

@st.dialog("📊 Rate Shop Analytics", width="large")
def show_tile_modal(selected_date, selected_course, month_df):
    """Display analytics modal for selected date"""
    
    # Tabs
    tab1, tab2 = st.tabs(["📊 Summary", "📈 RateShop History Chart"])
    
    # TAB 1: SUMMARY
    with tab1:
        day_df = month_df[
            month_df["tee_date"] == pd.Timestamp(selected_date)
        ]

        my_row = day_df[
            day_df["course_name"] == selected_course
        ].iloc[0] if len(day_df[day_df["course_name"] == selected_course]) > 0 else None

        if my_row is not None:
            my_price = my_row["average_price"]
            total_slots = my_row["total_slots"]
            occupied_slots = my_row["occupied_slots"]
            available_slots = total_slots - occupied_slots

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("My Price", f"${my_price:.0f}")
            
            # Initialize filter state
            if f"slot_filter_{selected_date.strftime('%Y%m%d')}" not in st.session_state:
                st.session_state[f"slot_filter_{selected_date.strftime('%Y%m%d')}"] = "all"
            
            # Clickable metric-style buttons for filtering
            with m2:
                if st.button(f"**Total Slots**\n\n## {int(total_slots)}", key=f"total_{selected_date.strftime('%Y%m%d')}", use_container_width=True):
                    st.session_state[f"slot_filter_{selected_date.strftime('%Y%m%d')}"] = "all"
            
            with m3:
                if st.button(f"**Occupied Slots**\n\n## {int(occupied_slots)}", key=f"occupied_{selected_date.strftime('%Y%m%d')}", use_container_width=True):
                    st.session_state[f"slot_filter_{selected_date.strftime('%Y%m%d')}"] = "occupied"
            
            with m4:
                if st.button(f"**Available Slots**\n\n## {int(available_slots)}", key=f"available_{selected_date.strftime('%Y%m%d')}", use_container_width=True):
                    st.session_state[f"slot_filter_{selected_date.strftime('%Y%m%d')}"] = "available"

        st.markdown("")
        
        # Get current filter state
        current_filter = st.session_state.get(f"slot_filter_{selected_date.strftime('%Y%m%d')}", "all")
        filter_label = {
            "all": "All Tee Times",
            "occupied": "Occupied Slots (Sold Out Everywhere)",
            "available": "Available Slots"
        }
        
        st.markdown(f"### ⛳ {filter_label[current_filter]}")

        availability_df = load_channel_availability(
            selected_date.strftime('%Y-%m-%d'),
            selected_course
        )

        if not availability_df.empty:
            # Select and format columns for display
            display_df = availability_df[[
                'tee_time',
                'brand_current_price',
                'brand_availability_status',
                'golfnow_current_price',
                'golfnow_availability_status',
                'teeoff_current_price',
                'teeoff_availability_status',
                'supremegolf_current_price',
                'supremegolf_availability_status',
                'overall_availability_status'
            ]].copy()
            
            # Apply filter based on current selection
            if current_filter == "occupied":
                display_df = display_df[display_df['overall_availability_status'] == 'SOLD_OUT_EVERYWHERE']
            elif current_filter == "available":
                display_df = display_df[display_df['overall_availability_status'] != 'SOLD_OUT_EVERYWHERE']
            # 'all' shows everything, no filter needed
            
            # Rename columns for better display
            display_df.columns = [
                'Tee Time',
                'Brand Price',
                'Brand Status',
                'GolfNow Price',
                'GolfNow Status',
                'TeeOff Price',
                'TeeOff Status',
                'SupremeGolf Price',
                'SupremeGolf Status',
                'Overall Status'
            ]
            
            # Format price columns
            for col in ['Brand Price', 'GolfNow Price', 'TeeOff Price', 'SupremeGolf Price']:
                display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=500
            )
        else:
            st.info("No tee time data available for this date.")
    
    # TAB 2: RATESHOP HISTORY CHART
    with tab2:
        st.markdown("### 📈 Price Trend by Lead Time")
        
        history_df = load_history_chart(selected_date.strftime('%Y-%m-%d'))

        if not history_df.empty:
            course_options = sorted(history_df["course_name"].unique().tolist())
            selected_courses = st.multiselect(
                "Courses to display",
                options=course_options,
                default=course_options,
                key=f"chart_courses_{selected_date.strftime('%Y%m%d')}"
            )

            if not selected_courses:
                st.info("Select at least one course to show the chart.")
            else:
                chart_df = history_df[
                    history_df["course_name"].isin(selected_courses)
                ].copy()
                chart_df["tee_date"] = pd.to_datetime(chart_df["tee_date"])
                chart_df["course_label"] = chart_df["course_name"].where(
                    chart_df["course_name"] != selected_course,
                    "self"
                )
                chart_df["date_label"] = chart_df["tee_date"].dt.strftime("%A %b %d")

                pivot_df = (
                    chart_df.pivot(
                        index="tee_date",
                        columns="course_label",
                        values="avg_price"
                    )
                    .reset_index()
                    .sort_values("tee_date", ascending=False)
                )
                pivot_df["date_label"] = pivot_df["tee_date"].dt.strftime("%A %b %d")

                course_cols = [
                    c for c in pivot_df.columns
                    if c not in ("tee_date", "date_label")
                ]
                course_cols_sorted = sorted(course_cols)
                if "self" in course_cols_sorted:
                    course_cols_sorted.remove("self")
                    course_cols_sorted = ["self"] + course_cols_sorted

                tooltip_course_cols = course_cols_sorted[:7]
                tooltip_fields = [
                    alt.Tooltip("date_label:N", title="Date")
                ]
                for col in tooltip_course_cols:
                    tooltip_fields.append(
                        alt.Tooltip(f"{col}:Q", title=col, format="$.2f")
                    )

                legend_order = course_cols_sorted

                # Merge pivot data into chart_df for tooltip access
                chart_df_with_tooltip = chart_df.merge(
                    pivot_df[["tee_date", "date_label"] + tooltip_course_cols],
                    on="tee_date",
                    how="left"
                )

                # Build tooltip fields
                tooltip_fields_list = [
                    alt.Tooltip("date_label_y:N", title="Date")
                ]
                for col in tooltip_course_cols:
                    tooltip_fields_list.append(
                        alt.Tooltip(f"{col}:Q", title=col, format="$.2f")
                    )

                # Single chart with lines and points that show tooltip on hover
                chart = (
                    alt.Chart(chart_df_with_tooltip)
                    .mark_line(point=alt.OverlayMarkDef(size=140, filled=True, opacity=1))
                    .encode(
                        x=alt.X("tee_date:T", title="Date", axis=alt.Axis(format="%b %d")),
                        y=alt.Y("avg_price:Q", title="Avg Price ($)"),
                        color=alt.Color(
                            "course_label:N",
                            title="Course",
                            sort=legend_order
                        ),
                        strokeWidth=alt.condition(
                            alt.FieldEqualPredicate(field="course_label", equal="self"),
                            alt.value(4),
                            alt.value(2)
                        ),
                        tooltip=tooltip_fields_list
                    )
                    .properties(height=400)
                    .interactive()
                )

                st.altair_chart(chart, use_container_width=True)
                
                # st.markdown("")
                # st.markdown("**📊 Data Table**")
                # st.dataframe(chart_df, use_container_width=True, hide_index=True)
        else:
            st.info("No historical data available for this date.")

# @st.cache_data(ttl=60)
@st.cache_data
def load_channel_availability(date_str, course):
    """Load channel availability with lifecycle tracking for specific date"""
    try:
        client = bigquery.Client.from_service_account_json(
            "D:\\Aman\\Web Scraping\\Golf Rateshop\\golf_credential.json"
        )
        
        query = f"""
        WITH normalized AS (
          SELECT
            CASE
              WHEN course_name IN ('thorntree_golf_club','thorntree_country_club')
                THEN 'thorntree_golf_club'
              WHEN course_name IN (
                'riverside_golf_club_-_dallas',
                'riverside_golf_club',
                'riverside_g.c.'
              ) THEN 'riverside_golf_club_dallas'
              WHEN course_name IN (
                'bear_creek',
                'bear_creek_golf_club_-_west',
                'bear_creek_golf_club_-_west_course'
              ) THEN 'bear_creek_golf_club_west'
              ELSE course_name
            END AS course_name,
            source_channel,
            tee_date,
            tee_time,
            price,
            scrape_timestamp
          FROM `tee-metrics-golf-tee-time.golf_silver.tee_time_clean`
          WHERE DATE(tee_date) = '{date_str}'
            AND CASE
              WHEN course_name IN ('thorntree_golf_club','thorntree_country_club')
                THEN 'thorntree_golf_club'
              WHEN course_name IN (
                'riverside_golf_club_-_dallas',
                'riverside_golf_club',
                'riverside_g.c.'
              ) THEN 'riverside_golf_club_dallas'
              WHEN course_name IN (
                'bear_creek',
                'bear_creek_golf_club_-_west',
                'bear_creek_golf_club_-_west_course'
              ) THEN 'bear_creek_golf_club_west'
              ELSE course_name
            END = '{course}'
        ),

        -- Day boundaries per channel
        day_bounds AS (
          SELECT
            course_name,
            source_channel,
            tee_date,
            MIN(scrape_timestamp) AS first_scrape_ts,
            MAX(scrape_timestamp) AS last_scrape_ts
          FROM normalized
          GROUP BY course_name, source_channel, tee_date
        ),

        -- Slot lifecycle per channel
        slot_lifecycle AS (
          SELECT
            n.course_name,
            n.source_channel,
            n.tee_date,
            n.tee_time,
            MIN(n.scrape_timestamp) AS first_seen_at,
            MAX(n.scrape_timestamp) AS last_seen_at,
            ANY_VALUE(n.price) AS sample_price
          FROM normalized n
          GROUP BY n.course_name, n.source_channel, n.tee_date, n.tee_time
        ),

        -- Classify lifecycle per channel
        classified AS (
          SELECT
            s.course_name,
            s.source_channel,
            s.tee_date,
            s.tee_time,
            s.sample_price,

            CASE
              WHEN s.first_seen_at = d.first_scrape_ts
                   AND s.last_seen_at = d.last_scrape_ts
                THEN 'STILL_AVAILABLE'

              WHEN s.first_seen_at = d.first_scrape_ts
                   AND s.last_seen_at < d.last_scrape_ts
                THEN 'SOLD_OUT'

              WHEN s.first_seen_at > d.first_scrape_ts
                   AND s.last_seen_at = d.last_scrape_ts
                THEN 'ADDED_LATER'

              WHEN s.first_seen_at > d.first_scrape_ts
                   AND s.last_seen_at < d.last_scrape_ts
                THEN 'ADDED_AND_SOLD'
            END AS lifecycle_status

          FROM slot_lifecycle s
          JOIN day_bounds d
            ON s.course_name = d.course_name
           AND s.source_channel = d.source_channel
           AND s.tee_date = d.tee_date
        ),

        -- Pivot per slot
        pivoted AS (
          SELECT
            course_name,
            tee_date,
            tee_time,

            MAX(IF(source_channel='brand', sample_price, NULL)) AS brand_price,
            MAX(IF(source_channel='golfnow', sample_price, NULL)) AS golfnow_price,
            MAX(IF(source_channel='teeoff', sample_price, NULL)) AS teeoff_price,
            MAX(IF(source_channel='supremegolf', sample_price, NULL)) AS supremegolf_price,

            MAX(IF(source_channel='brand', lifecycle_status, NULL)) AS brand_availability_status,
            MAX(IF(source_channel='golfnow', lifecycle_status, NULL)) AS golfnow_availability_status,
            MAX(IF(source_channel='teeoff', lifecycle_status, NULL)) AS teeoff_availability_status,
            MAX(IF(source_channel='supremegolf', lifecycle_status, NULL)) AS supremegolf_availability_status

          FROM classified
          GROUP BY course_name, tee_date, tee_time
        )

        SELECT
          ROW_NUMBER() OVER (ORDER BY tee_time) AS Row,
          course_name,
          tee_date,
          tee_time,

          brand_price AS brand_current_price,
          golfnow_price AS golfnow_current_price,
          teeoff_price AS teeoff_current_price,
          supremegolf_price AS supremegolf_current_price,

          COALESCE(brand_availability_status, 'NEVER_LISTED') AS brand_availability_status,
          COALESCE(golfnow_availability_status, 'NEVER_LISTED') AS golfnow_availability_status,
          COALESCE(teeoff_availability_status, 'NEVER_LISTED') AS teeoff_availability_status,
          COALESCE(supremegolf_availability_status, 'NEVER_LISTED') AS supremegolf_availability_status,

          CASE
            -- All channels never listed
            WHEN COALESCE(brand_availability_status, 'NEVER_LISTED') = 'NEVER_LISTED'
             AND COALESCE(golfnow_availability_status, 'NEVER_LISTED') = 'NEVER_LISTED'
             AND COALESCE(teeoff_availability_status, 'NEVER_LISTED') = 'NEVER_LISTED'
             AND COALESCE(supremegolf_availability_status, 'NEVER_LISTED') = 'NEVER_LISTED'
              THEN 'NOT_AVAILABLE_ANYWHERE'

            -- All channels sold out or never listed (not currently available)
            WHEN COALESCE(brand_availability_status, 'NEVER_LISTED') IN ('SOLD_OUT', 'NEVER_LISTED', 'ADDED_AND_SOLD')
             AND COALESCE(golfnow_availability_status, 'NEVER_LISTED') IN ('SOLD_OUT', 'NEVER_LISTED', 'ADDED_AND_SOLD')
             AND COALESCE(teeoff_availability_status, 'NEVER_LISTED') IN ('SOLD_OUT', 'NEVER_LISTED', 'ADDED_AND_SOLD')
             AND COALESCE(supremegolf_availability_status, 'NEVER_LISTED') IN ('SOLD_OUT', 'NEVER_LISTED', 'ADDED_AND_SOLD')
              THEN 'SOLD_OUT_EVERYWHERE'

            -- Brand and at least one OTA currently available
            WHEN COALESCE(brand_availability_status, 'NEVER_LISTED') IN ('STILL_AVAILABLE', 'ADDED_LATER')
             AND (COALESCE(golfnow_availability_status, 'NEVER_LISTED') IN ('STILL_AVAILABLE', 'ADDED_LATER')
               OR COALESCE(teeoff_availability_status, 'NEVER_LISTED') IN ('STILL_AVAILABLE', 'ADDED_LATER')
               OR COALESCE(supremegolf_availability_status, 'NEVER_LISTED') IN ('STILL_AVAILABLE', 'ADDED_LATER'))
              THEN 'BRAND_AND_OTA'

            -- Only brand currently available
            WHEN COALESCE(brand_availability_status, 'NEVER_LISTED') IN ('STILL_AVAILABLE', 'ADDED_LATER')
              THEN 'BRAND_ONLY'

            -- Only OTA channels currently available
            WHEN COALESCE(golfnow_availability_status, 'NEVER_LISTED') IN ('STILL_AVAILABLE', 'ADDED_LATER')
              OR COALESCE(teeoff_availability_status, 'NEVER_LISTED') IN ('STILL_AVAILABLE', 'ADDED_LATER')
              OR COALESCE(supremegolf_availability_status, 'NEVER_LISTED') IN ('STILL_AVAILABLE', 'ADDED_LATER')
              THEN 'OTA_ONLY'

            ELSE 'NOT_AVAILABLE_ANYWHERE'
          END AS overall_availability_status

        FROM pivoted
        ORDER BY tee_time
        """
        
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Error loading availability: {str(e)}")
        return pd.DataFrame()

# @st.cache_data(ttl=60)
@st.cache_data
def load_history_chart(date_str):
    """Load rate shop history for chart - shows price trends across multiple dates"""
    try:
        client = bigquery.Client.from_service_account_json(
            "D:\\Aman\\Web Scraping\\Golf Rateshop\\golf_credential.json"
        )
        
        query = f"""
        WITH normalized AS (
          SELECT
            CASE
              WHEN course_name IN ('thorntree_golf_club','thorntree_country_club')
                THEN 'thorntree_golf_club'
              WHEN course_name IN (
                'riverside_golf_club_-_dallas',
                'riverside_golf_club',
                'riverside_g.c.'
              ) THEN 'riverside_golf_club_dallas'
              WHEN course_name IN (
                'bear_creek',
                'bear_creek_golf_club_-_west',
                'bear_creek_golf_club_-_west_course'
              ) THEN 'bear_creek_golf_club_west'
              ELSE course_name
            END AS course_name,
            source_channel,
            CAST(tee_date AS DATE) AS tee_date,
            price,
            scrape_timestamp
          FROM `tee-metrics-golf-tee-time.golf_silver.tee_time_clean`
          WHERE CAST(tee_date AS DATE) >= CAST('2026-02-03' AS DATE)
            AND CAST(tee_date AS DATE) <= CAST('{date_str}' AS DATE)
        )
        SELECT
            course_name,
            tee_date,
            AVG(price) AS avg_price
        FROM normalized
        GROUP BY course_name, tee_date
        ORDER BY tee_date DESC, course_name
        """
        
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")
        return pd.DataFrame()

# Show tile modal if date is selected
if st.session_state.tile_modal_date:
    show_tile_modal(st.session_state.tile_modal_date, selected_course, month_df)
    st.session_state.tile_modal_date = None  # Reset after showing

# --------------------------
# FLOATING MODAL (View Details)
# --------------------------

if st.session_state.selected_date:
    selected_date = st.session_state.selected_date

    day_data = month_df[
        month_df["tee_date"] == pd.Timestamp(selected_date)
    ].sort_values("average_price")

    my_row = my_df[my_df["tee_date"] == pd.Timestamp(selected_date)]

    if not my_row.empty:
        my_price = my_row["average_price"].values[0]
        my_gap = my_row["price_gap_percent"].values[0]
        my_occupancy = my_row["occupancy_percent"].values[0]
        min_rate = day_data["market_min_price"].values[0]
        avg_rate = day_data["market_avg_price"].values[0]
        max_rate = day_data["market_max_price"].values[0]

        # Create modal using native Streamlit components
        with st.container():
            st.markdown("---")
            st.markdown("")
            
            # Modal header with close button
            modal_col1, modal_col2 = st.columns([0.9, 0.1])
            with modal_col1:
                st.markdown(f"### 📅 {selected_date.strftime('%B %d, %Y')}")
            with modal_col2:
                if st.button("❌", key="close_btn"):
                    st.session_state.selected_date = None
                    st.rerun()
            
            st.markdown("")
            
            # Price display - using columns for layout
            price_col1, price_col2, price_col3 = st.columns(3)
            
            with price_col1:
                st.info(f"**Your Price**\n\n# ${my_price:.0f}")
            
            with price_col2:
                gap_indicator = "🟢 GOOD" if my_gap < 0 else "🔴 HIGH"
                st.warning(f"**Price Gap**\n\n# {my_gap:+.1f}%\n\n{gap_indicator}")
            
            with price_col3:
                st.metric("Occupancy", f"{my_occupancy:.0f}%")
            
            st.markdown("")
            
            # Market range section
            st.markdown("#### 📊 Market Price Range")
            market_col1, market_col2, market_col3 = st.columns(3)
            
            with market_col1:
                st.metric("Minimum", f"${min_rate:.0f}")
            
            with market_col2:
                st.metric("Average", f"${avg_rate:.0f}")
            
            with market_col3:
                st.metric("Maximum", f"${max_rate:.0f}")
            
            st.markdown("")
            
            # Pricing insight
            if my_gap < 0:
                insight_msg = f"✅ **You're underpriced by {abs(my_gap):.1f}%** - This is a competitive advantage! Consider this pricing strategy."
                st.success(insight_msg)
            elif my_gap < 5:
                insight_msg = f"⚠️ **You're {my_gap:.1f}% above market** - You're competitively positioned."
                st.info(insight_msg)
            else:
                insight_msg = f"⛔ **You're {my_gap:.1f}% above market** - Consider reducing prices to match competitors."
                st.warning(insight_msg)
            
            st.markdown("")
            st.markdown("---")
            st.markdown("### 🏌️ Competitor Pricing")

            comp_df = day_data[
                day_data["course_name"] != selected_course
            ][["course_name", "source_channel", "average_price", "occupancy_percent", "price_position_flag"]].copy()
            comp_df.columns = ["Course", "Source", "Price", "Occupancy %", "Position"]
            comp_df = comp_df.sort_values("Price")
            
            # Display competitors table
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            
            st.markdown("")
            
            # Close button at bottom
            close_col1, close_col2, close_col3 = st.columns([1, 1, 1])
            with close_col2:
                if st.button("✕ Close Details", use_container_width=True, key="close_btn_bottom"):
                    st.session_state.selected_date = None
                    st.rerun()
