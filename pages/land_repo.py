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
    <div style="font-family: Arial, sans-serif; padding: 15px; padding-bottom:3px; min-width: 300px;">
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
        "position": "topleft",
        "draw_options": {
            "polygon": True,
            "rectangle": True,
            "circle": True,
            "marker": False,
            "circlemarker": False,
            "polyline": False,
        },
    }
    plugins.Draw(export=True, **draw_options).add_to(m)

    # # Initialize marker cluster with custom count display
    marker_cluster = MarkerCluster().add_to(m)

    # # Add markers for each plot location with styled count label
    for location, count in plot_locations.items():
        location_plots = [
            p for p in plots_to_show if p["land_data"]["location"] == location
        ]
        if location_plots:
            first_plot = location_plots[0]
            first_point = first_plot["land_data"]["site_plan"][
                "gps_processed_data_summary"
            ]["point_list"][0]

            # Custom DivIcon for centered count label with improved styling
            folium.Marker(
                location=[first_point["latitude"], first_point["longitude"]],
                icon=folium.DivIcon(
                    html=f"""
                        <div style="
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            width: 30px;
                            height: 30px;
                            border-radius: 50%;
                            background-color: #1f77b4;
                            color: white;
                            font-size: 14px;
                            font-weight: bold;
                            border: 2px solid white;
                            text-align: center;
                        ">
                            {count}
                        </div>
                    """
                ),
                popup=f"{location}: {count} plots",
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
        iframe = IFrame(html=popup_content, width=350, height=230)
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
                radius=2,
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

    # Multiple Coordinate search
    with st.sidebar.expander("🎯 Coordinate Search", expanded=False):
        coordinate_pairs = []
        radius = st.slider("Search Radius (km)", 0.1, 10.0, 1.0, 0.1)

        # Initialize session state for coordinate pairs
        if "coordinate_pairs" not in st.session_state:
            st.session_state.coordinate_pairs = [{"lat": "", "lon": ""}]

        # Add coordinate pair button
        if st.button("Add Another Coordinate Pair"):
            st.session_state.coordinate_pairs.append({"lat": "", "lon": ""})

        # Remove coordinate pair button
        if len(st.session_state.coordinate_pairs) > 1 and st.button(
            "Remove Last Coordinate Pair"
        ):
            st.session_state.coordinate_pairs.pop()

        # Create input fields for each coordinate pair
        for i, coord_pair in enumerate(st.session_state.coordinate_pairs):
            st.markdown(f"**Coordinate Pair {i + 1}**")
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input(
                    f"Latitude {i + 1}",
                    min_value=-90.0,
                    max_value=90.0,
                    value=float(coord_pair["lat"]) if coord_pair["lat"] else 0.0,
                    format="%.6f",
                    key=f"lat_{i}",
                )
            with col2:
                lon = st.number_input(
                    f"Longitude {i + 1}",
                    min_value=-180.0,
                    max_value=180.0,
                    value=float(coord_pair["lon"]) if coord_pair["lon"] else 0.0,
                    format="%.6f",
                    key=f"lon_{i}",
                )

            st.session_state.coordinate_pairs[i]["lat"] = lat
            st.session_state.coordinate_pairs[i]["lon"] = lon

            if lat != 0.0 or lon != 0.0:
                coordinate_pairs.append((lat, lon))

        if coordinate_pairs:
            filters["coordinates"] = (coordinate_pairs, radius)

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

    # Overlap detection in separate expander
    with st.sidebar.expander("🔍 Overlap Detection", expanded=False):
        show_overlapping = st.checkbox("Show Overlapping Plots")
        if show_overlapping:
            filters["show_overlapping"] = True

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

    return filters


def find_overlapping_plots(plots_data: List[Dict]) -> List[str]:
    """Find all plots that overlap with any other plot"""
    from shapely.geometry import Polygon

    overlapping_ids = set()

    try:
        for i, plot1 in enumerate(plots_data):
            # Convert plot1 coordinates to the correct format
            coords1 = [
                (
                    point["longitude"],
                    point["latitude"],
                )  # Note: Shapely uses (lon, lat) order
                for point in plot1["land_data"]["site_plan"][
                    "gps_processed_data_summary"
                ]["point_list"]
            ]

            # Skip if less than 3 points (not a valid polygon)
            if len(coords1) < 3:
                continue

            try:
                poly1 = Polygon(coords1)
                if not poly1.is_valid:
                    continue

                for j, plot2 in enumerate(plots_data[i + 1 :], i + 1):
                    coords2 = [
                        (point["longitude"], point["latitude"])
                        for point in plot2["land_data"]["site_plan"][
                            "gps_processed_data_summary"
                        ]["point_list"]
                    ]

                    if len(coords2) < 3:
                        continue

                    try:
                        poly2 = Polygon(coords2)
                        if not poly2.is_valid:
                            continue

                        if poly1.intersects(poly2):
                            overlapping_ids.add(plot1["land_data"]["plot_id"])
                            overlapping_ids.add(plot2["land_data"]["plot_id"])
                    except Exception as e:
                        st.error(
                            f"Error processing plot {plot2['land_data']['plot_id']}: {str(e)}"
                        )
                        continue

            except Exception as e:
                st.error(
                    f"Error processing plot {plot1['land_data']['plot_id']}: {str(e)}"
                )
                continue

    except Exception as e:
        st.error(f"Error in overlap detection: {str(e)}")

    return list(overlapping_ids)


def filter_by_coordinates(
    plots_data: List[Dict], center_lat: float, center_lon: float, radius_km: float
) -> List[str]:
    """Filter plots within a certain radius of given coordinates"""
    from math import radians, sin, cos, sqrt, atan2

    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371  # Earth's radius in kilometers
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    filtered_ids = []
    for plot in plots_data:
        # Check all points of the plot, not just the first one
        plot_points = plot["land_data"]["site_plan"]["gps_processed_data_summary"][
            "point_list"
        ]
        for point in plot_points:
            distance = haversine_distance(
                center_lat, center_lon, point["latitude"], point["longitude"]
            )
            if distance <= radius_km:
                filtered_ids.append(plot["land_data"]["plot_id"])
                break  # If any point is within radius, include the plot

    return filtered_ids


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

        # Coordinate filter with multiple pairs
        if "coordinates" in filters and filtered_plot_ids:
            coordinate_pairs, radius = filters["coordinates"]
            coordinate_filtered_ids = set()

            # Check each coordinate pair
            for lat, lon in coordinate_pairs:
                matching_ids = filter_by_coordinates(
                    [
                        p
                        for p in plots_data
                        if p["land_data"]["plot_id"] in filtered_plot_ids
                    ],
                    lat,
                    lon,
                    radius,
                )
                coordinate_filtered_ids.update(matching_ids)

            filtered_plot_ids = list(coordinate_filtered_ids)

        # Overlap filter
        if "show_overlapping" in filters and filtered_plot_ids:
            plots_to_check = [
                p for p in plots_data if p["land_data"]["plot_id"] in filtered_plot_ids
            ]
            overlapping_ids = find_overlapping_plots(plots_to_check)
            if overlapping_ids:  # Only filter if overlapping plots are found
                filtered_plot_ids = [
                    pid for pid in filtered_plot_ids if pid in overlapping_ids
                ]

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
                    st.rerun()

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

main()
