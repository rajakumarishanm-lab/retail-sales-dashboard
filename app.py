import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

# 1. Page Configuration
st.set_page_config(
    page_title="Retail Sales Intelligence App",
    page_icon="📈",
    layout="wide"
)

# --- CSS UPDATED TO FIX CURSOR AND SHOW FULL VALUE ON HOVER ---
st.markdown("""
    <style>
    /* Base style for the metric value */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important; 
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        cursor: default !important; /* Removes the '?' help cursor */
        display: block;
    }
    
    /* HOVER EFFECT: Pops out the full number clearly on top of other content */
    [data-testid="stMetricValue"]:hover {
        overflow: visible !important;
        white-space: nowrap !important;
        width: max-content !important;
        background-color: white !important; /* White background for readability */
        padding: 5px 15px !important;
        border: 1px solid #e6e9ef !important;
        border-radius: 8px !important;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.15) !important;
        z-index: 10000 !important;
        position: relative;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper function to format currency in Indian Standard (Lakhs/Crores grouping)
def format_indian_currency(num):
    if pd.isna(num) or num is None:
        return "₹0.00"
    try:
        num = float(num)
        sign = "-" if num < 0 else ""
        num = abs(num)
        
        # Round to 2 decimal places
        num_str = f"{num:.2f}"
        parts = num_str.split('.')
        int_part = parts[0]
        dec_part = parts[1]
        
        if len(int_part) <= 3:
            return f"{sign}₹{int_part}.{dec_part}"
        
        last_three = int_part[-3:]
        remaining = int_part[:-3]
        
        # Group remaining digits in pairs
        groups = []
        while len(remaining) > 0:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
            
        groups.reverse()
        formatted_remaining = ",".join(groups)
        return f"{sign}₹{formatted_remaining},{last_three}.{dec_part}"
    except Exception:
        return f"₹{num}"

# Title Header
st.title("📈 Retail Sales Intelligence Dashboard")
st.markdown("Gain actionable insights from store performance and weekly transaction metrics.")
st.markdown("---")

# Initialize placeholder data frames
store_df = None
sales_df = None
data_loaded = False

# 2. Sidebar File Uploaders
st.sidebar.header("📁 Data Source Upload")
store_file = st.sidebar.file_uploader("1. Upload Store Data (CSV/XLSX)", type=["csv", "xlsx"])
sales_file = st.sidebar.file_uploader("2. Upload Weekly Sales Data (CSV/XLSX)", type=["csv", "xlsx"])

# Option to load mock data for testing purposes
load_mock = st.sidebar.checkbox("Load Sample/Demo Data")

# Generate Mock Data Helper
def generate_mock_data():
    stores = {
        'store_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
        'store_name': ['Alpha Mart', 'Beta Bazar', 'Gamma Retail', 'Delta Express', 'Epsilon Super'],
        'region': ['North', 'South', 'West', 'East', 'North'],
        'city': ['Delhi', 'Bengaluru', 'Mumbai', 'Kolkata', 'Noida'],
        'store_format': ['Hypermarket', 'Supermarket', 'Express', 'Hypermarket', 'Supermarket']
    }
    s_df = pd.DataFrame(stores)
    
    weeks = ['2026-06-01', '2026-06-08', '2026-06-15', '2026-06-22']
    categories = ['Electronics', 'Apparel', 'Grocery']
    
    sales_rows = []
    np.random.seed(42)
    for week in weeks:
        for idx, row in s_df.iterrows():
            for cat in categories:
                footfall = np.random.randint(800, 3000)
                transactions = int(footfall * np.random.uniform(0.35, 0.55))
                units_sold = int(transactions * np.random.uniform(1.5, 3.5))
                gross_sales = units_sold * np.random.uniform(300, 1200)
                discount_amount = gross_sales * np.random.uniform(0.05, 0.20)
                net_sales = gross_sales - discount_amount
                sales_target = net_sales * np.random.uniform(0.85, 1.25)
                inventory_on_hand = np.random.randint(200, 1000)
                stockouts = np.random.randint(0, 8)
                returns_amount = net_sales * np.random.uniform(0.01, 0.07)
                customer_rating = round(np.random.uniform(3.8, 4.9), 1)
                marketing_spend = np.random.uniform(2000, 8000)
                
                sales_rows.append({
                    'week_start_date': week,
                    'region': row['region'],
                    'store_id': row['store_id'],
                    'store_name': row['store_name'],
                    'city': row['city'],
                    'store_format': row['store_format'],
                    'product_category': cat,
                    'footfall': footfall,
                    'transactions': transactions,
                    'units_sold': units_sold,
                    'gross_sales': gross_sales,
                    'discount_amount': discount_amount,
                    'net_sales': net_sales,
                    'sales_target': sales_target,
                    'inventory_on_hand': inventory_on_hand,
                    'stockouts': stockouts,
                    'returns_amount': returns_amount,
                    'customer_rating': customer_rating,
                    'marketing_spend': marketing_spend
                })
    sa_df = pd.DataFrame(sales_rows)
    return s_df, sa_df

# Handle File Reading
def read_uploaded_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    else:
        return pd.read_excel(uploaded_file)

if load_mock:
    store_df, sales_df = generate_mock_data()
    data_loaded = True
elif store_file is not None and sales_file is not None:
    try:
        store_df = read_uploaded_file(store_file)
        sales_df = read_uploaded_file(sales_file)
        data_loaded = True
    except Exception as e:
        st.sidebar.error(f"Error loading files: {e}")

# Apply logic for dynamic filtering if data is available
if data_loaded:
    # --- Capture original column order from source ---
    original_col_order = list(sales_df.columns)

    # --- FIX for DateParseError ---
    sales_df['week_start_date'] = pd.to_datetime(sales_df['week_start_date'], errors='coerce')
    # Remove rows that couldn't be parsed
    sales_df = sales_df.dropna(subset=['week_start_date'])
    sales_df['week_start_date'] = sales_df['week_start_date'].dt.date
    
    # Drop duplication to avoid suffix errors
    store_df_clean = store_df.drop_duplicates(subset=['store_id'])
    overlap_cols = [col for col in ['store_name', 'region', 'city', 'store_format'] if col in sales_df.columns]
    sales_df_clean = sales_df.drop(columns=overlap_cols)
    
    # Merge datasets
    merged_df = pd.merge(sales_df_clean, store_df_clean, on='store_id', how='left')

    # --- Restore Column Order ---
					 
				 
    cols_in_source = [c for c in original_col_order if c in merged_df.columns]
    cols_extra = [c for c in merged_df.columns if c not in original_col_order]
    merged_df = merged_df[cols_in_source + cols_extra]
    
    # Convert numerical columns to explicit floats/ints
    numeric_cols = [
        'footfall', 'transactions', 'units_sold', 'gross_sales', 'discount_amount', 
        'net_sales', 'sales_target', 'inventory_on_hand', 'stockouts', 'returns_amount', 
        'customer_rating', 'marketing_spend'
    ]
    for col in numeric_cols:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').fillna(0)

    # 3. Sidebar Filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Filters")
    
    # Multi-select lists
    week_list = sorted(list(merged_df['week_start_date'].unique()))
    region_list = sorted(list(merged_df['region'].unique()))
    city_list = sorted(list(merged_df['city'].unique()))
    format_list = sorted(list(merged_df['store_format'].unique()))
    store_list = sorted(list(merged_df['store_name'].unique()))
    category_list = sorted(list(merged_df['product_category'].unique()))
    
    selected_weeks = st.sidebar.multiselect("Week", options=week_list)
    selected_regions = st.sidebar.multiselect("Region", options=region_list)
    selected_cities = st.sidebar.multiselect("City", options=city_list)
    selected_formats = st.sidebar.multiselect("Store Format", options=format_list)
    selected_stores = st.sidebar.multiselect("Store Name", options=store_list)
    selected_categories = st.sidebar.multiselect("Product Category", options=category_list)
    
    # Applying filters
    filtered_df = merged_df.copy()
    if selected_weeks:
        filtered_df = filtered_df[filtered_df['week_start_date'].isin(selected_weeks)]
    if selected_regions:
        filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]
    if selected_cities:
        filtered_df = filtered_df[filtered_df['city'].isin(selected_cities)]
    if selected_formats:
        filtered_df = filtered_df[filtered_df['store_format'].isin(selected_formats)]
    if selected_stores:
        filtered_df = filtered_df[filtered_df['store_name'].isin(selected_stores)]
    if selected_categories:
        filtered_df = filtered_df[filtered_df['product_category'].isin(selected_categories)]
        
else:
    filtered_df = pd.DataFrame()

# 4. Top-row KPI Cards Display
kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

if not data_loaded or filtered_df.empty:
    kpi_col1.metric("Net Sales", "-")
    kpi_col2.metric("Target Achievement (%)", "-")
    kpi_col3.metric("Avg Transaction Value (ATV)", "-")
    kpi_col4.metric("Return Rate (%)", "-")
    kpi_col5.metric("Discount Rate (%)", "-")
    
    # Prompt user to upload files
    st.info("👋 Welcome! Please upload **both Store Data and Weekly Sales Data** via the sidebar, or check the 'Load Sample/Demo Data' box to preview the intelligence tools.")
else:
    # Calculations
    net_sales_sum = filtered_df['net_sales'].sum()
    target_sum = filtered_df['sales_target'].sum()
    ach_percent = (net_sales_sum / target_sum * 100) if target_sum > 0 else 0.0
    
    total_tx = filtered_df['transactions'].sum()
    atv_val = (net_sales_sum / total_tx) if total_tx > 0 else 0.0
    
    gross_sales_sum = filtered_df['gross_sales'].sum()
    returns_sum = filtered_df['returns_amount'].sum()
    return_rate_val = (returns_sum / gross_sales_sum * 100) if gross_sales_sum > 0 else 0.0
    
    discounts_sum = filtered_df['discount_amount'].sum()
    discount_rate_val = (discounts_sum / gross_sales_sum * 100) if gross_sales_sum > 0 else 0.0

    kpi_col1.metric("Net Sales", format_indian_currency(net_sales_sum))
    kpi_col2.metric("Target Achievement", f"{ach_percent:.2f}%")
    kpi_col3.metric("Avg Transaction Value (ATV)", format_indian_currency(atv_val))
    kpi_col4.metric("Return Rate", f"{return_rate_val:.2f}%")
    kpi_col5.metric("Discount Rate", f"{discount_rate_val:.2f}%")

    # 5. Visual Charts Section
    st.markdown("### 📊 Interactive Visualizations")
    
    row1_col1, row1_col2 = st.columns(2)
    
    # Chart 1: Weekly Trend (Line)
    weekly_trend = filtered_df.groupby('week_start_date')['net_sales'].sum().reset_index()
    fig_weekly = px.line(
        weekly_trend, 
        x='week_start_date', 
        y='net_sales', 
        title="Weekly Net Sales Trend", 
        markers=True,
        labels={'week_start_date': 'Week Start Date', 'net_sales': 'Net Sales (₹)'}
    )
    fig_weekly.update_layout(yaxis_tickformat="~s") 
    row1_col1.plotly_chart(fig_weekly, use_container_width=True)
    
    # Chart 2: Sales by Region (Bar)
    region_sales = filtered_df.groupby('region')['net_sales'].sum().reset_index()
    fig_region = px.bar(
        region_sales, 
        x='region', 
        y='net_sales', 
        color='region',
        title="Net Sales by Region",
        labels={'region': 'Region', 'net_sales': 'Net Sales (₹)'}
    )
    row1_col2.plotly_chart(fig_region, use_container_width=True)
    
    row2_col1, row2_col2 = st.columns(2)
    
    # Chart 3: Category Performance (Donut)
    cat_sales = filtered_df.groupby('product_category')['net_sales'].sum().reset_index()
    fig_cat = px.pie(
        cat_sales, 
        names='product_category', 
        values='net_sales', 
        hole=0.4,
        title="Net Sales Distribution by Product Category"
    )
    row2_col1.plotly_chart(fig_cat, use_container_width=True)
    
    # Chart 4: Store Leaderboard (Horizontal Bar)
    store_leaderboard = filtered_df.groupby('store_name')['net_sales'].sum().reset_index()
    store_leaderboard = store_leaderboard.sort_values(by='net_sales', ascending=True).tail(10)
    fig_leaderboard = px.bar(
        store_leaderboard, 
        x='net_sales', 
        y='store_name', 
        orientation='h',
        title="Top Stores by Net Sales",
        labels={'store_name': 'Store', 'net_sales': 'Net Sales (₹)'}
    )
    row2_col2.plotly_chart(fig_leaderboard, use_container_width=True)
    
    # Chart 5: Stockout Risk (Scatter Plot)
    stockout_agg = filtered_df.groupby(['store_name', 'product_category']).agg({
        'inventory_on_hand': 'mean',
        'stockouts': 'sum',
        'net_sales': 'sum'
    }).reset_index()
    
    fig_stockout = px.scatter(
        stockout_agg, 
        x='inventory_on_hand', 
        y='stockouts', 
        size='net_sales', 
        color='product_category',
        hover_name='store_name',
        title="Stockout Risk Analysis (Average Inventory vs. Total Stockouts)",
        labels={'inventory_on_hand': 'Avg Inventory on Hand', 'stockouts': 'Total Stockouts (Weeks)'}
    )
    st.plotly_chart(fig_stockout, use_container_width=True)

    # 6. Business Insight Summary
    st.markdown("---")
    st.markdown("### 🔍 Business Insight Summary")
    
    region_perf = filtered_df.groupby('region')['net_sales'].sum()
    if not region_perf.empty:
        best_r = region_perf.idxmax()
        best_r_val = region_perf.max()
        worst_r = region_perf.idxmin()
        worst_r_val = region_perf.min()
    else:
        best_r, best_r_val, worst_r, worst_r_val = "N/A", 0, "N/A", 0
        
    store_achievement = filtered_df.groupby('store_name').agg({'net_sales': 'sum', 'sales_target': 'sum'}).reset_index()
    store_achievement['achievement'] = (store_achievement['net_sales'] / store_achievement['sales_target'] * 100).fillna(0)
    underperforming = store_achievement[store_achievement['sales_target'] > 0].sort_values(by='achievement', ascending=True).head(3)
    
    category_returns = filtered_df.groupby('product_category').agg({'returns_amount': 'sum', 'gross_sales': 'sum'}).reset_index()
    category_returns['return_rate'] = (category_returns['returns_amount'] / category_returns['gross_sales'] * 100).fillna(0)
    high_return_cats = category_returns.sort_values(by='return_rate', ascending=False).head(2)

    ins_col1, ins_col2, ins_col3 = st.columns(3)
    
    with ins_col1:
        st.subheader("🌐 Regional Outlook")
        st.write(f"- **Top-Performing Region:** {best_r} ({format_indian_currency(best_r_val)})")
        st.write(f"- **Lowest-Performing Region:** {worst_r} ({format_indian_currency(worst_r_val)})")
        
    with ins_col2:
        st.subheader("🏪 Underperforming Stores")
        if not underperforming.empty:
            for _, row in underperforming.iterrows():
                st.write(f"- **{row['store_name']}**: Achieved **{row['achievement']:.2f}%** of target.")
        else:
            st.write("No underperforming stores identified.")
            
    with ins_col3:
        st.subheader("📦 High-Return Categories")
        if not high_return_cats.empty:
            for _, row in high_return_cats.iterrows():
                st.write(f"- **{row['product_category']}**: Return Rate of **{row['return_rate']:.2f}%**.")
        else:
            st.write("No return data found.")

    # 7. Export Functionality
    st.markdown("---")
    st.markdown("### 📥 Export Filtered Dataset")
    st.write("The exported files will now maintain the column order of your original source file.")
    
    exp_col1, exp_col2 = st.columns(2)
    
    # CSV generation
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    exp_col1.download_button(
        label="Download Filtered Data as CSV",
        data=csv_data,
        file_name="filtered_retail_sales.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # Excel generation
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Filtered_Metrics')
    excel_data = buffer.getvalue()
    
    exp_col2.download_button(
        label="Download Filtered Data as Excel (.xlsx)",
        data=excel_data,
        file_name="filtered_retail_sales.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
