import streamlit as st
from streamlit_folium import st_folium

# Import custom utilities
from utils.filters import FilterUtils
from utils.data_loader import DataLoader
from utils.map_utils import MapUtils


def main():
    st.set_page_config(
        page_title="Land Registry Geospatial Platform (Land Search)",
        page_icon="🗺️",
        layout="wide",
    )

    # App title
    st.title("🗺️ Land Registry Geospatial and Search Platform")

    with st.sidebar:
        if st.button(label="📤 Load Land Registry"):
            # Load and validate data
            with st.spinner("Uploading files..."):
                land_data = DataLoader().load_and_validate_json()
                st.session_state["loaded_land_data"] = land_data

    if "loaded_land_data" in st.session_state:
        land_data = st.session_state["loaded_land_data"]
        if land_data:
            # Extract plot metadata for filtering
            plots_metadata = DataLoader.extract_plot_metadata(land_data["plots"])

            # Create filters
            filters = FilterUtils.create_filters(plots_metadata)

            # Apply filters
            filtered_plots, filter_type = FilterUtils.apply_filters(
                land_data["plots"], filters
            )

            # Create layout columns
            # map_col, details_col = st.columns([10, 1])

            # Map column
            # with map_col:
            # st.subheader("📍 Plot Locations")
            
            # # Display filter results
            # st.write(
            #     f"📊 Showing {len(filtered_plots)} of {len(land_data['plots'])} plots"
            # )
            m = MapUtils(land_data["plots"])
            m = m.create_map(filtered_plots, filter_type)

            if m:
                # Display Folium map
                output = st_folium(m, width=None, height=600)

            # Details column
            # with details_col:
            #     pass
            # st.subheader("🔎 Plot Details")

            # # Select plot for detailed view
            # plot_names = [
            #     f"{p.get('plot_info', {}).get('plot_number', 'Unknown')}"
            #     for p in filtered_plots
            # ]

            # selected_plot_index = st.selectbox(
            #     "Select Plot",
            #     range(len(plot_names)),
            #     format_func=lambda x: plot_names[x],
            # )

            # # Display selected plot details
            # if filtered_plots:
            #     selected_plot = filtered_plots[selected_plot_index]
            #     plot_info = selected_plot.get("plot_info", {})

            #     st.markdown("#### Plot Information")
            #     st.write(f"**Plot Number:** {plot_info.get('plot_number', 'N/A')}")
            #     st.write(
            #         f"**Area:** {plot_info.get('area', 'N/A')} {plot_info.get('metric', '')}"
            #     )
            #     st.write(f"**Locality:** {plot_info.get('locality', 'N/A')}")
            #     st.write(f"**District:** {plot_info.get('district', 'N/A')}")
            #     st.write(f"**Region:** {plot_info.get('region', 'N/A')}")

            #     # Survey points details
            #     st.markdown("#### Survey Points")
            #     for point in selected_plot.get("survey_points", []):
            #         st.write(f"**Point Name:** {point.get('point_name', 'N/A')}")
            #         st.write(
            #             f"Latitude: {point.get('converted_coords', {}).get('latitude', 'N/A')}"
            #         )
            #         st.write(
            #             f"Longitude: {point.get('converted_coords', {}).get('longitude', 'N/A')}"
            #         )
            #         st.markdown("---")
    else:
        # Landing page
        st.markdown(
            """
        ### Welcome to Land Registry Geospatial Platform
        
        To get started:
        1. Upload a JSON file containing land registry data
        2. Use sidebar filters to explore and analyze plots
        3. View plot locations on the interactive map
        
        📤 Upload your JSON file to begin!
        """
        )


if __name__ == "__main__":
    main()