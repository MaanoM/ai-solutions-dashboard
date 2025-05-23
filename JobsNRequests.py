import streamlit as st # type: ignore
import pandas as pd
import plotly.express as px # type: ignore
import time

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

st.markdown("# Job Types & Requests ❄️")
st.sidebar.markdown("# Job Types & Requests ❄️")

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

# Apply filters
filtered_data = df[
    (df['customer_country'].isin(customer_country))
]

# --- KPIs ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Requests", filtered_data.shape[0])
with col2:
    unique_customers = filtered_data['ip_address'].nunique() if 'ip_address' in filtered_data.columns else 0
    st.metric("Unique Customers", unique_customers)
with col3:
    unique_job_types = filtered_data['job_type_requested'].nunique() if 'job_type_requested' in filtered_data.columns else 0
    st.metric("Distinct Job Types Requested", unique_job_types)
    

Section1, Section2 = st.columns([1.69,2.31])
with Section1:
    # --- Donut Chart: Distribution of Job Types Requested (Plotly) ---
    # st.subheader("Distribution of Job Types Requested")
    if 'job_type_requested' in filtered_data.columns:
        job_counts = filtered_data[filtered_data['job_type_requested'] != 'N/A']['job_type_requested'].value_counts().reset_index()
        job_counts.columns = ['job_type_requested', 'count']
        fig_donut = px.pie(
            job_counts,
            names='job_type_requested',
            values='count',
            title="Distribution of Job Types Requested",
            color_discrete_sequence=px.colors.sequential.Viridis,
            hole=0.5  # This makes it a donut chart
        )
        fig_donut.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_donut, use_container_width=True)

with Section2:
    # --- Interactive Line Chart: Monthly Requests Over Time ---
    # st.subheader("Monthly Requests Over Time")
    if 'timestamp' in filtered_data.columns:
        time_data = filtered_data.copy()
        time_data['month'] = pd.to_datetime(time_data['timestamp']).dt.to_period('M').dt.to_timestamp()
        requests_over_month = time_data.groupby('month').size().reset_index(name='num_requests')
        fig_line = px.line(
            requests_over_month,
            x='month',
            y='num_requests',
            markers=True,
            title="Monthly Requests Over Time",
            labels={'month': 'Month', 'num_requests': 'Number of Requests'},
            hover_data={'month': True, 'num_requests': True}
        )
        fig_line.update_traces(hovertemplate='Month: %{x|%b %Y}<br>Requests: %{y}')
        fig_line.update_layout(xaxis_tickformat='%b %Y')
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("The 'timestamp' column is missing from the dataset.")

# --- Bar Charts: Job Types Requested & Scheduled Demos/Events (Side by Side) ---
st.subheader("Job Types & Scheduled Demos/Events")
colA, colB = st.columns(2)

with colA:
    # st.markdown("**Job Types Requested**")
    if 'job_type_requested' in filtered_data.columns:
        job_data = filtered_data[filtered_data['job_type_requested'] != 'N/A']
        job_counts = job_data['job_type_requested'].value_counts().reset_index()
        job_counts.columns = ['job_type_requested', 'count']
        fig3 = px.bar(
            job_counts,
            x='job_type_requested',
            y='count',
            color='count',
            color_continuous_scale='viridis',
            labels={'job_type_requested': 'Job Type', 'count': 'Number of Requests'},
            title="Job Types Requested"
        )
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.error("The 'job_type_requested' column is missing from the dataset.")

with colB:
    # st.markdown("**Scheduled Demos and Promotional Events Requests**")
    if 'customer_interaction' in filtered_data.columns:
        demo_events = filtered_data[filtered_data['customer_interaction'].str.contains('Demo|Event', case=False, na=False)]
        demo_counts = demo_events['customer_interaction'].value_counts().reset_index()
        demo_counts.columns = ['interaction_type', 'count']
        fig4 = px.bar(
            demo_counts,
            x='interaction_type',
            y='count',
            color='count',
            color_continuous_scale='viridis',
            labels={'interaction_type': 'Interaction Type', 'count': 'Number of Requests'},
            title="Scheduled Demos and Promotional Events Requests"
        )
        fig4.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.error("The 'customer_interaction' column is missing from the dataset.")

# --- Requests for AI-powered Virtual Assistant ---
st.header("Requests for AI-powered Virtual Assistant")
if 'customer_interaction' in filtered_data.columns:
    ai_requests = filtered_data[filtered_data['customer_interaction'].str.contains('AI Assistant', case=False, na=False)]
    st.write(f"Total AI Assistant Requests: {ai_requests.shape[0]}")
    st.dataframe(ai_requests[['timestamp', 'ip_address', 'customer_country', 'salesperson']].sort_values(by='timestamp', ascending=False).head(10))
else:
    st.warning("The 'customer_interaction' column is missing from the dataset.")
    
st.download_button("Export Data as CSV", data=filtered_data.to_csv(index=False), file_name="filtered_data.csv")