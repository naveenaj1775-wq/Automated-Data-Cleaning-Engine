import streamlit as st
import pandas as pd
import hashlib
from io import BytesIO


# --------------------------------
# PAGE CONFIGURATION
# --------------------------------

st.set_page_config(
    page_title="Automated Data Cleaning Engine",
    page_icon="🧹",
    layout="wide"
)

st.title("🧹 Automated Data Cleaning Engine")

st.write(
    "An intelligent platform to inspect, analyze "
    "and clean CSV and Excel datasets."
)

st.sidebar.title("Navigation")
st.sidebar.write("Welcome to Data Cleaning Engine!")


# --------------------------------
# CACHED FILE READING
# --------------------------------

@st.cache_data(show_spinner="Reading your dataset...")
def load_dataset(file_bytes, file_type):

    if file_type == "csv":

        try:
            df = pd.read_csv(
                BytesIO(file_bytes),
                encoding="utf-8"
            )

        except UnicodeDecodeError:

            df = pd.read_csv(
                BytesIO(file_bytes),
                encoding="cp1252"
            )

    else:

        df = pd.read_excel(
            BytesIO(file_bytes),
            engine="openpyxl"
        )

    return df


# --------------------------------
# DATASET STATISTICS
# --------------------------------

def calculate_statistics(df):

    missing_values = df.isnull().sum()

    duplicate_count = int(
        df.duplicated().sum()
    )

    missing_data = pd.DataFrame({

        "Column Name": df.columns,

        "Missing Count": missing_values.values,

        "Missing Percentage": (
            missing_values.values /
            max(len(df), 1)
        ) * 100

    })

    return {

        "total_rows": len(df),

        "total_columns": len(df.columns),

        "total_missing": int(
            missing_values.sum()
        ),

        "total_duplicates": duplicate_count,

        "missing_data": missing_data

    }


# --------------------------------
# FILE UPLOAD
# --------------------------------

uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx"]
)


