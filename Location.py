import streamlit as st # type: ignore
import pandas as pd
import plotly.express as px # type: ignore
from geopy.geocoders import Nominatim # type: ignore


# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv('ai_solutions_web_sales_logs.csv', parse_dates=['date_of_sale'], dayfirst=True)
    return df

df = load_data()

st.markdown("# Location Analysis 📍")
st.sidebar.markdown("# Location Analysis 📍")

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

filtered_data = df[df['customer_country'].isin(customer_country)]

# KPIs
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("Total Revenue", f"${filtered_data['cost'].sum():,.2f}")
with kpi2:
    st.metric("Countries", filtered_data['customer_country'].nunique())
with kpi3:
    st.metric("Total Transactions", filtered_data.shape[0])


Col1, Col2 = st.columns(2)
with Col1:
    # Revenue by Country
    st.header("Revenue by Country")
    revenue_by_country = filtered_data.groupby('customer_country')['cost'].sum().sort_values(ascending=False)
    fig1 = px.bar(
        revenue_by_country,
        x=revenue_by_country.values,
        y=revenue_by_country.index,
        orientation='h',
        labels={'x': 'Revenue', 'y': 'Country'},
        color=revenue_by_country.values,
        color_continuous_scale='viridis'
    )
    fig1.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
    st.plotly_chart(fig1, use_container_width=True)
with Col2:
    # Engagements by Country
    st.header("Engagements by Country")
    engagements_by_country = filtered_data['customer_country'].value_counts()
    fig2 = px.bar(
        engagements_by_country,
        x=engagements_by_country.values,
        y=engagements_by_country.index,
        orientation='h',
        labels={'x': 'Number of Engagements', 'y': 'Country'},
        color=engagements_by_country.values,
        color_continuous_scale='viridis'
    )
    fig2.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
    st.plotly_chart(fig2, use_container_width=True)

Part1, Part2 = st.columns(2)
with Part1:
    # Top Products by Selected Country
    st.header("Top Products by Country")

    # Dropdown to select a country from filtered countries
    selected_country = st.selectbox(
        "Select Country",
        options=revenue_by_country.index,
        index=0 if len(revenue_by_country) > 0 else None
    )

    if selected_country:
        st.subheader(f"{selected_country}")
        prod_counts = filtered_data[filtered_data['customer_country'] == selected_country]['product_sold'].value_counts()
        if not prod_counts.empty:
            fig = px.bar(
                prod_counts,
                x=prod_counts.index,
                y=prod_counts.values,
                labels={'x': 'Product', 'y': 'Count'},
                color=prod_counts.values,
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=45, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No product data available for this country.")
        
with Part2:
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

# Show raw data
with st.expander("Show Raw Location Data"):
    st.dataframe(filtered_data)
    st.download_button("Export Data as CSV", data=filtered_data.to_csv(index=False), file_name="filtered_data.csv")