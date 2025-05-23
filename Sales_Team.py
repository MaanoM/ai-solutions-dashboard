import streamlit as st  # type: ignore
import pandas as pd
import os
import plotly.express as px  # type: ignore
import plotly.graph_objects as go # type: ignore
from sklearn.cluster import KMeans
import time # type: ignore

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv('ai_solutions_web_sales_logs.csv', parse_dates=['timestamp', 'date_of_sale'], dayfirst=True)
    return df

df = load_data()

st.markdown("# Sales Team Performance 🎉")
st.sidebar.markdown("# Sales Team Performance 🎉")

# Sidebar filters with "Select All" functionality
st.sidebar.header("Filters")
st.sidebar.write("Select filters to customize the data view. For example, choose a country or salesperson.")
if st.sidebar.button("Reset Filters"):
    st.experimental_rerun()
    
with st.sidebar.expander("Help & Documentation"):
    st.write("""
    - Use the filters to customize your view.
    - Hover over charts for more details.
    - Click 'Export Data' to download results.
    """)
    
def multiselect_with_select_all(label, options, default):
    select_all = st.sidebar.checkbox(f"Select All {label}", value=True, key=f"all_{label}")
    if select_all:
        selected = st.sidebar.multiselect(label, options, default=options, key=label)
    else:
        selected = st.sidebar.multiselect(label, options, default=[], key=label)
    return selected

customer_country = multiselect_with_select_all(
    "Customer Country",
    options=df['customer_country'].unique(),
    default=df['customer_country'].unique()
)
salesperson = multiselect_with_select_all(
    "Salesperson",
    options=df['salesperson'].unique(),
    default=df['salesperson'].unique()
)
# Filter data based on sidebar selections
filtered_data = df[
    (df['customer_country'].isin(customer_country)) &
    (df['salesperson'].isin(salesperson))
]
# KPI Section: Sales Team Performance
kpi1, kpi2, kpi3, kpi4 = st.columns([2.5,1.5,1,1.25])

# Year to Date KPI: Compare current YTD vs last year's YTD (same date range)
today = pd.Timestamp.today()
start_of_year = pd.Timestamp(year=today.year, month=1, day=1)
start_of_last_year = pd.Timestamp(year=today.year - 1, month=1, day=1)
same_day_last_year = pd.Timestamp(year=today.year - 1, month=today.month, day=today.day)

# Check if filtered_data is empty or missing columns
if filtered_data.empty or 'date_of_sale' not in filtered_data.columns or 'cost' not in filtered_data.columns:
    ytd_sales = 0
    ytd_count = 0
    last_ytd_sales = 0
    last_ytd_count = 0
else:
    # Current YTD
    ytd_data = filtered_data[(filtered_data['date_of_sale'] >= start_of_year) & (filtered_data['date_of_sale'] <= today)]
    ytd_sales = ytd_data['cost'].sum()
    ytd_count = ytd_data['cost'].count()

    # Last year's YTD (same period)
    last_ytd_data = filtered_data[(filtered_data['date_of_sale'] >= start_of_last_year) & (filtered_data['date_of_sale'] <= same_day_last_year)]
    last_ytd_sales = last_ytd_data['cost'].sum()
    last_ytd_count = last_ytd_data['cost'].count()

# Calculate deltas
sales_delta = ytd_sales - last_ytd_sales
count_delta = ytd_count - last_ytd_count

with kpi1:
    sales_pct_delta = (sales_delta / last_ytd_sales * 100) if last_ytd_sales != 0 else 0
    st.metric(
        "Year to Date Revenue",
        f"${ytd_sales:,.2f}",
        delta=f"{sales_pct_delta:+.1f}%",
        delta_color="normal"  # green if up, red if down
    )

with kpi2:
    st.metric(
        "Year to Date Number of Sales",
        int(ytd_count),
        delta=int(count_delta),
        delta_color="normal"
    )
    

# Best Performing Salesperson
best_salesperson = (
    filtered_data.groupby('salesperson')['cost'].sum().idxmax()
    if not filtered_data.empty else "N/A"
)
best_salesperson_amount = (
    filtered_data.groupby('salesperson')['cost'].sum().max()
    if not filtered_data.empty else 0
)
with kpi3:
    st.metric("Best Salesperson", f"{best_salesperson}")
