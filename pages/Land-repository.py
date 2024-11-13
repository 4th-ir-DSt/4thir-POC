import streamlit as st
import folium
from folium import plugins
from streamlit_folium import folium_static
import pandas as pd
import json
from datetime import datetime
import random

class LandSurveyorApp:
    def __init__(self):
        self.initialize_session_state()
        
    def initialize_session_state(self):
        if 'land_records' not in st.session_state:
            # Initialize with empty DataFrame with correct column types
            st.session_state.land_records = pd.DataFrame({
                'plot_id': pd.Series(dtype='str'),
                'owner_name': pd.Series(dtype='str'),
                'location': pd.Series(dtype='str'),
                'area_acres': pd.Series(dtype='float'),
                'land_use': pd.Series(dtype='str'),
                'registration_date': pd.Series(dtype='datetime64[ns]'),
                'geometry': pd.Series(dtype='object')
            })
            
    def generate_gps_address(self):
        """Generate unique GPS address in GU-XXX-XXXX format"""
        while True:
            area_code = random.randint(100, 999)
            plot_num = random.randint(1000, 9999)
            gps_address = f"GU-{area_code}-{plot_num}"
            if gps_address not in st.session_state.land_records['plot_id'].values:
                return gps_address
                
    def create_map(self, center=[7.9465, -1.0232], zoom=7):
        """Create Folium map with satellite and drawing capabilities"""
        m = folium.Map(location=center, zoom_start=zoom)
        
        # Add satellite tile layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False
        ).add_to(m)
        
        # Add OpenStreetMap as alternative layer
        folium.TileLayer('OpenStreetMap').add_to(m)
        
        # Add drawing tools
        draw = plugins.Draw(
            export=True,
            position='topleft',
            draw_options={
                'rectangle': True,
                'polygon': True,
                'circle': False,
                'marker': True,
                'circlemarker': False,
                'polyline': True
            }
        )
        m.add_child(draw)
        
        # Add measurement tool
        plugins.MeasureControl(position='bottomleft').add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add scale and mouse position
        plugins.MousePosition().add_to(m)
        plugins.Fullscreen().add_to(m)
        
        # Add existing plots to map if there are any records
        if not st.session_state.land_records.empty:
            for _, record in st.session_state.land_records.iterrows():
                if pd.notna(record.get('geometry')) and isinstance(record['geometry'], dict):
                    try:
                        folium.GeoJson(
                            record['geometry'],
                            popup=f"Plot ID: {record['plot_id']}<br>Owner: {record['owner_name']}",
                            style_function=lambda x: {
                                'fillColor': '#ff7800',
                                'color': '#000000',
                                'weight': 2,
                                'fillOpacity': 0.35
                            }
                        ).add_to(m)
                    except Exception as e:
                        st.error(f"Error displaying plot {record['plot_id']}: {str(e)}")
        
        return m
        
    def add_land_record_form(self):
        """Create form for adding new land records"""
        with st.form("add_land_record"):
            col1, col2 = st.columns(2)
            
            with col1:
                plot_id = self.generate_gps_address()
                st.write(f"Generated Plot ID: {plot_id}")
                
                owner_name = st.text_input("Owner Name")
                location = st.text_input("Location Description")
                area_acres = st.number_input("Area (acres)", min_value=0.0)
                land_use = st.selectbox(
                    "Land Use",
                    ["Residential", "Commercial", "Agricultural", "Industrial", "Mining"]
                )
            
            with col2:
                st.write("Draw the plot boundary on the map:")
                st.info("1. Use the drawing tools on the left side of the map\n"
                       "2. After drawing, click the export button (in drawing tools)\n"
                       "3. Copy the generated GeoJSON and paste it below")
                
            m = self.create_map()
            folium_static(m, width=1200)
            
            geometry = st.text_area(
                "GeoJSON of drawn area (paste from map draw export)",
                height=100
            )
            
            submitted = st.form_submit_button("Submit")
            if submitted:
                if not owner_name or not location or not geometry:
                    st.error("Please fill in all required fields and draw the plot boundary.")
                    return
                
                try:
                    geometry_dict = json.loads(geometry)
                    new_record = pd.DataFrame([{
                        'plot_id': plot_id,
                        'owner_name': owner_name,
                        'location': location,
                        'area_acres': float(area_acres),
                        'land_use': land_use,
                        'registration_date': pd.Timestamp.now(),
                        'geometry': geometry_dict
                    }])
                    
                    st.session_state.land_records = pd.concat(
                        [st.session_state.land_records, new_record],
                        ignore_index=True
                    )
                    st.success("Land record added successfully!")
                except json.JSONDecodeError:
                    st.error("Invalid GeoJSON format. Please draw and export from the map.")
                except Exception as e:
                    st.error(f"Error adding record: {str(e)}")
    
    def show_records(self):
        """Display existing land records"""
        if not st.session_state.land_records.empty:
            st.write("### Existing Land Records")
            # Create a copy without geometry for display
            display_df = st.session_state.land_records.drop('geometry', axis=1).copy()
            st.dataframe(display_df)
            
            st.write("### Map View of All Records")
            m = self.create_map()
            folium_static(m, width=1200)
        else:
            st.info("No land records found. Add some records to see them here.")
        
    def export_data(self):
        """Export land records as GeoJSON"""
        if not st.session_state.land_records.empty:
            records_dict = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for _, record in st.session_state.land_records.iterrows():
                if pd.notna(record.get('geometry')) and isinstance(record['geometry'], dict):
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "plot_id": record['plot_id'],
                            "owner_name": record['owner_name'],
                            "location": record['location'],
                            "area_acres": float(record['area_acres']),
                            "land_use": record['land_use'],
                            "registration_date": str(record['registration_date'])
                        },
                        "geometry": record['geometry'].get('geometry', record['geometry'])
                    }
                    records_dict["features"].append(feature)
            
            st.download_button(
                "Export Data (GeoJSON)",
                data=json.dumps(records_dict, indent=2),
                file_name="land_records.geojson",
                mime="application/json"
            )
        else:
            st.info("No records to export. Add some land records first.")

def main():
    st.set_page_config(page_title="Land Surveyor Application", layout="wide")
    
    st.title("Land Surveyor Application")
    st.markdown("""
    This application helps surveyors record and manage land plots with the following features:
    - Interactive map with satellite view
    - Drawing tools for plot boundaries
    - Measurement tools for distances and areas
    - GPS address generation
    - Data export capabilities
    """)
    
    app = LandSurveyorApp()
    
    menu = st.sidebar.selectbox(
        "Select Action",
        ["View Map", "Add Land Record", "View Records", "Export Data"]
    )
    
    if menu == "View Map":
        st.write("### Interactive Map")
        m = app.create_map()
        folium_static(m, width=1200)
    
    elif menu == "Add Land Record":
        st.write("### Add New Land Record")
        app.add_land_record_form()
    
    elif menu == "View Records":
        app.show_records()
    
    elif menu == "Export Data":
        st.write("### Export Land Records")
        app.export_data()

if __name__ == "__main__":
    main()