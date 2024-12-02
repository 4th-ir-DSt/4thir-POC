import streamlit as st
import json
import logging
from typing import Dict, List, Optional
from modules.data_storage import Storage


class DataLoader:
    def __init__(self):
        self.storage = Storage()

    def load_and_validate_json(self) -> Optional[Dict]:
        """
        Load and validate the uploaded JSON file

        Args:
            uploaded_file: Uploaded file from Streamlit

        Returns:
            Validated data dictionary or None
        """
        try:
            if self.storage is None:
                return None

            # Read the content of the file
            content = self.storage.get_data()

            # Validate the data structure
            if isinstance(content, list):
                # If it's a list of dictionaries, process as is
                return {"plots": [data["data"] for data in content]}
            elif isinstance(content, dict):
                # If it's a single dictionary, wrap it in a list
                return {"plots": [content]}
            else:
                logging.error("Invalid JSON format")
                st.error(
                    "Invalid JSON format. Please ensure your file contains valid plot data."
                )
                return None

        except json.JSONDecodeError:
            logging.error("Invalid JSON file")
            st.error("Invalid JSON file. Please check the file format.")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in data loading: {e}")
            st.error(f"An unexpected error occurred: {e}")
            return None

    @staticmethod
    def extract_plot_metadata(plots: List[Dict]) -> Dict:
        """
        Extract metadata from plots for filtering and display

        Args:
            plots: List of plot dictionaries

        Returns:
            Dictionary of extracted metadata
        """
        metadata = {
            "regions": set(),
            "districts": set(),
            "localities": set(),
            "plot_numbers": set(),
        }

        for plot in plots:
            plot_info = plot.get("plot_info", {})

            # Safely extract and add metadata
            metadata["regions"].add(plot_info.get("region", "Unknown"))
            metadata["districts"].add(plot_info.get("district", "Unknown"))
            metadata["localities"].add(plot_info.get("locality", "Unknown"))
            metadata["plot_numbers"].add(plot_info.get("plot_number", "Unknown"))

        # Filter out None values and sort
        return {k: sorted(filter(None, v)) for k, v in metadata.items()}
