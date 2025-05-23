import streamlit as st # type: ignore
import pandas as pd
import plotly.express as px # type: ignore

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv('ai_solutions_web_sales_logs.csv', parse_dates=['date_of_sale'], dayfirst=True)
    return df

df = load_data()

st.markdown("# Customer Engagement 🗨️")
st.sidebar.markdown("# Customer Engagement 🗨️")

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

filtered_data = df[
    (df['customer_country'].isin(customer_country))
]

# KPIs
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("Total Engagements", filtered_data.shape[0])
with kpi2:
    st.metric("Unique Customers", filtered_data['ip_address'].nunique())
with kpi3:
    st.metric("Engagement Types", filtered_data['customer_interaction'].nunique())

# Engagement Over Time (Monthly)
# st.header("Engagements Over Time")
engagements_over_time = (
    filtered_data
    .set_index('date_of_sale')
    .resample('M')['customer_interaction']
    .count()
    .reset_index()
)
engagements_over_time['month'] = engagements_over_time['date_of_sale'].dt.strftime('%Y-%m')

fig1 = px.line(
    engagements_over_time,
    x='month',
    y='customer_interaction',
    markers=True,
    labels={'customer_interaction': 'Number of Engagements', 'month': 'Month'},
    title='Engagements Over Time'
)
fig1.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig1, use_container_width=True)

# Engagement by Type
Sec1, Sec2 = st.columns([2, 2.5])
with Sec1:
    # st.subheader("Engagement by Type")
    engagement_type_counts = filtered_data['customer_interaction'].value_counts()
    fig2 = px.pie(
        names=engagement_type_counts.index,
        values=engagement_type_counts.values,
        title="Engagement by Type",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    fig2.update_traces(textinfo='percent+label', textfont_size=14)
    st.plotly_chart(fig2, use_container_width=True)

with Sec2:
    # st.subheader("Top Countries by Engagement")
    country_engagement = filtered_data['customer_country'].value_counts().head(10)
    fig3 = px.bar(
        x=country_engagement.values,
        y=country_engagement.index,
        orientation='h',
        labels={'x': 'Number of Engagements', 'y': 'Country'},
        color=country_engagement.values,
        color_continuous_scale='viridis',
        title="Top Countries by Engagement"
    )
    fig3.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)
    
    
Col1, Col2 = st.columns([2, 2])

with Col1:
    # Engagement by Product (using Plotly)
    # st.header("Engagement by Product")
    product_engagement = (
        filtered_data.groupby('product_sold')['customer_interaction']
        .count()
        .sort_values(ascending=False)
    )
    fig4 = px.bar(
        x=product_engagement.index,
        y=product_engagement.values,
        labels={'x': 'Product', 'y': 'Number of Engagements'},
        color=product_engagement.values,
        color_continuous_scale='viridis',
        title="Engagement by Product"
    )
    fig4.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig4, use_container_width=True)

with Col2:
    # Engagement by Job Type (using Plotly)
    if 'job_type_requested' in filtered_data.columns:
        # st.header("Engagement by Job Type")
        job_engagement = filtered_data['job_type_requested'].value_counts()
        fig5 = px.bar(
            x=job_engagement.index,
            y=job_engagement.values,
            labels={'x': 'Job Type', 'y': 'Number of Engagements'},
            color=job_engagement.values,
            color_continuous_scale='viridis',
            title="Engagement by Job Type"
        )
        fig5.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig5, use_container_width=True)

# Show raw data
with st.expander("Show Raw Engagement Data"):
    st.dataframe(filtered_data)
    st.download_button("Export Data as CSV", data=filtered_data.to_csv(index=False), file_name="filtered_data.csv")

