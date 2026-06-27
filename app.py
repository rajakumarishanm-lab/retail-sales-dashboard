import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Page Configuration
st.set_page_config(
    page_title="Retail Sales Intelligence App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to prevent st.metric from truncating values
st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 2. General Helper Utilities & Cache Functions
def convert_df_to_csv(dataframe):
    """Converts a dataframe to a downloadable CSV byte stream dynamically."""
    return dataframe.to_csv(index=False).encode('utf-8')

@st.cache_data
def generate_mock_store_master():
    """Generates a mock Store Master dataframe matching expected schema."""
    np.random.seed(42)
    regions = ['North', 'South', 'East', 'West']
    cities = {
        'North': ['Delhi', 'Noida', 'Gurugram'],
        'South': ['Chennai', 'Bengaluru', 'Hyderabad'],
        'East': ['Kolkata', 'Patna', 'Bhubaneswar'],
        'West': ['Mumbai', 'Pune', 'Ahmedabad']
    }
    formats = ['High Street', 'Mall', 'Express', 'Boutique']
    
    data = []
    for i in range(1, 16):
        store_id = f"ST-{i:03d}"
        region = np.random.choice(regions)
        city = np.random.choice(cities[region])
        store_name = f"{city} Retail Hub"
        store_format = np.random.choice(formats)
        data.append({
            'store_id': store_id,
            'store_name': store_name,
            'region': region,
            'city': city,
            'store_format': store_format
        })
    return pd.DataFrame(data)

@st.cache_data
def generate_mock_retail_weekly_status(_store_master_df):
    """Generates a mock Retail Weekly Status dataframe linked to store master identifiers."""
    np.random.seed(42)
    categories = ['Grocery', 'Apparel', 'Electronics', 'Footwear', 'Beauty']
    weeks = ['05-01-2026', '12-01-2026', '19-01-2026', '26-01-2026', '02-02-2026', '09-02-2026', '16-02-2026', '23-02-2026']
    
    store_col = 'store_id' if 'store_id' in _store_master_df.columns else _store_master_df.columns[0]
    stores = _store_master_df.to_dict('records')
    data = []
    
    for _ in range(800):
        store = np.random.choice(stores)
        category = np.random.choice(categories)
        week = np.random.choice(weeks)
        
        footfall = np.random.randint(1000, 5000)
        transactions = int(footfall * np.random.uniform(0.2, 0.45))
        units_sold = int(transactions * np.random.uniform(1.1, 2.5))
        
        gross_sales = round(units_sold * np.random.uniform(15.0, 45.0), 2)
        discount_amount = round(gross_sales * np.random.uniform(0.05, 0.20), 2)
        returns_amount = round(gross_sales * np.random.uniform(0.01, 0.05), 2)
        
        net_sales = round(gross_sales - discount_amount - returns_amount, 2)
        sales_target = round(net_sales * np.random.uniform(0.8, 1.3), 2)
        
        inventory_on_hand = np.random.randint(100, 1500)
        stockouts = np.random.choice([0, 1, 2, 3], p=[0.75, 0.15, 0.08, 0.02])
        customer_rating = np.random.choice([3, 4, 5], p=[0.1, 0.4, 0.5])
        marketing_spend = np.random.randint(500, 3000)
        
        row = {
            'week_start_date': week,
            'product_category': category,
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
        }
        row[store_col] = store[store_col]
        data.append(row)
    return pd.DataFrame(data)

# 3. Indian Currency Formatting Utility
def format_indian_currency(number):
    """Formats a numeric value into the Indian numbering system with ₹ symbol."""
    try:
        val = round(float(number), 2)
        is_negative = val < 0
        val = abs(val)
        
        parts = f"{val:.2f}".split('.')
        int_part = parts[0]
        dec_part = parts[1]
        
        if len(int_part) <= 3:
            formatted_int = int_part
        else:
            last_three = int_part[-3:]
            remaining = int_part[:-3]
            
            groups = []
            while len(remaining) > 0:
                groups.append(remaining[-2:])
                remaining = remaining[:-2]
            
            groups.reverse()
            formatted_int = ",".join(groups) + "," + last_three
        
        return f"₹{'-' if is_negative else ''}{formatted_int}.{dec_part}"
    except Exception:
        return f"₹{number}"

# 4. Dynamic File Loader
def load_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file)
    except Exception as e:
        st.sidebar.error(f"Error loading {uploaded_file.name}: {e}")
    return None

