from typing import List, Dict, Optional
from collections import Counter
import folium
from folium import plugins, IFrame, Popup
from folium.plugins import MarkerCluster


class MapUtils:
    def __init__(self, plots_data: List[Dict]):
        self.plots_data = self._normalize_data(plots_data)

    def _normalize_data(self, plots_data: List[Dict]) -> List[Dict]:
        """Normalize different data structures into a standard format."""
        normalized_data = []
        for plot in plots_data:
            if "land_data" in plot:
                normalized_data.append(plot)
            elif "plot_info" in plot:
                normalized_data.append(
                    {
                        "land_data": {
                            "plot_id": plot["plot_info"]["plot_number"],
                            "size": plot["plot_info"]["area"],
                            "type": (
                                "Acres"
                                if plot["plot_info"]["metric"] == "Acres"
                                else "Unknown"
                            ),
                            "location": f"{plot["plot_info"]["region"]}, {plot["plot_info"]["district"]} - {plot["plot_info"]["locality"]}",
                            "owners": plot["plot_info"].get("owners", []),
                            "site_plan": {
                                "gps_processed_data_summary": {
                                    "point_list": [
                                        {
                                            "latitude": p["latitude"],
                                            "longitude": p["longitude"],
                                        }
                                        for p in plot["point_list"]
                                    ]
                                }
                            },
                        }
                    }
                )
        return normalized_data

    def _create_detail_popup(self, plot_data: Dict) -> str:
        """Create an enhanced popup with basic info and details button."""
        plot = plot_data["land_data"]
        owners_str = ", ".join([owner for owner in plot["owners"]])
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 15px; padding-bottom:3px; height:auto; min-width: 300px; max-width: 340px; overflow:hidden">
            <div style="border-bottom: 2px solid #1f77b4; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #1f77b4;">Plot Number: {plot['plot_id']}</h4>
            </div>
            <div style="margin-bottom: 15px;">
                <span style="background: #e3f2fd; padding: 3px 8px; border-radius: 12px; font-size: 0.9em;">
                    {plot['type']}
                </span>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                <tr>
                    <td style="padding: 4px 0;"><strong>Size: </strong></td>
                    <td>{plot['size']} m²</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0; padding-right:5px"><strong>Location: </strong></td>
                    <td>{plot['location']}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>Owners: </strong></td>
                    <td>{owners_str}</td>
                </tr>
            </table>
            <div style="display: flex; justify-content: space-between;">
                <button 
                    onclick="document.dispatchEvent(new CustomEvent('showDetails', {{detail: '{plot['plot_id']}'}}))"
                    style="background-color: #1f77b4; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; flex: 1; margin-right: 5px; max-width: 300px;">
                    View Details
                </button>
            </div>
        </div>
        """
        return popup_content

    def create_map(
        self,
        filtered_plots: Optional[List[Dict]] = None,
        filter_type: Optional[bool] = False,
    ):
        """Create an enhanced Folium map with all plot polygons."""
        all_points = []
        plot_locations = Counter()

        plots_to_show = self._normalize_data(filtered_plots) or self.plots_data

        # Collect points and count plots
        for plot in plots_to_show:
            points = plot["land_data"]["site_plan"]["gps_processed_data_summary"][
                "point_list"
            ]
            all_points.extend([(p["latitude"], p["longitude"]) for p in points])
            plot_locations[plot["land_data"]["location"]] += 1

        if not all_points:
            raise ValueError("No plots to display with current filters.")

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

        # Initialize marker cluster with custom count display
        marker_cluster = MarkerCluster().add_to(m)

        # Add markers for each plot location with styled count label
        for location, count in plot_locations.items():
            location_plots = [
                p for p in plots_to_show if p["land_data"]["location"] == location
            ]
            if location_plots:
                first_plot = location_plots[0]
                first_point = first_plot["land_data"]["site_plan"][
                    "gps_processed_data_summary"
                ]["point_list"][0]

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

        # Add polygons and popups
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
            plot_color = (
                color_map.get(plot["land_data"]["type"], "#2196F3")
                if not filter_type
                else "#FF0000"
            )
            popup_content = self._create_detail_popup(plot)
            iframe = IFrame(html=popup_content, width=350, height=245)
            popup = Popup(iframe, max_width=355)

            folium.Polygon(
                locations=plot_coordinates,
                color=plot_color,
                weight=2,
                fill=True,
                fill_color=plot_color,
                fill_opacity=0.4,
                popup=popup,
            ).add_to(m)

        return m
