"""
Name:       Liam Houchin
CS230:      Section 5
Data:       Fortune 500 Companies
URL:

Description: This streamlit site takes a look at the Fortune 500 dataset.
It includes pivot tables, charts, interactive drop-down menus, and maps.
The intention of this project was to visualize certain key factors to businesses performance,
and plot similarities among them along the way.
"""
# Library Imports
from enum import unique
import pandas as pd
import streamlit as st
import numpy as np
import pydeck as pdk
import matplotlib.pyplot as plt

# File Path
path = "/Users/liamhouchin/Library/CloudStorage/OneDrive-BentleyUniversity/cs230/pythonProject/finalProject/"

def main_page():
    # [ST4] image for the sidebar, this function is on every file in my code
    def side_bar_img():
        image_path = "finalProject/fortune500.jpg"
        st.sidebar.image(image_path, use_container_width=True)

    # [ST4]
    def load_main_page():
        st.title("Fortune 500 Companies")
        st.header("Dataset Overview")
        st.markdown("""
        **Title:** Fortune 500 Companies  
        **Type:** Profits, locations, employees, & more  
        **Description:** This dataset includes comprehensive information about Fortune 500 companies in the United States,
        focusing on revenues & profits, employees, and location
        """)
        st.header("About the Dataset")
        st.markdown("""
        The "Fortune 500" Dataset provides us with a brief financial insight to these companies.
        We can observe this data and look for correlations between employee populations, state of operations, etc.
        """)

    def run_page1():
        side_bar_img()
        load_main_page()
    run_page1() # Run home page

def page2():
    @st.cache_data
    def load_data():
        df = pd.read_csv('finalProject/fortune500.csv')
        df['STATE'] = df['STATE'].str.upper()
        if df.empty:
            st.error("Loaded data is empty.")
        return df

    # [DA1] Clean and filter data
    def clean_data(data):
        columns = ["RANK", "NAME", "CITY", "STATE", "EMPLOYEES", "REVENUES"]
        if not all(col in data.columns for col in columns):
            st.error(f"The dataset does not include all required columns: {columns}")
            return None
        cleaned_data = data[columns].dropna().copy()
        return cleaned_data

    # [ST1] Text box to filter companies by state
    def state_text_box(data):
        st.title('State lookup')
        df = load_data()
        input_state = st.text_input("Enter state abbreviations [ex: MA, ME, CT]").upper().strip()
        if input_state:
            count = df[df['STATE'] == input_state].shape[0]
            results_df = pd.DataFrame({
                'State': [input_state.capitalize()],
                'Number of Fortune 500 companies': [count]
            })
            st.write("### Total Responses for the entered state")
            st.table(results_df)
        else:
            st.write("Please enter valid state abbreviation.")

    # [PY2] This function returns two values, the total list of companies by state, and a percentile break down
    def calculate_comp_by_state(data):
        df = load_data()
        if 'STATE' not in df.columns:
            st.error("The expected column 'STATE' is not found in this dataset, unfortunately.")
            return None, None # Will output None for both if column is absent
        states = ["AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "IA", "ID",
                  "IL", "IN", "KS", "KY", "LA", "MA", "MD", "MI", "MN", "MO", "NC", "ND",
                  "NE", "NJ", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "TN", "TX", "UT",
                  "VA", "WA", "WI"]
        df = df[df['STATE'].isin(states)]
        state_counts = df['STATE'].value_counts()
        total = state_counts.sum()
        state_percentiles = (state_counts / total * 100).round(2).astype(str) + '%'
        results_df = pd.DataFrame({
            'State': state_counts.index,
            'Total': state_counts.values,
            'Percentage': state_percentiles.values
        })
        return results_df, total

    # [DA4] Data breakdown displayed
    # [VIZ1]
    def display_state_breakdown(data):
        state_counts = data["STATE"].value_counts()
        total = state_counts.sum()
        state_percentiles = (state_counts / total * 100).round(2).astype(str) + '%'

        results_df = pd.DataFrame({
            'State': state_counts.index.str.upper(),
            'Total': state_counts.values,
            'Percentage': state_percentiles.values
        })
        st.write('### Breakdown of states by companies')
        st.dataframe(results_df)
        return results_df

    # [VIZ2]
    # [PY1, PY4] Filter New England companies using list comprehension and lambda
    def ne_companies(data, column_name="STATE"):
        new_england_states = {"ME", "NH", "VT", "MA", "RI", "CT"}
        if column_name not in data.columns:
            st.error(f"The column '{column_name}' does not exist within the provided dataset")
            return None

        #comprehension using lambda
        data["in_ne"] = data[column_name].apply(lambda x: "Yes" if x in new_england_states else "No")
        filtered_data = data[data["in_ne"]=="Yes"]

        ne_counts = filtered_data[column_name].value_counts().reset_index()
        ne_counts.columns = ["State", "Company Count"]

        ne_counts = ne_counts[ne_counts["Company Count"].apply(lambda x: x > 0)]

        fig, ax = plt.subplots()
        ax.pie(
            ne_counts["Company Count"],
            labels=ne_counts["State"].str.upper(),
            autopct=lambda p: f'{p:.1f}%',
            startangle=90
        )
        ax.set_title("New England Companies by State")
        st.pyplot(fig)
        
        return ne_counts