# Forecast Model Accuracy KPI
forecast_accuracy = 89.04  # Replace with dynamic calculation if available
with kpi4:
    st.metric("Forecast Model Accuracy", f"{forecast_accuracy:.2f}%")

# Section 2: Salesperson Performance
sales_data = df[df['salesperson'] != 'N/A']
sales_summary = sales_data.groupby('salesperson').agg(
    total_sales=('cost', 'sum'),
    number_of_sales=('cost', 'count'),
    average_sale=('cost', 'mean')
).reset_index()

col1, col2 = st.columns([2.5,1.5])

with col1:
    st.header("Monthly Sales Over Time")
    # Product filter for this plot
    product_options = ['All'] + list(filtered_data['product_sold'].unique())
    selected_product = st.selectbox(
        "Select Product for Monthly Sales Over Time",
        options=product_options,
        key="monthly_sales_product_filter"
    )
    if selected_product == 'All':
        filtered_monthly = filtered_data
    else:
        filtered_monthly = filtered_data[filtered_data['product_sold'] == selected_product]

    # Group by year and month for monthly aggregation
    filtered_monthly['year'] = filtered_monthly['date_of_sale'].dt.year
    filtered_monthly['month'] = filtered_monthly['date_of_sale'].dt.month

    # Get current and last year
    current_year = pd.Timestamp.today().year
    last_year = current_year - 1

    # Aggregate sales by year and month
    monthly_sales = (
        filtered_monthly
        .groupby(['year', 'month'])['cost']
        .sum()
        .reset_index()
    )

    # Prepare data for plotting
    months = range(1, 13)
    df_this_year = pd.DataFrame({'month': months})
    df_last_year = pd.DataFrame({'month': months})

    # For current year, only plot up to May (month 5)
    this_year_sales = monthly_sales[monthly_sales['year'] == current_year][['month', 'cost']].set_index('month').reindex(months, fill_value=0).reset_index()
    this_year_sales.loc[this_year_sales['month'] > 5, 'cost'] = None  # Hide after May

    last_year_sales = monthly_sales[monthly_sales['year'] == last_year][['month', 'cost']].set_index('month').reindex(months, fill_value=0).reset_index()

    # Calculate sales target: average of last year's monthly sales
    sales_target = last_year_sales['cost'].mean()

    # Prepare month labels
    month_labels = pd.date_range('2023-01-01', periods=12, freq='MS').strftime('%b')

    fig_ly = go.Figure()

    # Last year (blue)
    fig_ly.add_trace(go.Scatter(
        x=month_labels,
        y=last_year_sales['cost'],
        mode='lines+markers',
        name=f'{last_year} Sales',
        line=dict(color='royalblue', width=3),
        marker=dict(color='royalblue')
    ))

    # This year (green, only up to May)
    fig_ly.add_trace(go.Scatter(
        x=month_labels,
        y=this_year_sales['cost'],
        mode='lines+markers',
        name=f'{current_year} Sales',
        line=dict(color='green', width=3),
        marker=dict(color='green')
    ))

    # Sales target (red dashed)
    fig_ly.add_trace(go.Scatter(
        x=month_labels,
        y=[sales_target]*12,
        mode='lines',
        name='Sales Target (Last Year Avg)',
        line=dict(color='red', width=2, dash='dash')
    ))

    fig_ly.update_layout(
        title=f'Monthly Sales: {current_year} vs {last_year}',
        xaxis_title='Month',
        yaxis_title='Total Sales',
        legend_title_text='',
        margin=dict(l=20, r=20, t=40, b=40),
        xaxis=dict(tickmode='array', tickvals=month_labels, tickangle=45)
    )

    st.plotly_chart(fig_ly, use_container_width=True)