if uploaded_file is not None:

    try:

        # --------------------------------
        # READ FILE
        # --------------------------------

        file_bytes = uploaded_file.getvalue()

        file_signature = hashlib.sha256(
            file_bytes
        ).hexdigest()

        file_type = uploaded_file.name.split(".")[-1].lower()

        original_df_loaded = load_dataset(
            file_bytes,
            file_type
        )

        # --------------------------------
        # INITIALIZE SESSION STATE
        # --------------------------------

        if (
            "file_signature" not in st.session_state
            or st.session_state.file_signature != file_signature
        ):

            st.session_state.original_df = (
                original_df_loaded.copy()
            )

            st.session_state.cleaned_df = (
                original_df_loaded.copy()
            )

            st.session_state.file_signature = file_signature

            st.session_state.activity_log = []

            st.session_state.duplicates_removed = 0

            st.session_state.missing_values_filled = 0

            st.session_state.rows_removed_missing = 0

            st.session_state.cleaned_version = 0

            st.session_state.original_stats = calculate_statistics(
                st.session_state.original_df
            )

            st.session_state.cleaned_stats = (
                st.session_state.original_stats
            )

            st.session_state.cleaned_stats_version = 0

            st.session_state.csv_export = None

            st.session_state.excel_export = None

        # --------------------------------
        # GET CURRENT DATASET
        # --------------------------------

        original_df = st.session_state.original_df

        cleaned_df = st.session_state.cleaned_df

        # --------------------------------
        # REUSE CACHED STATISTICS
        # --------------------------------

        if (
            st.session_state.cleaned_stats_version
            != st.session_state.cleaned_version
        ):

            st.session_state.cleaned_stats = calculate_statistics(
                cleaned_df
            )

            st.session_state.cleaned_stats_version = (
                st.session_state.cleaned_version
            )

        original_stats = st.session_state.original_stats

        cleaned_stats = st.session_state.cleaned_stats

        st.success("Dataset uploaded successfully!")

        # --------------------------------
        # DATASET PREVIEW
        # --------------------------------

        st.subheader("📊 Dataset Preview")

        st.dataframe(
            cleaned_df.head(10),
            width="stretch"
        )

        # --------------------------------
        # DATASET OVERVIEW
        # --------------------------------

        st.subheader("📌 Dataset Overview")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Rows",
            f"{cleaned_stats['total_rows']:,}"
        )

        col2.metric(
            "Total Columns",
            cleaned_stats["total_columns"]
        )

        col3.metric(
            "Missing Values",
            f"{cleaned_stats['total_missing']:,}"
        )

        col4.metric(
            "Duplicate Rows",
            f"{cleaned_stats['total_duplicates']:,}"
        )

        # --------------------------------
        # BEFORE AND AFTER COMPARISON
        # --------------------------------

        st.subheader(
            "📈 Before & After Cleaning Comparison"
        )

        comparison = pd.DataFrame({

            "Metric": [
                "Total Rows",
                "Total Columns",
                "Missing Values",
                "Duplicate Rows"
            ],

            "Before Cleaning": [

                original_stats["total_rows"],

                original_stats["total_columns"],

                original_stats["total_missing"],

                original_stats["total_duplicates"]

            ],

            "After Cleaning": [

                cleaned_stats["total_rows"],

                cleaned_stats["total_columns"],

                cleaned_stats["total_missing"],

                cleaned_stats["total_duplicates"]

            ]

        })

        st.dataframe(
            comparison,
            hide_index=True,
            width="stretch"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Rows Removed",
            f"{len(original_df) - len(cleaned_df):,}"
        )

        col2.metric(
            "Missing Values Filled",
            f"{st.session_state.missing_values_filled:,}"
        )

        col3.metric(
            "Duplicates Removed",
            f"{st.session_state.duplicates_removed:,}"
        )

        # --------------------------------
        # MISSING VALUE ANALYSIS
        # --------------------------------

        st.subheader("🔍 Missing Value Analysis")

        st.dataframe(
            cleaned_stats["missing_data"],
            hide_index=True,
            width="stretch"
        )

        # --------------------------------
        # DUPLICATE DETECTION
        # --------------------------------

        st.subheader("🔁 Duplicate Detection")

        duplicate_count = cleaned_stats["total_duplicates"]

        if duplicate_count > 0:

            st.warning(
                f"{duplicate_count:,} duplicate records detected!"
            )

            st.dataframe(
                cleaned_df[
                    cleaned_df.duplicated()
                ].head(10),
                width="stretch"
            )

            if st.button("Remove Duplicates"):

                new_df = cleaned_df.drop_duplicates()

                st.session_state.cleaned_df = new_df

                st.session_state.duplicates_removed += (
                    duplicate_count
                )

                st.session_state.activity_log.append(
                    f"Removed {duplicate_count:,} duplicate records."
                )

                st.session_state.cleaned_version += 1

                st.session_state.csv_export = None

                st.session_state.excel_export = None

                st.success("Duplicates removed successfully!")

                st.rerun()

        else:

            st.success("No duplicate records found!")

        # --------------------------------
        # MISSING VALUE HANDLING
        # --------------------------------

        st.subheader("🧹 Missing Value Handling")

        columns_with_missing = [

            col for col in cleaned_df.columns

            if cleaned_df[col].isnull().any()

        ]

        if columns_with_missing:

            selected_column = st.selectbox(
                "Select a column with missing values",
                columns_with_missing
            )

            missing_count = int(
                cleaned_df[selected_column].isnull().sum()
            )

            st.info(
                f"{missing_count:,} missing values found "
                f"in {selected_column}."
            )

            is_identifier = (

                "id" in selected_column.lower()

                or "code" in selected_column.lower()

            )

            if is_identifier:

                strategies = [

                    "Leave unchanged",

                    "Drop rows with missing values"

                ]

            elif pd.api.types.is_numeric_dtype(
                cleaned_df[selected_column]
            ):

                strategies = [

                    "Leave unchanged",

                    "Fill with Mean",

                    "Fill with Median",

                    "Fill with Mode",

                    "Drop rows with missing values"

                ]

            else:

                strategies = [

                    "Leave unchanged",

                    "Fill with Unknown",

                    "Fill with Mode",

                    "Drop rows with missing values"

                ]

            strategy = st.selectbox(
                "Choose a cleaning method",
                strategies
            )

            if st.button("Apply Missing Value Cleaning"):

                new_df = cleaned_df.copy()

                previous_rows = len(new_df)

                if strategy == "Leave unchanged":

                    st.info("No changes made.")

                elif strategy == "Fill with Unknown":

                    new_df[selected_column] = (
                        new_df[selected_column].fillna("Unknown")
                    )

                elif strategy == "Fill with Mean":

                    value = new_df[selected_column].mean()

                    if pd.notna(value):

                        new_df[selected_column] = (
                            new_df[selected_column].fillna(value)
                        )

                elif strategy == "Fill with Median":

                    value = new_df[selected_column].median()

                    if pd.notna(value):

                        new_df[selected_column] = (
                            new_df[selected_column].fillna(value)
                        )

                elif strategy == "Fill with Mode":

                    mode_values = new_df[selected_column].mode()

                    if not mode_values.empty:

                        new_df[selected_column] = (
                            new_df[selected_column].fillna(
                                mode_values.iloc[0]
                            )
                        )

                elif strategy == "Drop rows with missing values":

                    new_df = new_df.dropna(
                        subset=[selected_column]
                    )

                remaining_missing = int(
                    new_df[selected_column].isnull().sum()
                )

                handled = missing_count - remaining_missing

                rows_removed = previous_rows - len(new_df)

                if strategy in [

                    "Fill with Unknown",

                    "Fill with Mean",

                    "Fill with Median",

                    "Fill with Mode"

                ]:

                    st.session_state.missing_values_filled += handled

                    if handled > 0:

                        st.session_state.activity_log.append(
                            f"{strategy} applied to {selected_column}. "
                            f"{handled:,} missing values filled."
                        )

                elif strategy == "Drop rows with missing values":

                    st.session_state.rows_removed_missing += rows_removed

                    st.session_state.activity_log.append(
                        f"Dropped {rows_removed:,} rows because "
                        f"{selected_column} contained missing values."
                    )

                if strategy != "Leave unchanged":

                    st.session_state.cleaned_df = new_df

                    st.session_state.cleaned_version += 1

                    st.session_state.csv_export = None

                    st.session_state.excel_export = None

                    st.success("Cleaning operation completed!")

                    st.rerun()

        else:

            st.success("No missing values found!")

        # --------------------------------
        # CLEANING SUMMARY
        # --------------------------------

        st.subheader("📋 Cleaning Summary")

        total_duplicates_removed = (
            st.session_state.duplicates_removed
        )

        total_missing_filled = (
            st.session_state.missing_values_filled
        )

        total_rows_removed = (
            len(original_df) - len(cleaned_df)
        )

        remaining_missing = (
            cleaned_stats["total_missing"]
        )

        total_operations = len(
            st.session_state.activity_log
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Duplicate Records Removed",
            f"{total_duplicates_removed:,}"
        )

        col2.metric(
            "Missing Values Filled",
            f"{total_missing_filled:,}"
        )

        col3.metric(
            "Total Rows Removed",
            f"{total_rows_removed:,}"
        )

        col4, col5 = st.columns(2)

        col4.metric(
            "Remaining Missing Values",
            f"{remaining_missing:,}"
        )

        col5.metric(
            "Cleaning Operations",
            f"{total_operations:,}"
        )

        # --------------------------------
        # CLEANING ACTIVITY LOG
        # --------------------------------

        st.subheader("📝 Cleaning Activity Summary")

        if st.session_state.activity_log:

            for index, activity in enumerate(
                st.session_state.activity_log,
                start=1
            ):

                st.write(
                    f"{index}. ✔️ {activity}"
                )

        else:

            st.info(
                "No cleaning operations performed yet."
            )

        # --------------------------------
        # RESET CLEANING
        # --------------------------------

        st.subheader("🔄 Reset Cleaning")

        st.write(
            "Restore your dataset to its original state "
            "and clear all cleaning operations."
        )

        if st.button("🔄 Reset Cleaning"):

            st.session_state.cleaned_df = (
                st.session_state.original_df.copy()
            )

            st.session_state.duplicates_removed = 0

            st.session_state.missing_values_filled = 0

            st.session_state.rows_removed_missing = 0

            st.session_state.activity_log = []

            st.session_state.cleaned_version += 1

            st.session_state.csv_export = None

            st.session_state.excel_export = None

            st.success("Dataset restored successfully!")

            st.rerun()

        # --------------------------------
        # CLEANING SUMMARY FOR EXPORT
        # --------------------------------

        cleaning_summary = pd.DataFrame({

            "Metric": [

                "Duplicate Records Removed",

                "Missing Values Filled",

                "Rows Removed Due to Missing Values",

                "Total Rows Removed",

                "Remaining Missing Values",

                "Cleaning Operations Performed"

            ],

            "Value": [

                total_duplicates_removed,

                total_missing_filled,

                st.session_state.rows_removed_missing,

                total_rows_removed,

                remaining_missing,

                total_operations

            ]

        })

        # --------------------------------
        # DATA QUALITY ANALYSIS
        # --------------------------------

        st.header("🔍 Data Quality Analysis")

        st.write(
            "Analyze your dataset to identify potential data quality issues."
        )

        missing_count = int(cleaned_df.isnull().sum().sum())

        duplicate_count = int(cleaned_df.duplicated().sum())

        negative_quantity = (
            int(cleaned_df["Quantity"].lt(0).sum())
            if "Quantity" in cleaned_df.columns else 0
        )

        zero_quantity = (
            int(cleaned_df["Quantity"].eq(0).sum())
            if "Quantity" in cleaned_df.columns else 0
        )

        negative_price = (
            int(cleaned_df["UnitPrice"].lt(0).sum())
            if "UnitPrice" in cleaned_df.columns else 0
        )

        zero_price = (
            int(cleaned_df["UnitPrice"].eq(0).sum())
            if "UnitPrice" in cleaned_df.columns else 0
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("Missing Values", f"{missing_count:,}")
        col2.metric("Duplicate Records", f"{duplicate_count:,}")
        col3.metric("Negative Quantity", f"{negative_quantity:,}")

        col4, col5, col6 = st.columns(3)

        col4.metric("Zero Quantity", f"{zero_quantity:,}")
        col5.metric("Negative Unit Price", f"{negative_price:,}")
        col6.metric("Zero Unit Price", f"{zero_price:,}")

        quality_report = pd.DataFrame({

            "Quality Check": [

                "Missing Values",

                "Duplicate Records",

                "Negative Quantity",

                "Zero Quantity",

                "Negative Unit Price",

                "Zero Unit Price"

            ],

            "Issues Found": [

                missing_count,

                duplicate_count,

                negative_quantity,

                zero_quantity,

                negative_price,

                zero_price

            ]

        })

        st.subheader("📋 Data Quality Report")

        st.dataframe(
            quality_report,
            hide_index=True,
            width="stretch"
        )

        if quality_report["Issues Found"].sum() == 0:

            st.success(
                "Excellent! No issues detected in the selected checks."
            )

        else:

            st.warning(
                "Some data quality issues were detected. "
                "Review the report above."
            )

        # --------------------------------
        # STAGE 6 - DATA VISUALIZATION
        # --------------------------------

        st.header("📊 Data Visualization")

        st.write(
            "Explore your dataset through interactive charts "
            "and understand important business insights."
        )

        visual_df = cleaned_df.copy()

        # Check required columns

        if "Quantity" in visual_df.columns and "UnitPrice" in visual_df.columns:

            visual_df["Quantity"] = pd.to_numeric(
                visual_df["Quantity"],
                errors="coerce"
            )

            visual_df["UnitPrice"] = pd.to_numeric(
                visual_df["UnitPrice"],
                errors="coerce"
            )

            # Calculate revenue

            visual_df["Revenue"] = (
                visual_df["Quantity"] * visual_df["UnitPrice"]
            )

            # --------------------------------
            # CHART 1 - MONTHLY SALES TREND
            # --------------------------------

            st.subheader("📈 Monthly Sales Trend")

            if "InvoiceDate" in visual_df.columns:

                visual_df["InvoiceDate"] = pd.to_datetime(
                    visual_df["InvoiceDate"],
                    errors="coerce"
                )

                monthly_data = visual_df.dropna(
                    subset=["InvoiceDate", "Revenue"]
                ).copy()

                monthly_data["Month"] = (
                    monthly_data["InvoiceDate"]
                    .dt.to_period("M")
                    .astype(str)
                )

                monthly_sales = (
                    monthly_data.groupby("Month")["Revenue"]
                    .sum()
                    .sort_index()
                )

                if not monthly_sales.empty:

                    st.line_chart(
                        monthly_sales,
                        x_label="Month",
                        y_label="Revenue"
                    )

                else:

                    st.info("No valid date information available.")

            else:

                st.info(
                    "InvoiceDate column is required for monthly sales analysis."
                )

            # --------------------------------
            # CHART 2 - TOP 10 COUNTRIES
            # --------------------------------

            st.subheader("🌍 Top 10 Countries by Revenue")

            if "Country" in visual_df.columns:

                country_sales = (
                    visual_df.groupby("Country")["Revenue"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                )

                st.bar_chart(
                    country_sales,
                    x_label="Country",
                    y_label="Revenue"
                )

            else:

                st.info("Country column is not available.")

            # --------------------------------
            # CHART 3 - TOP 10 PRODUCTS
            # --------------------------------

            st.subheader("🏆 Top 10 Products by Revenue")

            if "Description" in visual_df.columns:

                product_sales = (
                    visual_df.dropna(subset=["Description"])
                    .groupby("Description")["Revenue"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                )

                st.bar_chart(
                    product_sales,
                    x_label="Product",
                    y_label="Revenue"
                )

            elif "StockCode" in visual_df.columns:

                product_sales = (
                    visual_df.groupby("StockCode")["Revenue"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                )

                st.bar_chart(
                    product_sales,
                    x_label="Product Code",
                    y_label="Revenue"
                )

            else:

                st.info("Product information is not available.")

            # --------------------------------
            # CHART 4 - SALES VS RETURNS
            # --------------------------------

            st.subheader("📦 Sales vs Returns Analysis")

            positive_sales = int(
                visual_df["Quantity"].gt(0).sum()
            )

            returned_transactions = int(
                visual_df["Quantity"].lt(0).sum()
            )

            zero_transactions = int(
                visual_df["Quantity"].eq(0).sum()
            )

            transaction_data = pd.DataFrame({

                "Transaction Count": [

                    positive_sales,

                    returned_transactions,

                    zero_transactions

                ]

            }, index=[

                "Sales",

                "Returns",

                "Zero Quantity"

            ])

            st.bar_chart(
                transaction_data,
                x_label="Transaction Type",
                y_label="Number of Records"
            )

            st.info(
                "Note: Negative quantities are treated as returns "
                "and are not automatically removed."
            )

        else:

            st.warning(
                "Data visualization requires Quantity and UnitPrice columns."
            )

        # --------------------------------
        # DOWNLOAD CLEANED DATASET
        # --------------------------------

        st.subheader("📥 Export Cleaned Dataset")

        col1, col2 = st.columns(2)

        # --------------------------------
        # CSV EXPORT
        # --------------------------------

        with col1:

            st.write("📄 CSV Download")

            if st.button("Prepare CSV"):

                with st.spinner("Preparing CSV file..."):

                    st.session_state.csv_export = (
                        cleaned_df.to_csv(
                            index=False
                        ).encode("utf-8")
                    )

                st.success("CSV file prepared successfully!")

            if st.session_state.csv_export is not None:

                st.download_button(
                    label="⬇️ Download CSV",
                    data=st.session_state.csv_export,
                    file_name="Cleaned_Dataset.csv",
                    mime="text/csv",
                    width="stretch"
                )

        # --------------------------------
        # EXCEL EXPORT
        # --------------------------------

        with col2:

            st.write("📊 Excel Report")

            if st.button("Prepare Excel"):

                with st.spinner("Preparing Excel report..."):

                    excel_buffer = BytesIO()

                    with pd.ExcelWriter(
                        excel_buffer,
                        engine="xlsxwriter"
                    ) as writer:

                        cleaned_df.to_excel(
                            writer,
                            sheet_name="Cleaned Data",
                            index=False
                        )

                        comparison.to_excel(
                            writer,
                            sheet_name="Before & After",
                            index=False
                        )

                        cleaning_summary.to_excel(
                            writer,
                            sheet_name="Cleaning Summary",
                            index=False
                        )

                        activity_df = pd.DataFrame({

                            "Cleaning Activity": (
                                st.session_state.activity_log
                            )

                        })

                        activity_df.to_excel(
                            writer,
                            sheet_name="Activity Log",
                            index=False
                        )

                    st.session_state.excel_export = (
                        excel_buffer.getvalue()
                    )

                st.success("Excel report prepared successfully!")

            if st.session_state.excel_export is not None:

                st.download_button(
                    label="⬇️ Download Excel Report",
                    data=st.session_state.excel_export,
                    file_name="Cleaned_Dataset_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )

    except Exception as e:

        st.error(
            f"Error processing dataset: {e}"
        )

else:

    st.info(
        "Please upload a CSV or Excel file to begin."
    )