# Speaking Point
    # [DA6] Interactive pivot tables
    # [VIZ3]
    def interactive_pivot_table(data, employee_col="EMPLOYEES", state_col="STATE"):
        data = clean_data(data)
        if data is None:
            return

        # Error Check
        if employee_col not in data.columns:
            st.error(f"The column '{employee_col}' does not exist in the dataset.")
            return None

        # Employee range calculation
        if data[employee_col].dropna().empty: # ChatGPT Provided
            st.warning("No valid employee data available for the selected state. Default ranges will be used.")
            employee_min, employee_max = 0, 1000
        else:
            employee_min = int(data[employee_col].dropna().min())
            employee_max = int(data[employee_col].dropna().max())

        # Bins and Labels
        bins = [0, 2500, 5000, 10000, 50000, 100000, employee_max]
        bin_labels = ["0 - 2500",
                    "2,501 - 5,000",
                    "5,001 - 10,000",
                    "10,001 - 50,000",
                    "50,001 - 100,000",
                    f"{100001:,}+"
                      ]

        # Assign ranges
        # [PY3] try/except
        try:
            data["Employee_Range"] = pd.cut(
                data[employee_col].fillna(employee_min),
                bins=bins,
                labels=bin_labels,
                include_lowest=True
            )
        except Exception as e:
            st.error(f"Error during Employee_Range creation: {e}")
            st.dataframe(data.head())
            return None

        # Debug: Verify Employee_Range creation ChatGPT Provided
        if data["Employee_Range"].isnull().all():
            st.error("Failed to create 'Employee_Range'. Check your bins or data.")
            st.write(data.head())
            return None

        # [ST2]
        # Radio buttons for employee range
        st.write("### Select employee range:")
        selected_range = st.radio(
            "Choose a range:",
            options=bin_labels
        )

        # Filter data based on the selected range
        filtered_data = data[data["Employee_Range"] == selected_range]

        if filtered_data.empty:
            st.write("No data available for the selected range.")
            return None

        # Sort order radio button
        sort_order = st.radio(
            "Sort order for pivot table:",
            options=["Ascending", "Descending"]
        )

        # Pivot Table
        # [DA7] create new column 'Employee_Range'
        filtered_data = filtered_data[["NAME", "CITY", "STATE", "RANK","EMPLOYEES", "REVENUES","Employee_Range"]]
        pivot_table = pd.pivot_table(
            filtered_data,
            values="EMPLOYEES",
            index=["EMPLOYEES", "RANK", "NAME", "CITY", "STATE", "REVENUES"],
            aggfunc="count"
        )
        pivot_table.rename(columns={"EMPLOYEES": "Total Employees"}, inplace=True)

        # [DA2] sort employee numbers by ascending/descending
        pivot_table = pivot_table.sort_values(by="EMPLOYEES", ascending=(sort_order == "Ascending"))

        # Display pivot table and filtered data
        st.write("### Pivot Table Showing Total Employees for Selected Employee Range")
        st.dataframe(pivot_table)


    def run_page2():
        data= load_data()
        state_text_box(data)
        display_state_breakdown(data)
        ne_companies(data, column_name="STATE")
        interactive_pivot_table(data, employee_col="EMPLOYEES", state_col="STATE")

    run_page2()

