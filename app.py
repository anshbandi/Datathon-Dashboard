import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

# -----------------------------------------------------------------------------
# 1. CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NEXUS | OMNI-DASHBOARD",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. REFINED CSS (Deep Void Style)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;600&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        /* DEEP VOID BACKGROUND */
        .stApp {
            background-color: #000000;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(20, 20, 40, 0.8) 0%, transparent 25%), 
                radial-gradient(circle at 85% 30%, rgba(0, 40, 40, 0.4) 0%, transparent 25%);
            background-attachment: fixed;
        }

        .block-container {
            padding-top: 4.5rem !important;
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* HEADERS */
        h1, h2, h3, .stMetricLabel {
            font-family: 'Rajdhani', sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #fff !important;
            text-shadow: 0 0 15px rgba(0, 245, 255, 0.4);
        }
        h3 {
            font-size: 1.2rem !important;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 5px;
            margin-bottom: 15px;
        }

        /* KPI CARDS */
        .kpi-card {
            background: rgba(10, 10, 15, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, #00F5FF, #BD00FF);
            opacity: 0;
            transition: opacity 0.3s;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.5);
            border-color: rgba(255, 255, 255, 0.2);
        }
        .kpi-card:hover::before { opacity: 1; }

        .kpi-value {
            font-family: 'Rajdhani', sans-serif;
            font-size: 2.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #FFFFFF 0%, #00F5FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .kpi-label {
            font-family: 'Inter', sans-serif;
            color: #888;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* CHART CONTAINERS */
        .stPlotlyChart, [data-testid="stDataFrame"] {
            background: rgba(10, 10, 15, 0.4);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data():
    try:
        base_path = r"C:\Users\dell\Desktop\Ansh Dashboard"
        orders_path = f"{base_path}\\Order_Details.csv"
        products_path = f"{base_path}\\Product_Details.csv"

        cols_to_load = ["Product ID", "Product Name", "Category", "Sub_Collection", "Unit Price ($)"]
        df_products = pd.read_csv(products_path, usecols=cols_to_load, low_memory=False)
        df_products = df_products.drop_duplicates(subset=["Product ID"])
        df_products = df_products.rename(columns={
            "Product ID": "product_id", "Product Name": "product_name", 
            "Category": "category", "Sub_Collection": "sub_collection", "Unit Price ($)": "unit_cost"
        })

        df_orders = pd.read_csv(orders_path, low_memory=False)
        df_orders = df_orders.rename(columns={
            "Product ID": "product_id", "Shipping Fee ($)": "shipping_fee", 
            "Quantity (Units)": "quantity_units", "Net Price ($)": "selling_price", 
            "Date": "date", "Customer Location": "customer_location", "Customer Age Group": "age_group"
        })

        df_orders['product_id'] = df_orders['product_id'].astype(str).str.strip()
        df_products['product_id'] = df_products['product_id'].astype(str).str.strip()
        df = pd.merge(df_orders, df_products, on='product_id', how='left')

        for col in ['selling_price', 'quantity_units', 'shipping_fee', 'unit_cost']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['total_revenue'] = (df['selling_price'] * df['quantity_units']) + df['shipping_fee']
        df['total_cost'] = df['unit_cost'] * df['quantity_units']
        df['total_profit'] = df['total_revenue'] - df['total_cost']
        df['margin_percent'] = np.where(df['total_revenue'] > 0, (df['total_profit'] / df['total_revenue']) * 100, 0)

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['month_year'] = df['date'].dt.strftime('%Y-%m')
        df['country'] = df['customer_location'].astype(str).apply(lambda x: x.split(',')[-1].strip() if ',' in x else x)
        df['category'] = df['category'].fillna("Other")
        df['sub_collection'] = df['sub_collection'].fillna("General")

        return df
    except Exception as e:
        st.error(f"Data Error: {e}")
        st.stop()

df = load_data()

# -----------------------------------------------------------------------------
# 4. SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("💠 NEXUS")
    st.markdown("---")
    
    avail_countries = sorted(df['country'].unique())
    sel_country = st.multiselect("🌍 Territory", avail_countries)
    
    avail_categories = sorted(df['category'].unique())
    sel_category = st.multiselect("📦 Category", avail_categories)

filtered_df = df.copy()
if sel_country:
    filtered_df = filtered_df[filtered_df['country'].isin(sel_country)]
if sel_category:
    filtered_df = filtered_df[filtered_df['category'].isin(sel_category)]

# -----------------------------------------------------------------------------
# 5. DASHBOARD HEADER & KPIs
# -----------------------------------------------------------------------------
st.title("💠 NEXUS | OMNI-VISUAL COMMAND")

rev = filtered_df['total_revenue'].sum()
prof = filtered_df['total_profit'].sum()
margin = (prof / rev * 100) if rev != 0 else 0
txns = len(filtered_df)

col1, col2, col3, col4 = st.columns(4)

def kpi_card(title, value):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """

with col1: st.markdown(kpi_card("Total Revenue", f"${rev/1e6:,.1f}M"), unsafe_allow_html=True)
with col2: st.markdown(kpi_card("Net Profit", f"${prof/1e6:,.1f}M"), unsafe_allow_html=True)
with col3: st.markdown(kpi_card("Profit Margin", f"{margin:.1f}%"), unsafe_allow_html=True)
with col4: st.markdown(kpi_card("Total Orders", f"{txns:,}"), unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. VISUALIZATIONS
# -----------------------------------------------------------------------------
def style_chart(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='Inter',
        font_color='#B0B0B0',
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False, showline=False, showticklabels=True),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', showline=False),
        hoverlabel=dict(bgcolor="#0a0a0a", font_size=13, font_family="Inter", bordercolor="#00F5FF")
    )
    return fig

# ROW 2: Trend, Sunburst, Heatmap
c1, c2, c3 = st.columns([3, 2, 2])

with c1:
    st.markdown("### 📈 Performance Trend")
    df_trend = filtered_df.groupby('month_year')[['total_revenue', 'total_profit']].sum().reset_index().sort_values('month_year')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_trend['month_year'], y=df_trend['total_revenue'], fill='tozeroy', mode='lines', name='Revenue', 
        line=dict(color='#00F5FF', width=3), fillcolor='rgba(0, 245, 255, 0.05)',
        hovertemplate="<b>%{x}</b><br>Rev: $%{y:,.0f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df_trend['month_year'], y=df_trend['total_profit'], mode='lines', name='Profit', 
        line=dict(color='#BD00FF', width=3), hovertemplate="<b>%{x}</b><br>Prof: $%{y:,.0f}<extra></extra>"
    ))
    fig.update_layout(height=280, showlegend=False)
    st.plotly_chart(style_chart(fig), use_container_width=True)

with c2:
    st.markdown("### 🧬 Product Mix")
    df_sun = filtered_df.groupby(['category', 'sub_collection'])['total_revenue'].sum().reset_index()
    fig = px.sunburst(df_sun, path=['category', 'sub_collection'], values='total_revenue', 
                      color='total_revenue', color_continuous_scale='Teal')
    fig.update_layout(height=280, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(style_chart(fig), use_container_width=True)

with c3:
    st.markdown("### 🔥 Demographic Heat")
    df_heat = filtered_df.groupby(['category', 'age_group'])['total_revenue'].sum().reset_index()
    if not df_heat.empty:
        pivot = df_heat.pivot(index='category', columns='age_group', values='total_revenue').fillna(0)
        fig = px.imshow(pivot, color_continuous_scale="Viridis", aspect="auto")
        fig.update_layout(height=280)
        st.plotly_chart(style_chart(fig), use_container_width=True)

# ROW 3: RESTORED GLOBE + Bars + 3D
c4, c5, c6 = st.columns([2, 2, 3])

with c4:
    st.markdown("### 🌍 Top Territories")
    df_bar = filtered_df.groupby('country')[['total_revenue', 'margin_percent']].agg({'total_revenue':'sum', 'margin_percent':'mean'}).reset_index()
    df_bar = df_bar.sort_values('total_revenue', ascending=True).tail(7)
    fig = px.bar(df_bar, x='total_revenue', y='country', orientation='h', color='margin_percent', color_continuous_scale='RdBu')
    fig.update_layout(height=320, yaxis=dict(title=""), coloraxis_showscale=False)
    st.plotly_chart(style_chart(fig), use_container_width=True)

with c5:
    st.markdown("### 🪐 Holographic Earth") 
    df_geo = filtered_df.groupby('country')['total_revenue'].sum().reset_index()
    fig = px.scatter_geo(df_geo, locations="country", locationmode="country names", size="total_revenue", 
                         color="total_revenue", projection="orthographic", color_continuous_scale="Teal", hover_name="country")
    fig.update_layout(
        height=320, 
        geo=dict(bgcolor='rgba(0,0,0,0)', showland=True, landcolor="#0a0a0a", showocean=True, oceancolor="#111"),
        margin=dict(l=0,r=0,t=0,b=0)
    )
    fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>Rev: $%{marker.size:,.0f}<extra></extra>")
    st.plotly_chart(style_chart(fig), use_container_width=True)

with c6:
    st.markdown("### 🌌 Product Nebula 3D")
    df_prod = filtered_df.groupby(['product_name', 'category']).agg({
        'selling_price': 'mean', 'margin_percent': 'mean', 'quantity_units': 'sum'
    }).reset_index().sort_values('quantity_units', ascending=False).head(150)
    if not df_prod.empty:
        fig = px.scatter_3d(df_prod, x='selling_price', y='margin_percent', z='quantity_units', 
                            color='category', size='quantity_units', opacity=0.8)
        fig.update_layout(
            height=320, 
            scene=dict(
                bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title='Price', color='#666'),
                yaxis=dict(title='Margin', color='#666'),
                zaxis=dict(title='Volume', color='#666')
            )
        )
        st.plotly_chart(style_chart(fig), use_container_width=True)

# ROW 4: LOG
st.markdown("---")
st.markdown("### 📋 Live Transaction Log")
table_df = filtered_df[['date', 'product_name', 'category', 'country', 'selling_price', 'quantity_units', 'total_revenue', 'margin_percent']].head(100).sort_values('date', ascending=False)

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
        "product_name": st.column_config.TextColumn("Product", width="medium"),
        "category": st.column_config.TextColumn("Category", width="small"),
        "country": "Region",
        "selling_price": st.column_config.NumberColumn("Price", format="$%.2f"),
        "quantity_units": st.column_config.NumberColumn("Qty"),
        "total_revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
        "margin_percent": st.column_config.ProgressColumn("Margin %", min_value=-20, max_value=60, format="%.1f%%"),
    }
)