with col2:
    # Calculate a reasonable sales target: e.g., 10% above the average total sales
    avg_total_sales = sales_summary['total_sales'].mean()
    sales_target = avg_total_sales * 1.10  # 10% above average

    fig3 = px.bar(
        sales_summary,
        x='salesperson',
        y='total_sales',
        color='total_sales',
        color_continuous_scale='viridis',
        labels={'total_sales': 'Total Sales Amount', 'salesperson': 'Salesperson'},
        title='Total Sales by Salesperson'
    )

    # Add sales target as a red dashed line
    fig3.add_shape(
        type="line",
        x0=-0.5,
        x1=len(sales_summary['salesperson']) - 0.5,
        y0=sales_target,
        y1=sales_target,
        line=dict(color="red", width=2, dash="dash"),
        xref="x",
        yref="y"
    )
    fig3.add_annotation(
        x=len(sales_summary['salesperson']) - 1,
        y=sales_target,
        text=f"Sales Target (${sales_target:,.0f})",
        showarrow=False,
        yshift=10,
        font=dict(color="red", size=12),
        align="right"
    )

    st.plotly_chart(fig3, use_container_width=True)

st.header("Salesperson Performance")
st.dataframe(sales_summary)

# === Monthly Sales Forecast Section ===
st.header("Monthly Sales Forecast")

# Use the same salesperson filter as in your data section
forecast_salesperson = st.selectbox(
    "Select Salesperson for Forecast", 
    ['All'] + sales_summary['salesperson'].tolist(),
    key="forecast_salesperson"
)

# Determine which forecast files to load
if forecast_salesperson != 'All':
    forecast_file = f'monthly_forecast_{forecast_salesperson}.csv'
    actuals_file = f'monthly_actuals_{forecast_salesperson}.csv'
    if os.path.exists(forecast_file) and os.path.exists(actuals_file):
        forecast_df = pd.read_csv(forecast_file)
        actuals_df = pd.read_csv(actuals_file)
    else:
        st.warning("Not enough data for this salesperson's forecast.")
        forecast_df = None
        actuals_df = None
else:
    forecast_file = 'monthly_forecast.csv'
    actuals_file = 'monthly_actuals.csv'
    if os.path.exists(forecast_file) and os.path.exists(actuals_file):
        forecast_df = pd.read_csv(forecast_file)
        actuals_df = pd.read_csv(actuals_file)
    else:
        st.warning("Not enough data for overall forecast.")
        forecast_df = None
        actuals_df = None

if forecast_df is not None and actuals_df is not None:
    # Convert 'month' to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(actuals_df['month']):
        actuals_df['month'] = pd.PeriodIndex(actuals_df['month'], freq='M').to_timestamp()
    if not pd.api.types.is_datetime64_any_dtype(forecast_df['month']):
        forecast_df['month'] = pd.PeriodIndex(forecast_df['month'], freq='M').to_timestamp()

    # Actuals: plot all available
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=actuals_df['month'],
        y=actuals_df['cost'],
        mode='lines+markers',
        name='Actual Sales',
        line=dict(color='royalblue', width=3, dash='solid'),
        marker=dict(color='royalblue')
    ))

    # Forecasts: only Jan 2025 to May 2025
    forecast_mask = (forecast_df['month'] >= pd.Timestamp('2025-01-01')) & (forecast_df['month'] <= pd.Timestamp('2025-05-01'))
    forecast_2025 = forecast_df[forecast_mask]
    if not forecast_2025.empty:
        fig.add_trace(go.Scatter(
            x=forecast_2025['month'],
            y=forecast_2025['forecast'],
            mode='lines+markers',
            name='Forecast (Jan-May 2025)',
            line=dict(color='orange', width=3, dash='dash'),
            marker=dict(color='orange')
        ))

    fig.update_layout(
        title='Monthly Sales: Actual vs Forecast (Jan-May 2025)',
        xaxis_title='Month',
        yaxis_title='Sales',
        legend_title_text='',
        xaxis_tickformat='%Y-%m',
        xaxis_tickangle=45,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)
    
# === Weekly Sales Forecast Section ===
st.header("Weekly Sales Forecast (Next 4 Weeks)")

# Load weekly actuals and forecast
weekly_actuals_path = os.path.join("weekly_outputs", "weekly_actuals.csv")
weekly_forecast_path = os.path.join("weekly_outputs", "weekly_forecast.csv")

