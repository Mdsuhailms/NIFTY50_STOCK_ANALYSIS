import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import database


#=================================================
#       STREAMLIT DASHBOARD
#=================================================

st.set_page_config(page_title= "Stock Analysis Dashboard")

st.title(":grey[*NIFTY 50 STOCK ANALYSIS..*] ⚖️")

st.header(":blue[Sector Distribution]",divider="gray")

conn = database.db_connection()
cursor = conn.cursor()

query = """
        SELECT sector, company
        FROM yearly_data
        """

cursor.execute(query)
rows = cursor.fetchall()

data = [{"sector": row[0], "company": row[1]} for row in rows]

fig = px.treemap(
        data,
        path=["sector", "company"],
        color_discrete_sequence= px.colors.qualitative.Set1,
        height=600
)

fig.update_traces(
    branchvalues="total",
    textinfo="label",
    textposition="middle center",
    hovertemplate="<b>%{label}</b><extra></extra>"
)

st.plotly_chart(fig,width="stretch")

#=================================================
#       MARKET DATA
#=================================================

st.subheader(":orange[Market Summary] 🔍", divider= "rainbow")

query = """SELECT
        COUNT(*) FILTER (WHERE yearly_return > 0) AS green_stocks,
        COUNT(*) FILTER (WHERE yearly_return < 0) AS red_stocks,
        AVG(avg_price) AS avg_price_all,
        AVG(avg_volume) AS avg_volume_all
        FROM yearly_data;
        """
cursor.execute(query)
result = cursor.fetchone()

green_stocks = result[0]
red_stocks = result[1]
avg_price = result[2]
avg_vol = result[3]

col1,col2,col3,col4 = st.columns(4)

with col1:
    with st.container():
        st.metric(":green[*Total Greeen stocks*] 🟢", green_stocks)

with col2:
    with st.container():
        st.metric(":red[*Total Red stocks*] 🔴", red_stocks)

with col3:
    with st.container():
        st.metric(":blue[*Average Price*] ₹",f"₹{avg_price:,.2f}")

with col4:
    with st.container():
        st.metric(":violet[*Average Volume*] ▲▼",f"{avg_vol:,.0f}")


c1,c2 = st.columns(2)

with c1:
    with st.container(border=True):

        st.subheader(":green[*Top Green Stocks*] 📈",  divider="green")

        query = """
                SELECT symbol, avg_price,yearly_return
                FROM yearly_data
                ORDER BY yearly_return DESC
                LIMIT 10
                """
        
        cursor.execute(query)
        result = cursor.fetchall()
        
        df = pd.DataFrame(result,columns=['Symbol','Price (in ₹)','Returns (/ year)'])
        st.dataframe(df, hide_index=True)

with c2:
    with st.container(border=True):

        st.subheader(":red[*Top Loss Stocks*] 📈",  divider="red")

        query = """
                SELECT symbol, avg_price,yearly_return
                FROM yearly_data
                ORDER BY yearly_return ASC
                LIMIT 10
                """
        
        cursor.execute(query)
        result = cursor.fetchall()
        
        df = pd.DataFrame(result,columns=['Symbol','Price (in ₹)','Returns (/ year)'])
        st.dataframe(df, hide_index=True)

# ---> TAB FOR ACCESSING DATA
tab = option_menu(
        menu_title= "Analysis of Stocks",
        options= ["📶Sector-Wise Performance","🔃 Volatility","💰 Cumulative Returns","🔗 Stock Correlation","📈 Gainers and 📉 Losers"],   
        orientation="horizontal"
)

#=================================================
#     1. SECTOR WISE PERFORMANCE
#=================================================

if tab == "📶Sector-Wise Performance":
    
    query = """
            SELECT sector, AVG(yearly_return) AS avg_yearly_return
            FROM yearly_data
            GROUP BY sector
            """
    
    cursor.execute(query)
    sectors = cursor.fetchall()

    df = pd.DataFrame(sectors, columns=['sector','avg_yearly_return'])
    df = df.sort_values("sector")
  
    fig = px.bar(
        df, 
        x='sector', 
        y= 'avg_yearly_return', 
        title= "Sector Performance",
        color= df["avg_yearly_return"]>=0,
        color_discrete_map= {True: 'forestgreen', False: 'firebrick'},
        text= df["avg_yearly_return"].apply(lambda x: f"{x:,.2f}%"),
        height=600
        )
    
    fig.update_layout(
        xaxis_title = "Sector",
        yaxis_title = "Average Yearly Return (%)",
        showlegend = False
    )

    fig.update_traces(
        textposition = 'outside',
        hovertemplate=(
        "<b>Sector:</b> %{x}<br>"
        "<b>Avg Yearly Return:</b> %{y:.2f}%<extra></extra>")
    )

    st.plotly_chart(fig)


#=================================================
#     2. VOLATILITY 
#=================================================

if tab == "🔃 Volatility":
    
    query = """
            SELECT symbol, volatility
            FROM yearly_data
            ORDER BY volatility DESC
            LIMIT 10
            """
    
    cursor.execute(query)
    sectors = cursor.fetchall()

    df = pd.DataFrame(sectors, columns=['symbol','volatility'])

    df['volatility(%)'] = df['volatility'] * 100
    
    fig = px.bar(
        df, 
        x='symbol', 
        y= 'volatility(%)', 
        title= "Top 10 Volatile Stocks",
        text = df["volatility(%)"].apply(lambda x: f"{x:,.2f}%"),
        height=600
    )
    
    fig.update_traces(
        textposition = 'outside',
        hovertemplate=(
        "<b>symbol:</b> %{x}<br>"
        "<b>volatility(%):</b> %{y:.2f}%<extra></extra>")
    )

    st.plotly_chart(fig)


