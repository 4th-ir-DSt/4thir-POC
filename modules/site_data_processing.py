from dataclasses import dataclass
import json
import math
import re
from typing import List, Tuple, Optional
from pyproj import Proj, Transformer, transform

from utils.convert_string_to_float import to_float


@dataclass
class Point:
    """
    Data class representing a survey point with its coordinates and relationships.

    Attributes:
        name (str): Identifier of the point (e.g., "KNUST TREK 10/2021/1")
        x_coord (float): X coordinate in Ghana National Grid system
        y_coord (float): Y coordinate in Ghana National Grid system
        bearing_to_next (Optional[str]): Bearing to the next point in DMS format (e.g., "13°10'")
        distance_to_next (Optional[float]): Distance to the next point in meters
        next_point (Optional[str]): Identifier of the next connected point
        latitude (Optional[float]): Converted latitude in decimal degrees
        longitude (Optional[float]): Converted longitude in decimal degrees
    """

    name: str
    x_coord: float
    y_coord: float
    bearing_to_next: Optional[str] = None
    distance_to_next: Optional[float] = None
    reference_point: Optional[bool] = False
    next_point: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LandDataProcessor:
    """
    Processes land survey data and converts coordinates between Ghana National Grid and WGS84.

    This class handles the conversion of coordinates, processing of bearings and distances,
    and organization of survey data into a structured format.
    """

    def __init__(self):
        """
        Initialize the processor with coordinate transformation settings.
        Sets up the coordinate transformer from Ghana National Grid (EPSG:25000) to WGS84 (EPSG:4326).
        """
        # Initialize coordinate transformer for Ghana National Grid to WGS84

        self.transformer = Transformer.from_crs(
            "epsg:2136", "epsg:4326", always_xy=True
        )

    def convert_dms_to_decimal(self, dms_str: str) -> float:
        """
        Convert bearing from Degrees-Minutes-Seconds (DMS) format to decimal degrees.

        Args:
            dms_str (str): Bearing in DMS format (e.g., "13°10'")

        Returns:
            float: Bearing in decimal degrees

        Examples:
            >>> convert_dms_to_decimal("13°10'")
            13.166666666666666
        """
        if not dms_str:
            return 0.0

        # Split the DMS string into components
        parts = dms_str.replace("°", " ").replace("'", " ").strip().split()
        degrees = to_float(parts[0])
        minutes = to_float(parts[1]) if len(parts) > 1 else 0
        return degrees + (minutes / 60)

    def ghana_grid_to_latlon(
        self, easting: float, northing: float
    ) -> Tuple[float, float]:
        """
        Convert coordinates from Ghana National Grid to WGS84 latitude/longitude.

        Args:
            easting (float): Easting coordinate in Ghana National Grid
            northing (float): Northing coordinate in Ghana National Grid

        Returns:
            Tuple[float, float]: (latitude, longitude) in decimal degrees
        """
        # Transform coordinates using the initialized transformer
        # lon, lat = self.transformer.transform(easting, northing)
        ghana_proj = Proj(init="EPSG:2136")
        wgs84_proj = Proj(init="EPSG:4326")

        lon, lat = transform(ghana_proj, wgs84_proj, northing, easting)
        return (lat, lon)

    def identify_reference_point_pattern(self, text):
        """
        Identifies if a given text matches patterns like:
        - 'SMDA A001 191'
        - 'SMDA A001 19 1'
        - 'SGA.CORS 2020 3'

        :param text: The input string to check.
        :return: True if the text matches the pattern, False otherwise.
        """
        pattern = r"^[A-Z]+(?:\.[A-Z]+)?\s[A-Z0-9]+\s(?:\d+\s?)+$"
        return bool(re.match(pattern, text))

    def order_points_by_bearing(self, point_list):
        """
        Order points based on clockwise bearing from the first point.
        """
        ref_point = point_list[0]
        ref_lat, ref_lon = ref_point["latitude"], ref_point["longitude"]

        def bearing(point):
            lat, lon = point["latitude"], point["longitude"]
            angle = math.atan2(lon - ref_lon, lat - ref_lat)
            return (math.degrees(angle) + 360) % 360  # Normalize to [0, 360)

        return sorted(point_list, key=bearing)

    def process_land_data(self, data: dict) -> dict:
        """
        Process land survey data and convert coordinates.

        Args:
            data (dict): Input JSON data containing survey information

        Returns:
            dict: Processed data including converted coordinates and structured survey information

        The returned dictionary contains:
        - Plot information (number, area, location details)
        - Survey points with original and converted coordinates
        - Boundary points with converted coordinates
        - Bearings and distances between points
        """
        # Extract coordinate data from the input
        plan_data = data["site_plan_data"]["plan_data"]
        points: List[Point] = []

        # Process each survey point
        for i in range(len(plan_data["from"])):
            # Only process points with valid coordinates
            if plan_data["x_coords"][i] and plan_data["y_coords"][i]:
                # Create Point object with survey data

                name = plan_data["from"][i] if i < len(plan_data["from"]) else None

                x_coord = (
                    to_float(plan_data["x_coords"][i])
                    if i < len(plan_data["x_coords"])
                    else None
                )

                y_coord = (
                    to_float(plan_data["y_coords"][i])
                    if i < len(plan_data["y_coords"])
                    else None
                )

                bearing_to_next = (
                    plan_data["bearing"][i] if i < len(plan_data["bearing"]) else None
                )
                distance_to_next = (
                    (
                        to_float(plan_data["distance"][i])
                        if i < len(plan_data["distance"])
                        else None
                    ),
                )
                next_point = plan_data["to"][i] if i < len(plan_data["to"]) else None

                point = Point(
                    name=name,
                    x_coord=x_coord,
                    y_coord=y_coord,
                    bearing_to_next=bearing_to_next,
                    distance_to_next=distance_to_next,
                    next_point=next_point,
                    reference_point=self.identify_reference_point_pattern(name),
                )

                # Convert coordinates to latitude/longitude
                lat, lon = self.ghana_grid_to_latlon(point.x_coord, point.y_coord)
                point.latitude = lat  # round(lat, 8)
                point.longitude = lon  # round(lon, 8)
                points.append(point)

        # Process boundary coordinates
        boundary_coords = []
        north_easterns = data["site_plan_data"]["north_easterns"]

        # Convert each boundary point
        for i in range(len(north_easterns["norths"])):
            north = (
                to_float(north_easterns["norths"][i])
                if i < len(north_easterns["norths"])
                else 0
            )
            east = (
                to_float(north_easterns["easterns"][i])
                if i < len(north_easterns["easterns"])
                else 0
            )
            lat, lon = self.ghana_grid_to_latlon(north, east)
            boundary_coords.append(
                {
                    "point": f"Boundary_{i+1}",
                    "northing": north,
                    "easting": east,
                    "latitude": round(lat, 8),
                    "longitude": round(lon, 8),
                }
            )

        result = {
            "plot_info": {
                "plot_number": data.get("plot_number", ""),
                "area": to_float(data["area"]),
                "metric": data.get("metric", ""),
                "locality": data.get("locality", ""),
                "district": data.get("district", ""),
                "region": data.get("region", ""),
                "owners": data.get("owners", []),
                "date": data.get("date", ""),
                "scale": data.get("scale", ""),
                "other_location_details": data.get("other_location_details", ""),
                "surveyors_name": data.get("surveyors_name", ""),
                "surveyors_location": data.get("surveyors_location", ""),
                "surveyors_reg_number": data.get("surveyors_reg_number", ""),
                "regional_number": data.get("regional_number", ""),
                "reference_number": data.get("reference_number", ""),
            },
            "survey_points": [
                {
                    "point_name": p.name,
                    "original_coords": {
                        "x": p.x_coord,
                        "y": p.y_coord,
                        "ref_point": p.reference_point,
                    },
                    "converted_coords": {
                        "latitude": p.latitude,
                        "longitude": p.longitude,
                        "ref_point": p.reference_point,
                    },
                    "next_point": {
                        "name": p.next_point,
                        "bearing": p.bearing_to_next,
                        "bearing_decimal": (
                            self.convert_dms_to_decimal(p.bearing_to_next)
                            if p.bearing_to_next
                            else None
                        ),
                        "distance": p.distance_to_next,
                    },
                }
                for p in points
            ],
            "boundary_points": boundary_coords,
        }

        point_list = []
        for coord in result["survey_points"]:
            if not coord["converted_coords"]["ref_point"]:
                point_list.append(coord["converted_coords"])

        result["point_list"] = self.order_points_by_bearing(point_list)

        return result