# 5. Header Normalization and Smart Merger
def normalize_column_headers(df):
    if df is not None:
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    return df

def align_and_merge(weekly, store):
    """Intelligently detects join keys across files and merges them safely."""
    weekly = normalize_column_headers(weekly)
    store = normalize_column_headers(store)
    
    weekly_candidates = [c for c in ['store_id', 'store', 'store_name'] if c in weekly.columns]
    store_candidates = [c for c in ['store_id', 'store', 'store_name'] if c in store.columns]
    
    join_key = None
    common_keys = list(set(weekly_candidates).intersection(set(store_candidates)))
    
    if common_keys:
        for k in ['store_id', 'store', 'store_name']:
            if k in common_keys:
                join_key = k
                break
    else:
        if weekly_candidates and store_candidates:
            join_key = weekly_candidates[0]
            store = store.rename(columns={store_candidates[0]: join_key})
            
    if not join_key:
        join_key = 'store_id'
        if len(store.columns) > 0:
            store = store.rename(columns={store.columns[0]: join_key})
        if len(weekly.columns) > 1:
            weekly = weekly.rename(columns={weekly.columns[1]: join_key})

    overlap_cols = [c for c in store.columns if c in weekly.columns and c != join_key]
    weekly_clean = weekly.drop(columns=overlap_cols, errors='ignore')
    
    merged = pd.merge(weekly_clean, store, on=join_key, how='inner')
    return merged, join_key