#=================================================
#      3. CUMULATIVE RETURNS
#=================================================

if tab == "💰 Cumulative Returns":
        
    query = """
            SELECT *
            FROM daily_data
            """
    
    cursor.execute(query)
    daily_data = cursor.fetchall()

    df = pd.DataFrame(daily_data,
                      columns= ['date', 'open', 'close', 'high', 'low', 'volume', 'symbol',
       'daily_returns', 'cumulative_return_daily']
       )

    final_returns = df.groupby('symbol')['cumulative_return_daily'].last().sort_values(ascending=False)

    top5_stocks = final_returns.head(5).index
    df_top5 = df[df['symbol'].isin(top5_stocks)]

    fig1 = px.line(
        df_top5,
        x= 'date',
        y= 'cumulative_return_daily',
        color='symbol',
        title= "Cumulative Return for Top 5 Performing Stocks",
        labels={'date':'Date',
                'cumulative_return_daily':'Cumulative Return',
                'symbol':'Stock'
                },
        height=600
    )
    
    st.plotly_chart(fig1)

    all_stocks = sorted(df['symbol'].unique().tolist())

    stocks_select = st.multiselect("**Select Stocks to compare Cumulative Return.!**",
                   options=all_stocks
    )

    if stocks_select:
        df_selected = df[df['symbol'].isin(stocks_select)]

        fig2 = px.line(
            df_selected,
            x= 'date',
            y= 'cumulative_return_daily',
            color='symbol',
            title= "Cumulative Return",
            labels={'date':'Date',
                    'cumulative_return_daily':'Cumulative Return',
                    'symbol':'Stock'
                    },
            height=600
        )

        st.plotly_chart(fig2)
    
    
#=================================================
#       4. STOCK CORRELATION
#=================================================

if tab == "🔗 Stock Correlation":

    query = """
            SELECT *
            FROM daily_data
            """
    
    cursor.execute(query)
    daily_data = cursor.fetchall()

    df = pd.DataFrame(daily_data,
                      columns= ['date', 'open', 'close', 'high', 'low', 'volume', 'symbol',
       'daily_returns', 'cumulative_return_daily']
       )

    pivot_df = df.pivot(index="date", columns="symbol", values="daily_returns")
    corr_returns = pivot_df.dropna().corr().round(2)
    
    show_all = st.toggle("Show correlation of all stocks!")

    if show_all:
        fig1 = px.imshow(
            corr_returns,
            title= "Stock Price Correlation Heatmap",
            text_auto=True,
            aspect="auto",
            height=1000,
            width=1500
        )
        
        st.plotly_chart(fig1)

    all_stocks = sorted(df['symbol'].unique().tolist())

    stocks_select = st.multiselect("**Select Stocks to show Heatmap.!**",
                   options=all_stocks
    )

    if stocks_select:

        pivot_selected = pivot_df[stocks_select]
        corr_selected = corr_returns[stocks_select]

        fig1 = px.imshow(
            corr_selected,
            title= "Stock Price Correlation Heatmap",
            text_auto=True,
            aspect="auto",
            height=1000,
            width=1500
        )
        
        st.plotly_chart(fig1)
    
    
#=================================================
#      5. TOP 5 GAINERS AND LOSERS (MONTH-WISE)
#=================================================

if tab == "📈 Gainers and 📉 Losers":
        
    query = """
            SELECT *
            FROM daily_data
            """
    
    cursor.execute(query)
    daily_data = cursor.fetchall()

    df = pd.DataFrame(daily_data,
                      columns= ['date', 'open', 'close', 'high', 'low', 'volume', 'symbol',
       'daily_returns', 'cumulative_return_daily']
       )

    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby(["month","symbol"])["close"].agg(["first","last"])

    monthly_return = ((monthly["last"] - monthly["first"]) / monthly["first"])*100
    df_monthly_return = monthly_return.reset_index(name= "monthly_return")

    months = sorted(df_monthly_return["month"].astype(str).unique())

    month_select = st.selectbox("Select Month",
                                options= months,
                                index=len(months)-1
    )

    month_df = df_monthly_return[df_monthly_return['month'].astype(str) == month_select]

    top_5_gainers = month_df.nlargest(5, "monthly_return")
    top_5_losers = month_df.nsmallest(5, "monthly_return")

    col1,col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader(":green[Top 5 Gainers]",divider="grey")

            fig_gain = px.bar(
                top_5_gainers, 
                x='symbol', 
                y= 'monthly_return', 
                title= f"({month_select})",
                text = top_5_gainers["monthly_return"].apply(lambda x: f"{x:,.2f}%"),
                color_discrete_sequence=["forestgreen"],
                height=600
            )
        
            fig_gain.update_traces(
                textposition = 'outside',
                hovertemplate=(
                "<b>symbol:</b> %{x}<br>"
                "<b>monthly_return:</b> %{y:.2f}%<extra></extra>")
            )

            st.plotly_chart(fig_gain)

    with col2:
        with st.container(border=True):
            st.subheader(":red[Top 5 Losers]", divider="grey")

            fig_loss = px.bar(
                top_5_losers, 
                x='symbol', 
                y= 'monthly_return', 
                title= f"({month_select})",
                text = top_5_losers["monthly_return"].apply(lambda x: f"{x:,.2f}%"),
                color_discrete_sequence=["firebrick"],
                height=600
            )
            
            fig_loss.update_traces(
                textposition = 'outside',
                hovertemplate=(
                "<b>symbol:</b> %{x}<br>"
                "<b>monthly_return:</b> %{y:.2f}%<extra></extra>")
            )

            st.plotly_chart(fig_loss)
    

