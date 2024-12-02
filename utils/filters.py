import tempfile
import streamlit as st
from typing import List, Dict, Optional

from modules.document_processing import DocumentProcessor


class FilterUtils:
    @staticmethod
    def create_filters(plots_metadata: Dict) -> Dict:
        """
        Create filter sidebar with various filtering options

        Args:
            plots_metadata: Metadata extracted from plots

        Returns:
            Dictionary of selected filters
        """
        filters = {}
        filters["is_document_search"] = False

        st.sidebar.title("🔍 Plot Filters")

        # Region filter
        with st.sidebar.expander("🌍 Region"):
            selected_regions = st.multiselect(
                "Select Regions", plots_metadata.get("regions", [])
            )
            if selected_regions:
                filters["regions"] = selected_regions

        # District filter
        with st.sidebar.expander("🏘️ District"):
            selected_districts = st.multiselect(
                "Select Districts", plots_metadata.get("districts", [])
            )
            if selected_districts:
                filters["districts"] = selected_districts

        # Locality filter
        with st.sidebar.expander("📍 Locality"):
            selected_localities = st.multiselect(
                "Select Localities", plots_metadata.get("localities", [])
            )
            if selected_localities:
                filters["localities"] = selected_localities

        # Plot number search
        st.sidebar.markdown("---")
        plot_search = st.sidebar.text_input("🔎 Search Plot Number")
        if plot_search:
            filters["plot_number"] = plot_search

        # # Coordinate search
        # with st.sidebar.expander("🌐 Coordinate Search"):
        #     col1, col2 = st.columns(2)
        #     with col1:
        #         lat = st.number_input(
        #             "Latitude", min_value=-90.0, max_value=90.0, value=0.0
        #         )
        #     with col2:
        #         lon = st.number_input(
        #             "Longitude", min_value=-180.0, max_value=180.0, value=0.0
        #         )

        #     radius = st.slider(
        #         "Search Radius (km)", min_value=0.1, max_value=50.0, value=1.0
        #     )

        #     match_type = st.selectbox(
        #         label="Search Type", options=["Radius", "Coordinates Match"]
        #     )

        #     if lat != 0.0 or lon != 0.0:
        #         # filters["coordinates"] = {
        #         #     "latitude": lat,
        #         #     "longitude": lon,
        #         #     "radius": radius,
        #         # }

        #         filters["coordinates"] = {
        #             "coordinates": [(lat, lon)],
        #             "radius": radius,
        #             "match_type": (
        #                 "by_radius" if match_type == "Radius" else "coords_match"
        #             ),
        #         }

        # Multiple Coordinate search
        with st.sidebar.expander("🌐 Coordinate Search", expanded=False):
            coordinate_pairs = []

            match_type = st.selectbox(
                label="Search Type", options=["Radius", "Coordinates Match"]
            )
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
                # st.markdown(f"**Coordinate Pair {i + 1}**")
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
                # filters["coordinates"] = (coordinate_pairs, radius)
                filters["coordinates"] = {
                    "coordinates": coordinate_pairs,
                    "radius": radius,
                    "match_type": (
                        "by_radius" if match_type == "Radius" else "coords_match"
                    ),
                }

                if st.button("Clear Filters"):
                    for index in range(0, len(st.session_state.coordinate_pairs)):
                        st.session_state.coordinate_pairs.pop()
                    filters["coordinates"] = {
                        "coordinates": [(0.0, 0.0)],
                        "radius": 0,
                        "match_type": (
                            "by_radius" if match_type == "Radius" else "coords_match"
                        ),
                    }

            filters["is_document_search"] = False

        # Multiple Coordinate search
        with st.sidebar.expander("🌐 Document Search", expanded=False):
            # Initialize the DocumentProcessor
            processor = DocumentProcessor(llm_api_key="your-api-key")
            model = st.selectbox(label="Model", options=["GEMINI", "OPENAI"])
            match_type_2 = st.selectbox(
                label="Search Type",
                options=["Radius", "Coordinates Match"],
                key="match_type_2",
            )
            radius_2 = st.slider(
                "Search Radius (km)", 0.1, 10.0, 1.0, 0.1, key="radius_2"
            )
            # File Uploader
            file = st.file_uploader(
                "Upload your documents (PDF, JPG, PNG)",
                type=["pdf", "jpg", "png"],
                accept_multiple_files=False,
            )
            if file:
                # Save file temporarily
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
                with open(temp_file.name, "wb") as f:
                    f.write(file.read())

                # Process the document
                with st.spinner("Processing Document..."):
                    result = None
                    if (
                        "search_file" in st.session_state
                        and "search_data" in st.session_state
                    ):
                        if st.session_state["search_file"] == file.name:
                            result = st.session_state["search_data"]
                        else:
                            result = processor.process_document(
                                temp_file.name, file.name, model
                            )
                    else:
                        result = processor.process_document(
                            temp_file.name, file.name, model
                        )

                    st.session_state["search_file"] = file.name
                    st.session_state["search_data"] = result

                    data = result.data["results"]["plot_info"]
                    st.markdown(
                        f"""
                            **Plot Information**
                            - **Plot Number:** {data.get("plot_number", "")}
                            - **Area:** {data.get("area", "")}
                            - **Metric:** {data.get("metric", "")}
                            - **Locality:** {data.get("locality", "")}
                            - **District:** {data.get("district", "")}
                            - **Region:** {data.get("region", "")}
                            - **Owners:** {", ".join(data.get("owners", [])) if data.get("owners") else "None"}
                            """
                    )

                with st.spinner("Seaching For Land..."):
                    points = result.data["results"]["point_list"]
                    filters["coordinates"] = {
                        "coordinates": [
                            (point["latitude"], point["longitude"]) for point in points
                        ],
                        "radius": radius_2,
                        "match_type": (
                            "by_radius" if match_type_2 == "Radius" else "coords_match"
                        ),
                    }

                    filters["is_document_search"] = True

        return filters

    @staticmethod
    def apply_filters(plots: List[Dict], filters: Dict) -> List[Dict]:
        """
        Apply filters to the plots

        Args:
            plots: List of plot dictionaries
            filters: Dictionary of selected filters

        Returns:
            Filtered list of plots
        """
        filtered_plots = plots.copy()

        # Region filter
        if "regions" in filters:
            filtered_plots = [
                plot
                for plot in filtered_plots
                if plot.get("plot_info", {}).get("region") in filters["regions"]
            ]

        # District filter
        if "districts" in filters:
            filtered_plots = [
                plot
                for plot in filtered_plots
                if plot.get("plot_info", {}).get("district") in filters["districts"]
            ]

        # Locality filter
        if "localities" in filters:
            filtered_plots = [
                plot
                for plot in filtered_plots
                if plot.get("plot_info", {}).get("locality") in filters["localities"]
            ]

        # Plot number search
        if "plot_number" in filters:
            filtered_plots = [
                plot
                for plot in filtered_plots
                if filters["plot_number"].lower()
                in str(plot.get("plot_info", {}).get("plot_number", "")).lower()
            ]

        # Coordinate search
        if "coordinates" in filters:
            from math import radians, sin, cos, sqrt, atan2

            def haversine_distance(lat1=0, lon1=0, lat2=0, lon2=0):
                """
                Calculate the Haversine distance between two points on the Earth's surface.

                Args:
                    lat1 (float): Latitude of the first point (default 0 if not provided).
                    lon1 (float): Longitude of the first point (default 0 if not provided).
                    lat2 (float): Latitude of the second point (default 0 if not provided).
                    lon2 (float): Longitude of the second point (default 0 if not provided).

                Returns:
                    float: Distance in kilometers between the two points.
                """
                R = 6371  # Earth radius in kilometers

                # Convert degrees to radians
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

                # Haversine formula
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                distance = R * c

                return distance

            coord_filter = filters["coordinates"]
            match_type = coord_filter.get("match_type", "by_radius")
            radius = coord_filter.get("radius", 0)

            if match_type == "by_radius":
                # Filter by radius
                filtered_plots = [
                    plot
                    for plot in filtered_plots
                    if any(
                        any(
                            haversine_distance(
                                lat, lon, point["latitude"], point["longitude"]
                            )
                            <= radius
                            for lat, lon in coord_filter["coordinates"]
                        )
                        for point in plot.get("point_list", [])
                    )
                ]
            else:
                # Match by approximate latitude and longitude
                def approx_match(lat1, lon1, lat2, lon2, tolerance=0.01):
                    """
                    Check if two coordinates match approximately within a tolerance.

                    Args:
                        lat1 (float): Latitude of the first point.
                        lon1 (float): Longitude of the first point.
                        lat2 (float): Latitude of the second point.
                        lon2 (float): Longitude of the second point.
                        tolerance (float): Acceptable difference for latitude and longitude.

                    Returns:
                        bool: True if coordinates match approximately, False otherwise.
                    """
                    return (
                        lat1 is None or lat2 is None or abs(lat1 - lat2) <= tolerance
                    ) and (
                        lon1 is None or lon2 is None or abs(lon1 - lon2) <= tolerance
                    )

                filtered_plots = [
                    plot
                    for plot in filtered_plots
                    if any(
                        any(
                            approx_match(
                                lat, lon, point["latitude"], point["longitude"]
                            )
                            for lat, lon in coord_filter["coordinates"]
                        )
                        for point in plot.get("point_list", [])
                    )
                ]

            if filters["is_document_search"]:
                with st.sidebar:
                    st.markdown("## Matching Site Plans")
                    with st.expander("Site Plans"):
                        for plot in filtered_plots:
                            data = plot["plot_info"]
                            with st.sidebar:
                                st.markdown(
                                    f"""
                                **Plot Information**
                                - **Plot Number:** {data.get("plot_number", "")}
                                - **Area:** {data.get("area", "")}
                                - **Metric:** {data.get("metric", "")}
                                - **Locality:** {data.get("locality", "")}
                                - **District:** {data.get("district", "")}
                                - **Region:** {data.get("region", "")}
                                - **Owners:** {", ".join(data.get("owners", [])) if data.get("owners") else "None"}
                                """
                                )

        return filtered_plots, filters["is_document_search"]
