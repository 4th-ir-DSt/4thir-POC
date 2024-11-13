import streamlit as st
import folium
from streamlit_folium import st_folium
from folium import Popup, IFrame, plugins
from folium.plugins import MarkerCluster, Draw, MeasureControl, HeatMap
import json
import html
from typing import Dict, List
import pandas as pd
from collections import Counter
import branca.colormap as cm
import numpy as np


def load_and_validate_json(uploaded_file) -> Dict:
    """Load and validate the uploaded JSON file"""
    try:
        if uploaded_file is None:
            return None
        content = json.load(uploaded_file)
        if isinstance(content, dict) and "land_data" in content:
            return {"plots": [content]}
        elif isinstance(content, list):
            return {"plots": content}
        elif isinstance(content, dict) and "plots" in content:
            return content
        else:
            st.error(
                "Invalid JSON format. Please ensure your file contains land_data or is a list of land plots."
            )
            return None
    except json.JSONDecodeError:
        st.error("Invalid JSON file. Please check the file format.")
        return None


def create_detail_popup(plot_data: Dict) -> str:
    """Create an enhanced popup with basic info and details button"""
    plot = plot_data["land_data"]
    owners_str = ", ".join([owner["name"] for owner in plot["owners"]])
    popup_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 15px; min-width: 300px;">
        <div style="border-bottom: 2px solid #1f77b4; margin-bottom: 10px;">
            <h4 style="margin: 0; color: #1f77b4;">{plot['plot_id']}</h4>
        </div>
        <div style="margin-bottom: 15px;">
            <span style="background: #e3f2fd; padding: 3px 8px; border-radius: 12px; font-size: 0.9em;">
                {plot['type']}
            </span>
        </div>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
            <tr>
                <td style="padding: 4px 0;"><strong>Size:</strong></td>
                <td>{plot['size']} m²</td>
            </tr>
            <tr>
                <td style="padding: 4px 0;"><strong>Location:</strong></td>
                <td>{plot['location']}</td>
            </tr>
            <tr>
                <td style="padding: 4px 0;"><strong>Owners:</strong></td>
                <td>{owners_str}</td>
            </tr>
        </table>
        <div style="display: flex; justify-content: space-between;">
            <button 
                onclick="document.dispatchEvent(new CustomEvent('showDetails', {{detail: '{plot['plot_id']}}}))"
                style="background-color: #1f77b4; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; flex: 1; margin-right: 5px;">
                View Details
            </button>
            <button 
                onclick="document.dispatchEvent(new CustomEvent('centerPlot', {{detail: '{plot['plot_id']}}}))"
                style="background-color: #2196F3; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; flex: 1; margin-left: 5px;">
                Center Map
            </button>
        </div>
    </div>
    """
    return popup_content


def create_map(plots_data: List[Dict], filtered_plots: List[str] = None):
    """Create an enhanced Folium map with all plot polygons"""
    all_points = []
    plot_locations = Counter()

    # Filter plots if needed
    if filtered_plots:
        plots_to_show = [
            plot
            for plot in plots_data
            if plot["land_data"]["plot_id"] in filtered_plots
        ]
    else:
        plots_to_show = plots_data

    # Collect points and count plots
    for plot in plots_to_show:
        points = plot["land_data"]["site_plan"]["gps_processed_data_summary"][
            "point_list"
        ]
        all_points.extend([(p["latitude"], p["longitude"]) for p in points])
        plot_locations[plot["land_data"]["location"]] += 1

    if not all_points:
        st.error("No plots to display with current filters")
        return None

    center_lat = sum(p[0] for p in all_points) / len(all_points)
    center_lon = sum(p[1] for p in all_points) / len(all_points)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # Add draw control for segmentation
    draw_options = {
        'position': 'topleft',
        'draw_options': {
            'polygon': True,
            'rectangle': True,
            'circle': True,
            'marker': False,
            'circlemarker': False,
            'polyline': False
        }
    }
    plugins.Draw(export=True, **draw_options).add_to(m)

    # Add location clusters
    marker_cluster = MarkerCluster().add_to(m)

    # Add location markers with counts
    for location, count in plot_locations.items():
        location_plots = [
            p for p in plots_to_show if p["land_data"]["location"] == location
        ]
        if location_plots:
            first_plot = location_plots[0]
            first_point = first_plot["land_data"]["site_plan"][
                "gps_processed_data_summary"
            ]["point_list"][0]

            folium.CircleMarker(
                location=[first_point["latitude"], first_point["longitude"]],
                radius=20,
                popup=f"{location}: {count} plots",
                color="#1f77b4",
                fill=True,
                fill_color="#1f77b4",
            ).add_to(marker_cluster)

    # Add plots to map with different colors based on type
    for plot in plots_to_show:
        gps_points = plot["land_data"]["site_plan"]["gps_processed_data_summary"][
            "point_list"
        ]
        plot_coordinates = [
            (point["latitude"], point["longitude"]) for point in gps_points
        ]

        # Color based on land type
        color_map = {
            "Residential": "#2196F3",
            "Commercial": "#FF9800",
            "Industrial": "#4CAF50",
            "Agricultural": "#F44336",
            "Mixed Use": "#9C27B0",
        }
        plot_color = color_map.get(plot["land_data"]["type"], "#2196F3")

        # Create detailed popup
        popup_content = create_detail_popup(plot)
        iframe = IFrame(html=popup_content, width=350, height=300)
        popup = Popup(iframe, max_width=350)

        # Add polygon with styling
        plot_polygon = folium.Polygon(
            locations=plot_coordinates,
            color=plot_color,
            weight=2,
            fill=True,
            fill_color=plot_color,
            fill_opacity=0.4,
            popup=popup,
        )
        plot_polygon.add_to(m)

        # Add corner points
        for i, point in enumerate(gps_points, 1):
            folium.CircleMarker(
                location=[point["latitude"], point["longitude"]],
                radius=4,
                color=plot_color,
                fill=True,
                popup=f"Point {i}",
                weight=2,
            ).add_to(m)

    # Add legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 150px;
                border: 2px solid grey; z-index: 1000; background-color: white;
                padding: 10px; border-radius: 5px;">
        <p style="margin-bottom: 5px"><strong>Land Types</strong></p>
        <p><span style="color: #2196F3">■</span> Residential</p>
        <p><span style="color: #FF9800">■</span> Commercial</p>
        <p><span style="color: #4CAF50">■</span> Industrial</p>
        <p><span style="color: #F44336">■</span> Agricultural</p>
        <p><span style="color: #9C27B0">■</span> Mixed Use</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add measurement tool
    plugins.MeasureControl(position="topleft", active_color="red").add_to(m)

    # Add fullscreen button
    plugins.Fullscreen().add_to(m)

    return m


def search_and_filter_sidebar():
    """Create enhanced search and filter controls in sidebar"""
    st.sidebar.title("Search & Filters")

    filters = {}

    # Quick search
    search_query = st.sidebar.text_input("🔍 Quick Search (Plot ID or Location)")
    if search_query:
        filters["search_query"] = search_query

    st.sidebar.markdown("---")

    # Advanced filters
    with st.sidebar.expander("📍 Location Filter", expanded=True):
        if "land_data" in st.session_state:
            locations = list(
                set(
                    plot["land_data"]["location"]
                    for plot in st.session_state.land_data["plots"]
                )
            )
            selected_locations = st.multiselect("Select Locations", locations)
            if selected_locations:
                filters["locations"] = selected_locations

    with st.sidebar.expander("🏢 Property Type", expanded=True):
        land_types = [
            "Residential",
            "Commercial",
            "Industrial",
            "Agricultural",
            "Mixed Use",
        ]
        selected_types = st.multiselect("Select Types", land_types)
        if selected_types:
            filters["types"] = selected_types

    with st.sidebar.expander("📏 Size Range", expanded=False):
        if "land_data" in st.session_state:
            sizes = [
                plot["land_data"]["size"]
                for plot in st.session_state.land_data["plots"]
            ]
            min_size, max_size = min(sizes), max(sizes)
            size_range = st.slider(
                "Plot Size (m²)",
                min_value=float(min_size),
                max_value=float(max_size),
                value=(float(min_size), float(max_size)),
            )
            filters["size_range"] = size_range

    with st.sidebar.expander("📅 Date Range", expanded=False):
        if "land_data" in st.session_state:
            dates = [
                plot["land_data"]["date_of_instrument"]
                for plot in st.session_state.land_data["plots"]
            ]
            min_date = min(pd.to_datetime(dates))
            max_date = max(pd.to_datetime(dates))
            date_range = st.date_input(
                "Registration Date",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            if len(date_range) == 2:
                filters["date_range"] = date_range

    return filters


def filter_plots(plots_data: List[Dict], filters: Dict) -> List[str]:
    """Filter plots based on search criteria"""
    filtered_plot_ids = []

    for plot in plots_data:
        plot_data = plot["land_data"]
        include_plot = True

        # Quick search
        if "search_query" in filters:
            query = filters["search_query"].lower()
            if (
                query not in plot_data["plot_id"].lower()
                and query not in plot_data["location"].lower()
            ):
                include_plot = False

        # Location filter
        if "locations" in filters and plot_data["location"] not in filters["locations"]:
            include_plot = False

        # Type filter
        if "types" in filters and plot_data["type"] not in filters["types"]:
            include_plot = False

        # Size range filter
        if "size_range" in filters:
            min_size, max_size = filters["size_range"]
            if not (min_size <= plot_data["size"] <= max_size):
                include_plot = False

        # Date range filter
        if "date_range" in filters:
            plot_date = pd.to_datetime(plot_data["date_of_instrument"]).date()
            if not (filters["date_range"][0] <= plot_date <= filters["date_range"][1]):
                include_plot = False

        if include_plot:
            filtered_plot_ids.append(plot_data["plot_id"])

    return filtered_plot_ids


def main():
    st.set_page_config(layout="wide", page_title="Land Registry Platform")

    # Main header
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 20px;'>
            <h1 style='color: #1f77b4;'>🗺️ Land Registry Platform</h1>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # File upload in sidebar
    with st.sidebar:
        uploaded_file = st.file_uploader("📤 Upload Land Data", type=["json"])
        if uploaded_file is not None:
            data = load_and_validate_json(uploaded_file)
            if data is None:
                return
            st.session_state.land_data = data
            st.success(f"✅ Loaded {len(data['plots'])} plots")

    # Search and filter controls
    filters = search_and_filter_sidebar()

    if hasattr(st.session_state, "land_data"):
        filtered_plot_ids = filter_plots(st.session_state.land_data["plots"], filters)

        # Main content area
        map_col, details_col = st.columns([7, 3])

        with map_col:
            m = create_map(st.session_state.land_data["plots"], filtered_plot_ids)
            if m:
                st_folium(m, width=None, height=750)

        with details_col:
            st.markdown(f"### 📍 Showing {len(filtered_plot_ids)} plots")

            if filtered_plot_ids:
                selected_plot_id = st.selectbox(
                    "Select Plot", filtered_plot_ids, format_func=lambda x: f"{x}"
                )

                plot_data = next(
                    plot
                    for plot in st.session_state.land_data["plots"]
                    if plot["land_data"]["plot_id"] == selected_plot_id
                )

                # Display plot details in a clean format
                with st.expander("📄 Plot Details", expanded=True):
                    st.markdown(
                        f"""
                        **Plot ID:** {plot_data['land_data']['plot_id']}  
                        **Type:** {plot_data['land_data']['type']}  
                        **Size:** {plot_data['land_data']['size']} m²  
                        **Location:** {plot_data['land_data']['location']}  
                        **Registration Date:** {plot_data['land_data']['date_of_instrument']}
                    """
                    )

                with st.expander("👥 Ownership Information"):
                    for owner in plot_data["land_data"]["owners"]:
                        st.markdown(
                            f"""
                            **Name:** {owner['name']}  
                            **Address:** {owner['address']}
                        """
                        )
                        st.markdown("---")

                with st.expander("📐 Survey Details"):
                    st.markdown(
                        f"""
                        **Surveyor License:** {plot_data['land_data']['site_plan']['licensed_surveyor_number']}  
                        **Regional Number:** {plot_data['land_data']['site_plan']['regional_number']}  
                        **Survey Date:** {plot_data['land_data']['site_plan']['date_of_letter']}
                    """
                    )

                    st.markdown("##### Boundary Measurements")
                    for bd in plot_data["land_data"]["site_plan"]["bearing_distances"]:
                        st.markdown(
                            f"Point {bd['start_point']} → {bd['end_point']}: {bd['distance']}m"
                        )

                with st.expander("📍 GPS Coordinates"):
                    st.markdown("##### Plot Corner Points")
                    for i, point in enumerate(
                        plot_data["land_data"]["site_plan"][
                            "gps_processed_data_summary"
                        ]["point_list"],
                        1,
                    ):
                        st.markdown(
                            f"""
                            **Point {i}**  
                            Latitude: {point['latitude']}  
                            Longitude: {point['longitude']}
                        """
                        )
                        if i < len(
                            plot_data["land_data"]["site_plan"][
                                "gps_processed_data_summary"
                            ]["point_list"]
                        ):
                            st.markdown("---")

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📥 Export Plot Data", key="export_single"):
                        plot_json = json.dumps(plot_data, indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=plot_json,
                            file_name=f"plot_{plot_data['land_data']['plot_id']}.json",
                            mime="application/json",
                        )

                with col2:
                    if st.button("🖨️ Print Report", key="print_report"):
                        report_html = f"""
                        <div style="padding: 20px;">
                            <h2>Land Plot Report</h2>
                            <h3>Basic Information</h3>
                            <p>Plot ID: {plot_data['land_data']['plot_id']}</p>
                            <p>Type: {plot_data['land_data']['type']}</p>
                            <p>Size: {plot_data['land_data']['size']} m²</p>
                            <p>Location: {plot_data['land_data']['location']}</p>
                            <p>Registration Date: {plot_data['land_data']['date_of_instrument']}</p>
                            
                            <h3>Ownership Information</h3>
                            {''.join(f"<p>Owner: {owner['name']}<br>Address: {owner['address']}</p>" 
                                   for owner in plot_data['land_data']['owners'])}
                            
                            <h3>Survey Information</h3>
                            <p>Surveyor License: {plot_data['land_data']['site_plan']['licensed_surveyor_number']}</p>
                            <p>Regional Number: {plot_data['land_data']['site_plan']['regional_number']}</p>
                            <p>Survey Date: {plot_data['land_data']['site_plan']['date_of_letter']}</p>
                            
                            <h3>GPS Coordinates</h3>
                            {''.join(f"<p>Point {i+1}: ({point['latitude']}, {point['longitude']})</p>"
                                   for i, point in enumerate(plot_data['land_data']['site_plan']['gps_processed_data_summary']['point_list']))}
                        </div>
                        """
                        st.download_button(
                            label="Download Report",
                            data=report_html,
                            file_name=f"report_{plot_data['land_data']['plot_id']}.html",
                            mime="text/html",
                        )
            else:
                st.warning(
                    "No plots match the current filters. Try adjusting your search criteria."
                )

            # Quick Actions Panel
            st.markdown("### ⚡ Quick Actions")
            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if st.button("🔄 Reset Filters"):
                    # Clear all filters
                    st.session_state.filters = {}
                    st.experimental_rerun()

            with action_col2:
                if st.button("📋 Copy Plot ID"):
                    if "selected_plot_id" in locals():
                        st.code(selected_plot_id, language=None)
                        st.success("Plot ID copied to clipboard!")

            # Help section
            with st.expander("❓ Help & Tips"):
                st.markdown(
                    """
                    #### Using the Map
                    - 🖱️ **Zoom**: Use mouse wheel or +/- buttons
                    - 🗺️ **Pan**: Click and drag the map
                    - 📏 **Measure**: Use the measurement tool in top-left
                    - ✏️ **Draw**: Use drawing tools to mark areas
                    
                    #### Filtering Data
                    - 🔍 Use quick search for Plot ID or Location
                    - 📍 Filter by specific locations
                    - 🏢 Filter by property type
                    - 📏 Use size range to find specific plot sizes
                    - 📅 Filter by registration date range
                    
                    #### Tips
                    - Click on a plot to see basic information
                    - Use the 'View Details' button for complete information
                    - Export data for offline use
                    - Print reports for documentation
                """
                )
    else:
        # Landing page when no data is loaded
        st.markdown(
            """
            <div style='text-align: center; padding: 50px;'>
                <h2>Welcome to the Land Registry Platform</h2>
                <p>Upload a JSON file containing land registry data to begin exploring plots.</p>
                <p>Use the upload button in the sidebar to get started.</p>
            </div>
        """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
