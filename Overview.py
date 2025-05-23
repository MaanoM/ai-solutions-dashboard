import streamlit as st  # type: ignore
import pandas as pd
import plotly.express as px  # type: ignore
from geopy.geocoders import Nominatim  # type: ignore
import time
from datetime import datetime

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv('ai_solutions_web_sales_logs.csv', parse_dates=['timestamp', 'date_of_sale'], dayfirst=True)
    return df

start = time.time()
# Load data with a spinner
with st.spinner("Loading data..."):
    df = load_data()
end = time.time()
Loading_time = end - start
st.success("Data loaded successfully! Loaded Data in: {:.2f} seconds 🥳".format(Loading_time))

st.markdown("# Overview 🎈")
st.sidebar.markdown("# Overview 🎈")

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

customer_country = st.sidebar.multiselect(
    "Customer Country",
    options=df['customer_country'].unique(),
    default=df['customer_country'].unique(),
    help="Select one or more countries to filter the data."
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

# Define target sales (example: 100,000, adjust as needed)
SALES_TARGET = 1000000000

# Get current and previous year
current_year = datetime.now().year
last_year = current_year - 1

# Filter data for current and last year
filtered_data['year'] = filtered_data['date_of_sale'].dt.year
current_year_data = filtered_data[filtered_data['year'] == current_year]
last_year_data = filtered_data[filtered_data['year'] == last_year]

# KPIs
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns([2.25,1,1.25,0.9,1.25])

with kpi1:
    total_sales = filtered_data['cost'].sum()
    delta_sales = ((total_sales - SALES_TARGET) / SALES_TARGET) * 100 if SALES_TARGET else 0
    st.metric(
        "Total Revenue",
        f"${total_sales:,.2f}",
        f"{delta_sales:+.1f}% vs Target"
    )

with kpi2:
    ytd_interactions = current_year_data.shape[0]
    last_ytd_interactions = last_year_data.shape[0]
    delta_interactions = ytd_interactions - last_ytd_interactions
    delta_pct = (delta_interactions / last_ytd_interactions * 100) if last_ytd_interactions else 0
    st.metric(
        "YTD Interactions",
        ytd_interactions,
        f"{delta_pct:+.1f}% vs LY"
    )

with kpi3:
    ytd_customers = current_year_data['ip_address'].nunique()
    last_ytd_customers = last_year_data['ip_address'].nunique()
    delta_customers = ytd_customers - last_ytd_customers
    delta_customers_pct = (delta_customers / last_ytd_customers * 100) if last_ytd_customers else 0
    st.metric(
        "YTD Unique Customers",
        ytd_customers,
        f"{delta_customers_pct:+.1f}% vs LY"
    )

with kpi4:
    st.metric("Unique Countries", filtered_data['customer_country'].nunique())
    
with kpi5:
    best_product = (
        filtered_data.groupby('product_sold')['cost']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    if not best_product.empty:
        best_name = best_product.loc[0, 'product_sold']
        best_sales = best_product.loc[0, 'cost']
        if len(best_product) > 1:
            next_best_sales = best_product.loc[1, 'cost']
            delta = best_sales - next_best_sales
            delta_pct = (delta / next_best_sales * 100) if next_best_sales else 0
            delta_str = f"{delta_pct:+.1f}% vs Next"
        else:
            delta_str = "Top Product"
        st.metric(
            "Best Performing Product",
            best_name,
            delta_str
        )
    else:
        st.metric("Best Performing Product", "N/A", "N/A")
    
# Sales Over Time (Interactive with Plotly)

st.header("Monthly Sales Over Time")
# Group by year and month for monthly aggregation
sales_over_time = (
    filtered_data
    .set_index('date_of_sale')
    .resample('M')['cost']
    .sum()
    .reset_index()
)
sales_over_time['month'] = sales_over_time['date_of_sale'].dt.strftime('%Y-%m')

fig3 = px.line(
    sales_over_time,
    x='month',
    y='cost',
    markers=True,
    labels={'month': 'Month', 'cost': 'Total Sales'},
    hover_data={'month': True, 'cost': ':.2f'}
)
fig3.update_traces(hovertemplate='Month: %{x}<br>Total Sales: %{y:.2f}')
fig3.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=sales_over_time['month'][::max(1, len(sales_over_time)//8)],
        ticktext=sales_over_time['month'][::max(1, len(sales_over_time)//8)],
        tickangle=45
    ),
    margin=dict(l=20, r=20, t=40, b=40)
)
st.plotly_chart(fig3, use_container_width=True)

Sec1, Sec2 = st.columns([1.75, 2.25])
with Sec1:
    st.header("Customer Country Distribution")
    country_counts = filtered_data['customer_country'].value_counts().reset_index()
    country_counts.columns = ['country', 'count']
    fig = px.bar(
        country_counts,
        x='country',
        y='count',
        color='count',
        color_continuous_scale='viridis',
        labels={'country': 'Country', 'count': 'Number of Interactions'},
    )
    fig.update_layout(xaxis_tickangle=45, margin=dict(l=20, r=20, t=40, b=40))
    st.plotly_chart(fig, use_container_width=True)
with Sec2:
    st.header("Top 5 Customer Interaction Types")
    interaction_counts = (
        filtered_data['customer_interaction']
        .value_counts()
        .head(5)
        .reset_index()
    )
    interaction_counts.columns = ['interaction_type', 'count']
    fig2 = px.bar(
        interaction_counts,
        x='count',
        y='interaction_type',
        orientation='h',
        color='count',
        color_continuous_scale='viridis',
        labels={'interaction_type': 'Interaction Type', 'count': 'Number of Interactions'},
    )
    fig2.update_layout(margin=dict(l=20, r=20, t=40, b=40))
    st.plotly_chart(fig2, use_container_width=True)

Sec3, Sec4 = st.columns([1.69, 2.31])
with Sec3:
    # Product Popularity (Pie Chart)
    st.header("Product Popularity")
    product_counts = filtered_data['product_sold'].value_counts().reset_index()
    product_counts.columns = ['product', 'count']
    fig4 = px.pie(
        product_counts,
        names='product',
        values='count',
        color_discrete_sequence=px.colors.sequential.Viridis,
        hole=0.4,
    )
    fig4.update_traces(textinfo='percent+label')
    fig4.update_layout(margin=dict(l=20, r=20, t=40, b=40))
    st.plotly_chart(fig4, use_container_width=True)
with Sec4:
    # Sales by Salesperson (Bar Graph)
    st.header("Sales by Salesperson")
    salesperson_sales = (
        filtered_data.groupby('salesperson')['cost']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig5 = px.bar(
        salesperson_sales,
        x='salesperson',
        y='cost',
        color='cost',
        color_continuous_scale='viridis',
        labels={'salesperson': 'Salesperson', 'cost': 'Total Sales'},
    )
    fig5.update_layout(
        xaxis_tickangle=45,
        title='Sales Distribution by Salesperson',
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig5, use_container_width=True)

# Location Insights Map using customer_country
st.header("Customer Locations Map")
# Use pycountry and pycountry_convert to get approximate lat/lon for each country

country_counts = filtered_data['customer_country'].value_counts().reset_index()
country_counts.columns = ['country', 'count']

geolocator = Nominatim(user_agent="country_locator")
def get_country_latlon(country):
    try:
        location = geolocator.geocode(country)
        if location:
            return pd.Series({'lat': location.latitude, 'lon': location.longitude})
    except Exception:
        pass
    return pd.Series({'lat': None, 'lon': None})

country_counts[['lat', 'lon']] = country_counts['country'].apply(get_country_latlon)
map_df = country_counts.dropna(subset=['lat', 'lon'])
if not map_df.empty:
    st.map(map_df[['lat', 'lon', 'count']])
else:
    st.warning("Could not geocode any countries for the map.")
    
with st.expander("Show Raw Data"):
    st.dataframe(filtered_data)
    
st.download_button("Export Data as CSV", data=filtered_data.to_csv(index=False), file_name="filtered_data.csv")