def page3():
    @st.cache_data
    def read_data():
        df=pd.read_csv("finalProject/fortune500.csv")
        df.dropna(subset=["LATITUDE", "LONGITUDE","ADDRESS","REVENUES","PROFIT"],inplace=True)
        return df

    # [PY5] Dictionary usage
    def get_color_map(profit_ranges):
        colors = [
            [255, 0, 0, 160], [0, 255, 0, 160], [0, 0, 255, 160], [255, 255, 0, 160],
            [255, 0, 255, 160], [0, 255, 255, 160], [128, 0, 0, 160], [128, 128, 0, 160],
            [0, 128, 0, 160], [128, 0, 128, 160], [0, 128, 128, 160], [0, 0, 128, 160],
        ]
        color_map = {profit_range: colors[i % len(colors)] for i, profit_range in enumerate(profit_ranges)}
        return color_map

    # [DA9] calculate and categorize profits
    def categorize_profits(data):
        bins = [-float('inf'), 100, 500, 1000, 5000,10000,20000,float('inf')]
        labels = ["Less than $100M","$100M - $500M","$500M - $1000M", "$1B - $5B","$5B - $10B","$10B - $20B","More than $20B"]
        data['Profit_Category'] = pd.cut(data['PROFIT'],bins=bins,labels=labels, include_lowest=True)
        return data

    # [MAP]
    # [ST3] Select Box
    def show_map(data):
        states = sorted(list(data['STATE'].unique()))
        selected_state = st.selectbox(
                    "Select a state to show companies:",
                    sorted(states),
                    index = states.index("CA") if "CA" in states else 0
                    )
        st.write(f"Selected state: {selected_state}")  # Debugging output ChatGPT Provided

        # Filter data based on the selected state
        filtered_data = data[data['STATE'] == selected_state]
        st.write(f"Filtered data rows: {filtered_data.shape[0]}")  # Debugging output ChatGPT Provided

        if not filtered_data.empty:
            # Categorize profits
            filtered_data = categorize_profits(filtered_data)
            st.write("Profit categories created successfully.")  # Debugging output ChatGPT Provided

            weighted_lat = (filtered_data['LATITUDE'] * filtered_data['REVENUES']).sum() / filtered_data['REVENUES'].sum()
            weighted_lon = (filtered_data['LONGITUDE'] * filtered_data['REVENUES']).sum() / filtered_data['REVENUES'].sum()

            # Convert Profit_Category to strings
            filtered_data['Profit_Category'] = filtered_data['Profit_Category'].astype(str)

            # Generate color map for profit categories
            unique_profit_categories = filtered_data['Profit_Category'].unique()
            color_map = get_color_map(unique_profit_categories)

            # Map colors based on profit categories
            filtered_data['color'] = filtered_data['Profit_Category'].map(color_map)

            view_state = pdk.ViewState(
                latitude=weighted_lat,
                longitude=weighted_lon,
                zoom=5,
                pitch=40
            )

            tooltip = {
                "html": "<b>Company:</b> {NAME}<br><b>Profit Category:</b> {Profit_Category}",
                "style": {"backgroundColor": "steelblue", "color": "white"}
            }

            scatterplot_layer = pdk.Layer(
                "ScatterplotLayer",
                filtered_data,
                get_position="[LONGITUDE, LATITUDE]",
                get_color="color",
                get_radius=500,
                pickable=True
            )
            deck = pdk.Deck(
                map_style='mapbox://styles/mapbox/light-v9',
                initial_view_state=view_state,
                layers=[scatterplot_layer],
                tooltip=tooltip
            )
            st.pydeck_chart(deck)

            st.markdown("### Color Legend for Profit Categories")
            sorted_categories = {k: color_map[k] for k in sorted(color_map.keys())}

            for category, color in color_map.items():
                color_hex = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
                st.markdown(f"<span style='color:{color_hex}; font-weight: bold; '>●</span> {category}", unsafe_allow_html=True)
        else:
            st.error("No data available for the selected state.")

    def run_page_company_map():
        data = read_data()
        st.title('Company Profit Map Viewer')
        show_map(data)

    run_page_company_map()

def main():
    # Sidebar navigation
    st.sidebar.title("Navigation")
    # Create a dictionary of your pages
    pages_dict = {
        "Home": main_page,
        "Queries and Pivot Tables": page2,
        "Data Map": page3,
    }
    # Radio button for page selection
    selected_page = st.sidebar.radio("Select a page:", list(pages_dict.keys()))

    # Call the app function based on selection
    if selected_page in pages_dict:
        pages_dict[selected_page]()

main()