if os.path.exists(weekly_actuals_path) and os.path.exists(weekly_forecast_path):
    weekly_actuals = pd.read_csv(weekly_actuals_path)
    weekly_forecast = pd.read_csv(weekly_forecast_path)

    # Parse week start dates for plotting
    def week_start(week_str):
        return pd.to_datetime(week_str.split('/')[0])

    weekly_actuals['week_start'] = weekly_actuals['week'].apply(week_start)
    weekly_forecast['week_start'] = weekly_forecast['week'].apply(week_start)

    # Show only the last 8 weeks of actuals and next 4 weeks of forecast
    last_actuals = weekly_actuals.sort_values('week_start').tail(8)
    next_forecast = weekly_forecast.sort_values('week_start').head(4)

    # Plot
    fig_weekly = go.Figure()
    fig_weekly.add_trace(go.Scatter(
        x=last_actuals['week_start'],
        y=last_actuals['cost'],
        mode='lines+markers',
        name='Actual',
        line=dict(color='royalblue')
    ))
    fig_weekly.add_trace(go.Scatter(
        x=next_forecast['week_start'],
        y=next_forecast['forecast'],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='orange', dash='dash')
    ))
    fig_weekly.update_layout(
        xaxis_title="Week",
        yaxis_title="Sales",
        xaxis_tickformat='%Y-%m-%d',
        legend_title_text='',
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig_weekly, use_container_width=True)

    # Table: Next 4 weeks forecast
    st.subheader("Upcoming 4 Weeks Forecast")
    st.dataframe(
        next_forecast[['week', 'forecast']].rename(
            columns={'week': 'Week', 'forecast': 'Forecast Sales'}
        ),
        hide_index=True
    )

    # KPI: Next week forecast
    st.metric("Next Week Forecast", f"${next_forecast['forecast'].iloc[0]:,.2f}")

else:
    st.info("Weekly forecast data not available.")

Part3, Part4 = st.columns([2, 3])
with Part3:
    # === Sales Clustering by Region Section ===
    # st.header("Sales Clustering by Region")

    # Prepare data for clustering
    if 'Region' in df.columns and 'Sales' in df.columns:
        cluster_data = df.groupby('Region')['Sales'].sum().reset_index()
        sales_col = 'Sales'
        region_col = 'Region'
    else:
        # Fallback to customer_country and cost
        cluster_data = df.groupby('customer_country')['cost'].sum().reset_index()
        sales_col = 'cost'
        region_col = 'customer_country'

    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
    cluster_data['Cluster'] = kmeans.fit_predict(cluster_data[[sales_col]])

    # Visualize clusters with plotly
    fig = px.bar(
        cluster_data.sort_values('Cluster'),
        x=region_col,
        y=sales_col,
        color='Cluster',
        color_continuous_scale='viridis',
        labels={region_col: "Region", sales_col: "Total Sales", "Cluster": "Cluster Group"},
        title="Sales Clustering by Region"
    )
    fig.update_layout(
        xaxis_tickangle=45,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

with Part4:
    # Show cluster assignments as a table
    st.subheader("Region Cluster Assignments")
    st.dataframe(cluster_data.rename(
        columns={region_col: "Region", sales_col: "Total Sales", "Cluster": "Cluster Group"}
    ), hide_index=True)




# Section 4: Filter Sales Data
st.header("Filter Sales Forecast")
selected_salesperson = st.selectbox("Select Salesperson", ['All'] + sales_summary['salesperson'].tolist())
if selected_salesperson != 'All':
    filtered = sales_data[sales_data['salesperson'] == selected_salesperson]
else:
    filtered = sales_data
st.dataframe(filtered[['timestamp', 'product_sold', 'cost', 'customer_country', 'job_type_requested']].sort_values(by='timestamp', ascending=False).head(20))


# Download button for filtered data
section1, section2 = st.columns([1, 3])
with section1:
    st.download_button("Download Filtered Data", filtered.to_csv(index=False).encode('utf-8'), "filtered_sales_data.csv", "text/csv")
with section2:
    st.write("Download the filtered data as CSV.")