def conform_merged_dataframe(df, join_key):
    """Fills structural gaps in merged data to prevent dashboard charting crashes."""
    column_defaults = {
        'week_start_date': '01-01-2026', 'region': 'Unknown Region', 'city': 'Unknown City',
        'store_format': 'Standard', 'product_category': 'General', 'footfall': 0,
        'transactions': 0, 'units_sold': 0, 'gross_sales': 0.0, 'discount_amount': 0.0,
        'net_sales': 0.0, 'sales_target': 0.0, 'inventory_on_hand': 0, 'stockouts': 0,
        'returns_amount': 0.0, 'customer_rating': 5, 'marketing_spend': 0
    }
    
    rename_map = {
        'store': 'store_name',
        'store_id': 'store_name' if 'store_name' not in df.columns else 'store_id'
    }
    df = df.rename(columns=rename_map)
    
    for col, default in column_defaults.items():
        if col not in df.columns:
            df[col] = default
            
    numeric_cols = [
        'footfall', 'transactions', 'units_sold', 'gross_sales', 
        'discount_amount', 'net_sales', 'sales_target', 
        'inventory_on_hand', 'stockouts', 'returns_amount', 
        'customer_rating', 'marketing_spend'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    if 'week_start_date' in df.columns:
        parsed_dates = pd.to_datetime(df['week_start_date'], dayfirst=True, errors='coerce')
        parsed_dates = parsed_dates.fillna(pd.to_datetime('2026-01-01'))
        df['week_start_date'] = parsed_dates.dt.strftime('%d-%m-%Y')
        
    return df

# 6. Sidebar File Integration Segment
st.sidebar.title("📁 File Integration")
st.sidebar.markdown("Upload both store records and weekly transactional records below.")

store_file = st.sidebar.file_uploader("1. Upload Store Master (CSV/XLSX)", type=["csv", "xlsx"])
weekly_file = st.sidebar.file_uploader("2. Upload Retail Weekly Status (CSV/XLSX)", type=["csv", "xlsx"])

# 7. Sidebar Template Downloaders
st.sidebar.markdown("---")
st.sidebar.subheader("Template Downloads")

store_csv = convert_df_to_csv(generate_mock_store_master())
st.sidebar.download_button(
    label="⬇️ Download store_master Template",
    data=store_csv,
    file_name="store_master_template.csv",
    mime="text/csv"
)

weekly_csv = convert_df_to_csv(generate_mock_retail_weekly_status(generate_mock_store_master()))
st.sidebar.download_button(
    label="⬇️ Download retail_weekly_status Template",
    data=weekly_csv,
    file_name="retail_weekly_status_template.csv",
    mime="text/csv"
)

# 8. Data Ingestion Gatekeeping Logic (No mock fallbacks)
data_loaded = False
merged_df = pd.DataFrame()

if store_file is not None and weekly_file is not None:
    store_df = load_uploaded_file(store_file)
    weekly_df = load_uploaded_file(weekly_file)
    
    if store_df is not None and weekly_df is not None:
        # Process files through normalized merge pipeline
        merged_df, join_key = align_and_merge(weekly_df, store_df)
        merged_df = conform_merged_dataframe(merged_df, join_key)
        data_loaded = True

# 9. Sidebar Filter Interface (Conditionally displayed only when data is loaded)
if data_loaded:
    st.sidebar.title("🔍 Operations Filters")

    def build_multi_select(column_name, display_label):
        if column_name not in merged_df.columns:
            return []
        raw_vals = merged_df[column_name].dropna().unique()
        try:
            if column_name == 'week_start_date':
                unique_vals = sorted(
                    list(raw_vals),
                    key=lambda x: pd.to_datetime(x, format='%d-%m-%Y', errors='coerce')
                )
            else:
                unique_vals = sorted(list(raw_vals))
        except TypeError:
            unique_vals = sorted(list(raw_vals), key=lambda x: str(x))

        selected = st.sidebar.multiselect(
            label=display_label,
            options=unique_vals,
            placeholder="All values selected"
        )
        return selected

    selected_weeks = build_multi_select('week_start_date', 'Filter by Week')
    selected_regions = build_multi_select('region', 'Filter by Region')
    selected_cities = build_multi_select('city', 'Filter by City')
    selected_stores = build_multi_select('store_name', 'Filter by Store Name')
    selected_formats = build_multi_select('store_format', 'Filter by Store Format')
    selected_categories = build_multi_select('product_category', 'Filter by Product Category')

    # Apply Filters
    filtered_df = merged_df.copy()
    if selected_weeks:
        filtered_df = filtered_df[filtered_df['week_start_date'].isin(selected_weeks)]
    if selected_regions:
        filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]
    if selected_cities:
        filtered_df = filtered_df[filtered_df['city'].isin(selected_cities)]
    if selected_stores:
        filtered_df = filtered_df[filtered_df['store_name'].isin(selected_stores)]
    if selected_formats:
        filtered_df = filtered_df[filtered_df['store_format'].isin(selected_formats)]
    if selected_categories:
        filtered_df = filtered_df[filtered_df['product_category'].isin(selected_categories)]
else:
    filtered_df = pd.DataFrame()

# 10. Main Application Interface Header
st.title("📊 Retail Sales Intelligence Dashboard")
st.markdown("Multi-store operational tracking pipeline synthesizing **Weekly Status** and **Store Master** records.")

# 11. Performance KPI Section (Displays '-' when no dataset is loaded)
if data_loaded and not filtered_df.empty:
    total_net_sales = filtered_df['net_sales'].sum()
    total_gross_sales = filtered_df['gross_sales'].sum()
    total_sales_target = filtered_df['sales_target'].sum()
    total_transactions = filtered_df['transactions'].sum()
    total_returns = filtered_df['returns_amount'].sum()
    total_discounts = filtered_df['discount_amount'].sum()
    
    target_achievement = (total_net_sales / total_sales_target * 100) if total_sales_target > 0 else 0.0
    atv = (total_net_sales / total_transactions) if total_transactions > 0 else 0.0
    return_rate = (total_returns / total_gross_sales * 100) if total_gross_sales > 0 else 0.0
    discount_rate = (total_discounts / total_gross_sales * 100) if total_gross_sales > 0 else 0.0

    net_sales_val = format_indian_currency(total_net_sales)
    target_val = f"{target_achievement:.1f}%"
    atv_val = format_indian_currency(atv)
    return_val = f"{return_rate:.2f}%"
    discount_val = f"{discount_rate:.2f}%"
else:
    net_sales_val = "-"
    target_val = "-"
    atv_val = "-"
    return_val = "-"
    discount_val = "-"

kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
with kpi_col1:
    st.metric(label="Net Sales", value=net_sales_val)
