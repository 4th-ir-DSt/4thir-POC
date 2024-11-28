import streamlit as st
import folium
from streamlit_folium import folium_static
import os
import json
import datetime


def load_css():
    # External CSS dependencies
    st.markdown(
        """
        <meta charset="UTF-8">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/mdbootstrap/4.19.1/css/mdb.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        <link rel="icon" href="https://www.4th-ir.com/favicon.ico">
        
        <title>4thir-POC-repo</title>
        <meta name="title" content="4thir-POC-repo" />
        <meta name="description" content="view our proof of concepts" />

        <!-- Open Graph / Facebook -->
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://4thir-poc-repositoty.streamlit.app/" />
        <meta property="og:title" content="4thir-POC-repo" />
        <meta property="og:description" content="view our proof of concepts" />
        <meta property="og:image" content="https://www.4th-ir.com/favicon.ico" />

        <!-- Twitter -->
        <meta property="twitter:card" content="summary_large_image" />
        <meta property="twitter:url" content="https://4thir-poc-repositoty.streamlit.app/" />
        <meta property="twitter:title" content="4thir-POC-repo" />
        <meta property="twitter:description" content="view our proof of concepts" />
        <meta property="twitter:image" content="https://www.4th-ir.com/favicon.ico" />

        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        """,
        unsafe_allow_html=True,
    )

    # Custom CSS to hide Streamlit components and adjust layout
    st.markdown(
        """
        <style>
        /* Hide the Streamlit header and menu */
        header {visibility: hidden;}
                /* Optionally, hide the footer */
                .streamlit-footer {display: none;}
                /* Hide your specific div class, replace class name with the one you identified */
                .st-emotion-cache-uf99v8 {display: none;}


        .hero-section {
            background: white;
            text: white;
            padding: 0rem 0;
            width: 0%;
            height:2px;
        }
        .feature-icon {
            width: 4rem;
            height: 4rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
            box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
        }
        .card {
            transition: box-shadow 0.3s ease;
        }
        .card:hover {
            box-shadow: 0 1rem 3rem rgba(0,0,0,0.175);
        }
         .project-card {
            border-radius: 12px;
            border-left: 4px solid #0d6efd;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .project-icon {
            width: 48px;
            height: 48px;
            background: rgba(13, 110, 253, 0.1);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
        }
        .project-meta {
            font-size: 0.875rem;
            color: #6c757d;
        }
      
        .nav-link {
            font-weight: 500;
            padding: 0.5rem 1rem !important;
        }
        .nav-links {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        @media (max-width: 768px) {
            .navbar .container {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            .nav-links {
                flex-direction: column;
                align-items: flex-start;
                width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_navbar():
    st.html(
        """
             
        <nav class="navbar fixed-top navbar-expand-lg navbar-dark bg-white text-bold shadow-sm">
            <a class="navbar-brand text-primary" href="#" target="_blank">
                <img src="https://www.4th-ir.com/favicon.ico" alt="4th-ir logo">
                Accra Traffic Visualizer
            </a>
        </nav>

        <div class="hero-section">
            <div class="container text-center">
                <h1 class="display-4 text-white mb-3">4th-IR POC Page</h1>
                <!--<p class="lead text-white">Exploring the future of AI through innovative applications</p>-->
            </div>
        </div>
        
    <div id="projects">
    </div>

    
        """
    )




def create_google_maps_traffic_html(api_key):
    """
    Create an HTML snippet with Google Maps traffic layer for Accra
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Accra Traffic Map</title>
        <style>
            #map {{
                height: 100%;
                width: 100%;
            }}
            html, body {{
                height: 100%;
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            function initMap() {{
                // Coordinates for Accra
                const accra = {{ lat: 5.6037, lng: -0.1870 }};
                
                // Create the map
                const map = new google.maps.Map(document.getElementById('map'), {{
                    zoom: 12,
                    center: accra,
                    mapTypeId: 'roadmap'
                }});
                
                // Add traffic layer
                const trafficLayer = new google.maps.TrafficLayer();
                trafficLayer.setMap(map);
            }}
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" 
                async defer></script>
    </body>
    </html>
    """
    return html

def main():
    create_navbar()
    load_css()
    
    
    # Input for Google Maps API Key
    api_key = st.secrets["GOOGLE_MAPS_API_KEY"]
    if api_key:
        try:
            # Create an HTML component with the Google Maps traffic layer
            traffic_map_html = create_google_maps_traffic_html(api_key)
            
            # Display the map using st.components.v1.html
            st.components.v1.html(traffic_map_html, height=600)
            
            # Additional information
            st.sidebar.header("Traffic Information")
            st.sidebar.markdown("""
            ### Traffic Layer Explanation
            - Green: No traffic delays
            - Yellow: Some traffic
            - Red: Heavy traffic congestion
            
            ### How to Use
            - Zoom in/out using mouse scroll
            - Click and drag to move around
            - Traffic colors update in real-time
            """)
        
        except Exception as e:
            st.error(f"Error creating map: {e}")
    else:
        st.info("Please enter a valid Google Maps API Key to view the traffic map")

if __name__ == "__main__":
    main()

