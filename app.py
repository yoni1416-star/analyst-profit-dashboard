import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Profit Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

st.markdown("## 🚀 Profit Intelligence Dashboard")
st.caption("Data Cleaning • Duplicate Detection • Profit Analysis")

uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx"]
)

if uploaded_file:
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif file_name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("Unsupported file type")
        st.stop()

    # =========================
    # VALIDATION
    # =========================
    required_columns = ["LoadNum", "Revenue", "Cost", "Carrier", "Region"]
    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        st.error(f"Missing columns: {missing_cols}")
        st.stop()

    # =========================
    # SIDEBAR
    # =========================
    st.sidebar.header("⚙️ Controls")

    carrier_options = ["All"] + sorted(df["Carrier"].dropna().unique().tolist())
    region_options = ["All"] + sorted(df["Region"].dropna().unique().tolist())
    profit_view_options = ["All", "Profitable Only", "Loss Only"]

    selected_carrier = st.sidebar.selectbox("Carrier", carrier_options)
    selected_region = st.sidebar.selectbox("Region", region_options)
    selected_profit_view = st.sidebar.selectbox("Profit Filter", profit_view_options)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🧹 Data Cleaning")

    remove_duplicates = st.sidebar.button("Remove Duplicates (LoadNum + Cost)")
    show_only_duplicates = st.sidebar.checkbox("Show only duplicate loads")

    # =========================
    # DATA VALIDATION METRICS
    # =========================
    missing_values = int(df.isnull().sum().sum())
    exact_duplicate_rows = int(df.duplicated().sum())
    duplicate_loadnums = int(df.duplicated(subset=["LoadNum"]).sum())
    duplicate_load_cost = int(df.duplicated(subset=["LoadNum", "Cost"]).sum())

    cleaned_df = df.copy()

    if remove_duplicates:
        before = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates(subset=["LoadNum", "Cost"], keep="first")
        after = len(cleaned_df)
        st.success(f"Removed {before - after} duplicate rows")

    filtered_df = cleaned_df.copy()

    if selected_carrier != "All":
        filtered_df = filtered_df[filtered_df["Carrier"] == selected_carrier]

    if selected_region != "All":
        filtered_df = filtered_df[filtered_df["Region"] == selected_region]

    if show_only_duplicates:
        filtered_df = filtered_df[
            filtered_df.duplicated(subset=["LoadNum"], keep=False)
        ]

    # =========================
    # CALCULATIONS
    # =========================
    filtered_df["Profit"] = filtered_df["Revenue"] - filtered_df["Cost"]
    filtered_df["Margin %"] = (filtered_df["Profit"] / filtered_df["Revenue"]) * 100

    if selected_profit_view == "Profitable Only":
        filtered_df = filtered_df[filtered_df["Profit"] >= 0]
    elif selected_profit_view == "Loss Only":
        filtered_df = filtered_df[filtered_df["Profit"] < 0]

    # =========================
    # KPI TOP
    # =========================
    total_revenue = int(filtered_df["Revenue"].sum()) if not filtered_df.empty else 0
    total_profit = int(filtered_df["Profit"].sum()) if not filtered_df.empty else 0
    avg_margin = round(filtered_df["Margin %"].mean(), 2) if not filtered_df.empty else 0
    total_rows = len(filtered_df)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Revenue", total_revenue)
    k2.metric("Total Profit", total_profit)
    k3.metric("Avg Margin %", avg_margin)
    k4.metric("Rows", total_rows)

    # =========================
    # ALERTS
    # =========================
    low_margin = filtered_df[filtered_df["Margin %"] < 10]
    losses = filtered_df[filtered_df["Profit"] < 0]

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Missing Values", missing_values)
    a2.metric("Exact Duplicate Rows", exact_duplicate_rows)
    a3.metric("Duplicate LoadNum + Cost", duplicate_load_cost)
    a4.metric("Loss Making Loads", len(losses))

    if missing_values > 0:
        st.warning("There are missing values in the dataset")

    if exact_duplicate_rows > 0:
        st.warning("There are fully duplicated rows")

    # =========================
    # TABS
    # =========================
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Data", "🚨 Loss Analysis"])

    with tab1:
        st.subheader("Summary by Carrier")

        if not filtered_df.empty:
            carrier_summary = (
                filtered_df.groupby("Carrier", as_index=False)
                .agg(
                    Loads=("LoadNum", "count"),
                    Total_Revenue=("Revenue", "sum"),
                    Total_Cost=("Cost", "sum"),
                    Total_Profit=("Profit", "sum"),
                    Avg_Margin_pct=("Margin %", "mean"),
                )
            )

            st.dataframe(carrier_summary, use_container_width=True)

            c1, c2 = st.columns(2)

            with c1:
                st.markdown("#### Profit by Load")
                st.bar_chart(filtered_df.set_index("LoadNum")["Profit"])

            with c2:
                st.markdown("#### Profit by Carrier")
                st.bar_chart(carrier_summary.set_index("Carrier")["Total_Profit"])

            st.markdown("#### 🚨 Worst Performers")
            worst_carriers = carrier_summary.sort_values("Total_Profit").head(3)
            st.dataframe(worst_carriers, use_container_width=True)

        else:
            st.info("No data available for current filters.")

    with tab2:
        st.subheader("Data Validation")

        v1, v2, v3 = st.columns(3)
        v1.metric("Duplicate LoadNum", duplicate_loadnums)
        v2.metric("Duplicate LoadNum + Cost", duplicate_load_cost)
        v3.metric("Low Margin Loads (<10%)", len(low_margin))

        st.markdown("#### Duplicate LoadNum Details")
        dup_loads_df = cleaned_df[
            cleaned_df.duplicated(subset=["LoadNum"], keep=False)
        ].sort_values("LoadNum")

        if not dup_loads_df.empty:
            st.dataframe(dup_loads_df, use_container_width=True)
        else:
            st.success("No duplicate LoadNum values found")

        st.markdown("#### Data with Calculations")

        def color_profit(val):
            if val < 0:
                return "color: red;"
            return "color: lightgreen;"

        styled_df = filtered_df.style.map(color_profit, subset=["Profit", "Margin %"])
        st.dataframe(styled_df, use_container_width=True)

        csv_data = filtered_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download cleaned data",
            data=csv_data,
            file_name="cleaned_profit_dashboard.csv",
            mime="text/csv",
        )

    with tab3:
        st.subheader("Loss Analysis")

        if not losses.empty:
            st.markdown("#### Loss Making Loads ❌")
            st.dataframe(losses, use_container_width=True)

            st.markdown("#### Lowest Profit Loads")
            worst_loads = losses.sort_values("Profit").head(10)
            st.dataframe(worst_loads, use_container_width=True)
        else:
            st.success("No losses found 🎉")
else:
    st.info("Upload a CSV or Excel file to begin.")