with kpi_col2:
    st.metric(label="Target Achievement (%)", value=target_val)
with kpi_col3:
    st.metric(label="Average Transaction Value (ATV)", value=atv_val)
with kpi_col4:
    st.metric(label="Return Rate (%)", value=return_val)
with kpi_col5:
    st.metric(label="Discount Rate (%)", value=discount_val)

st.markdown("---")

# 12. Visualizations, Insights and Export (Rendered conditionally on load state)
if data_loaded and not filtered_df.empty:
    chart_row1_col1, chart_row1_col2 = st.columns(2)
    
    with chart_row1_col1:
        df_week = filtered_df.groupby('week_start_date')['net_sales'].sum().reset_index()
        df_week['date_parsed'] = pd.to_datetime(df_week['week_start_date'], format='%d-%m-%Y', errors='coerce')
        df_week = df_week.sort_values(by='date_parsed')
        df_week['net_sales_formatted'] = df_week['net_sales'].apply(format_indian_currency)
        
        fig_trend = px.line(
            df_week, x='week_start_date', y='net_sales', 
            title='Weekly Net Sales Trend', markers=True, template='plotly_white',
            custom_data=['net_sales_formatted']
        )
        fig_trend.update_layout(yaxis=dict(tickprefix="₹"))
        fig_trend.update_traces(hovertemplate="Week: %{x}<br>Net Sales: %{customdata[0]}")
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with chart_row1_col2:
        df_region = filtered_df.groupby('region')['net_sales'].sum().reset_index()
        df_region['net_sales_formatted'] = df_region['net_sales'].apply(format_indian_currency)
        
        fig_region = px.bar(
            df_region, x='region', y='net_sales', 
            title='Sales by Region', color='region', template='plotly_white',
            custom_data=['net_sales_formatted']
        )
        fig_region.update_layout(yaxis=dict(tickprefix="₹"))
        fig_region.update_traces(hovertemplate="Region: %{x}<br>Net Sales: %{customdata[0]}")
        st.plotly_chart(fig_region, use_container_width=True)

    chart_row2_col1, chart_row2_col2 = st.columns(2)
    
    with chart_row2_col1:
        df_category = filtered_df.groupby('product_category')['net_sales'].sum().reset_index()
        df_category['net_sales_formatted'] = df_category['net_sales'].apply(format_indian_currency)
        
        fig_category = px.pie(
            df_category, names='product_category', values='net_sales', 
            hole=0.4, title='Sales Share by Product Category', template='plotly_white',
            custom_data=['net_sales_formatted']
        )
        fig_category.update_traces(
            textinfo='percent+label',
            hovertemplate="%{label}<br>Net Sales: %{customdata[0]}<br>%{percent}"
        )
        st.plotly_chart(fig_category, use_container_width=True)
        
    with chart_row2_col2:
        df_store = (
            filtered_df.groupby('store_name')['net_sales']
            .sum().reset_index().sort_values(by='net_sales', ascending=True).tail(10)
        )
        df_store['net_sales_formatted'] = df_store['net_sales'].apply(format_indian_currency)
        
        fig_store = px.bar(
            df_store, x='net_sales', y='store_name', orientation='h',
            title='Top 10 Stores by Net Sales', color='net_sales',
            color_continuous_scale='Blues', template='plotly_white',
            custom_data=['net_sales_formatted']
        )
        fig_store.update_layout(
            xaxis=dict(tickprefix="₹"),
            margin=dict(l=160, r=20, t=40, b=40)
        )
        fig_store.update_traces(hovertemplate="Store: %{y}<br>Net Sales: %{customdata[0]}")
        st.plotly_chart(fig_store, use_container_width=True)

    # Stockout risk visual scatter
    st.subheader("Inventory Levels vs. Store Demand")
    max_val = max(filtered_df['inventory_on_hand'].max(), filtered_df['units_sold'].max())
    
    plot_df = filtered_df.copy()
    plot_df['marker_size'] = plot_df['stockouts'].clip(lower=0) * 6 + 8
    
    fig_stockout = px.scatter(
        plot_df, x='inventory_on_hand', y='units_sold',
        color='product_category', size='marker_size', 
        hover_data=['store_name', 'city', 'stockouts'],
        title='Stockout Risk Analysis (On Hand Inventory vs. Units Sold, sized by Stockouts)',
        labels={'inventory_on_hand': 'Inventory On Hand (Units)', 'units_sold': 'Units Sold (Volume)', 'stockouts': 'Stockouts Count'},
        template='plotly_white'
    )
    fig_stockout.add_shape(
        type="line", x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color="Red", width=1.5, dash="dash")
    )
    st.plotly_chart(fig_stockout, use_container_width=True)

    st.markdown("---")

    # Automated Business Insights
    st.subheader("🤖 Automated Business Insights")
    compiled_insights = []

    region_sales = filtered_df.groupby('region')['net_sales'].sum()
    if not region_sales.empty:
        best_region = region_sales.idxmax()
        worst_region = region_sales.idxmin()
        compiled_insights.append(f"🌟 **Leading Region**: **{best_region}** leads with a total of **{format_indian_currency(region_sales[best_region])}** in net sales.")
        compiled_insights.append(f"⚠️ **Trailing Region**: **{worst_region}** shows the lowest sales volume with **{format_indian_currency(region_sales[worst_region])}**.")
    
    store_perf = filtered_df.groupby('store_name').agg({'net_sales': 'sum', 'sales_target': 'sum'}).reset_index()
    store_perf['Target Gap'] = store_perf['net_sales'] - store_perf['sales_target']
    underperforming = store_perf[store_perf['Target Gap'] < 0].sort_values(by='Target Gap')
    
    if not underperforming.empty:
        top_underperforming = underperforming.head(3)
        store_items = [f"**{row['store_name']}** (Gap: **{format_indian_currency(abs(row['Target Gap']))}**)" for _, row in top_underperforming.iterrows()]
        compiled_insights.append(f"📉 **Target Gaps**: The following store locations finished below targets: {', '.join(store_items)}.")
    else:
        compiled_insights.append("🎉 **Target Performance**: All store locations within current parameters successfully met operational targets.")
        
    cat_returns = filtered_df.groupby('product_category').agg({'gross_sales': 'sum', 'returns_amount': 'sum'}).reset_index()
    cat_returns['Return Rate'] = (cat_returns['returns_amount'] / cat_returns['gross_sales']) * 100
    if not cat_returns.empty:
        highest_return_cat = cat_returns.sort_values(by='Return Rate', ascending=False).iloc[0]
        compiled_insights.append(f"🔄 **Return Exposure**: The **{highest_return_cat['product_category']}** category registers the highest return rate at **{highest_return_cat['Return Rate']:.2f}%** (amounting to **{format_indian_currency(highest_return_cat['returns_amount'])}**).")

    critical_stockouts = filtered_df[filtered_df['stockouts'] > 0]
    if not critical_stockouts.empty:
        compiled_insights.append(f"🚨 **Stockout Events**: Identified **{critical_stockouts['stockouts'].sum()}** stockout instances within the current filter range. Action is suggested to maintain consistent product availability.")
        
    for item in compiled_insights:
        st.markdown(item)

    st.markdown("---")

    # View and Insights Export Features
    st.subheader("📥 Export Filtered Views & Insights")
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        filtered_csv = convert_df_to_csv(filtered_df)
        st.download_button(
            label="Download Filtered Joined View as CSV",
            data=filtered_csv,
            file_name='joined_retail_sales_output.csv',
            mime='text/csv',
            use_container_width=True
        )
        
    with export_col2:
        raw_text_insights = "\n".join([text.replace("**", "") for text in compiled_insights])
        st.download_button(
            label="Download Automated Business Insights as TXT",
            data=raw_text_insights,
            file_name='retail_business_insights_summary.txt',
            mime='text/plain',
            use_container_width=True
        )

else:
    # App is awaiting dataset upload
    if not data_loaded:
        st.info("👋 **Awaiting Data Ingestion**: Please upload both the **Store Master** and the **Retail Weekly Status** files in the sidebar to activate interactive filters, charts, and business insights.")
    elif filtered_df.empty:
        st.warning("⚠️ **Filter Conflict**: No matching results correspond to the selected filter criteria. Please widen your filters in the sidebar.")
