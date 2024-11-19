import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
from geopy.distance import geodesic
from collections import defaultdict
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import numpy.random as rnd
import googlemaps
from datetime import datetime
import polyline


def load_css():
    # External CSS dependencies
    st.markdown(
        """
        <link href="https://cdnjs.cloudflare.com/ajax/libs/mdbootstrap/4.19.1/css/mdb.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        """,
        unsafe_allow_html=True
    )

    # Custom CSS to hide Streamlit components and adjust layout
    st.markdown(
        """
        <style>
            header {visibility: hidden;}
            .main {
                margin-top: -20px;
                padding-top: 10px;
            }
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .navbar {
                padding: 1rem;
                margin-bottom: 2rem;
            }
            .card {
                padding: 1rem;
                margin-bottom: 1rem;
                transition: transform 0.2s;
                border-radius:5px;
            }
            .card:hover {
                transform: scale(1.02);
            }
            .navbar-brand img {
                margin-right: 10px;
                height: 30px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

def create_navbar():
    st.markdown(
        """
        <nav class="navbar fixed-top navbar-expand-lg navbar-dark" style="background-color: #4267B2;">
            <a class="navbar-brand" href="#" target="_blank">
                <img src="https://www.4th-ir.com/favicon.ico" alt="4th-ir logo">
                Ride Router
            </a>
        </nav>
        """,
        unsafe_allow_html=True
    )
load_css()
create_navbar()

class SOMCluster:
    def __init__(self, input_len, grid_size=3, sigma=1.0, learning_rate=0.5):
        self.grid_size = grid_size
        self.sigma = sigma
        self.learning_rate = learning_rate
        self.input_len = input_len
        self._init_weights()
        
    def _init_weights(self):
        """Initialize the weight vectors of the SOM randomly"""
        self.weights = rnd.rand(self.grid_size, self.grid_size, self.input_len)
        
    def _neighborhood(self, c, sigma):
        """Returns a matrix of distances from a center position."""
        d = 2*sigma*sigma
        ax = np.arange(self.grid_size)
        xx, yy = np.meshgrid(ax, ax)
        return np.exp(-((xx-c[0])**2 + (yy-c[1])**2) / d)

    def find_winner(self, x):
        """Find the winner neuron for a given input vector x"""
        diff = self.weights - x
        dist = np.sum(diff**2, axis=-1)
        return np.unravel_index(np.argmin(dist), dist.shape)
    
    def train(self, data, epochs=1000):
        """Train the SOM on the input data"""
        for epoch in range(epochs):
            sigma = self.sigma * (1 - epoch/epochs)
            lr = self.learning_rate * (1 - epoch/epochs)
            
            for x in data:
                winner = self.find_winner(x)
                # Get neighborhood
                g = self._neighborhood(winner, sigma)
                # Update weights
                for i in range(self.grid_size):
                    for j in range(self.grid_size):
                        self.weights[i,j] += lr * g[i,j] * (x - self.weights[i,j])

    def get_cluster(self, x):
        """Get the cluster number for an input vector"""
        winner = self.find_winner(x)
        return winner[0] * self.grid_size + winner[1]

class StaffTransportOptimizer:
    def __init__(self, google_maps_key):
        self.office_location = {
            'lat': 5.582636441579255,
            'lon': -0.143551646497661
        }
        self.MAX_PASSENGERS = 4
        self.MIN_PASSENGERS = 3
        self.COST_PER_KM = 2.5
        self.scaler = MinMaxScaler()
        self.gmaps = googlemaps.Client(key=google_maps_key)
    def load_sample_data(self):
        """Load sample staff location data for Accra region"""
        return pd.DataFrame({
            'staff_id': range(1, 21),
            'name': [f'Employee {i}' for i in range(1, 21)],
            'latitude': np.random.uniform(5.5526, 5.6126, 20),
            'longitude': np.random.uniform(-0.1735, -0.1135, 20),
            'address': [
                'Adabraka', 'Osu', 'Cantonments', 'Airport Residential',
                'East Legon', 'Spintex', 'Tema', 'Teshie', 'Labadi',
                'Labone', 'Ridge', 'Roman Ridge', 'Dzorwulu', 'Abelemkpe',
                'North Kaneshie', 'Dansoman', 'Mamprobi', 'Chorkor',
                'Abeka', 'Achimota'
            ]
        })

    def create_clusters(self, staff_data, grid_size=3, sigma=1.0, learning_rate=0.5):
        """Create clusters based on staff locations using custom SOM implementation"""
        if staff_data is None or len(staff_data) == 0:
            return None
        
        try:
            # Prepare data for SOM
            locations = staff_data[['latitude', 'longitude']].values
            normalized_locations = self.scaler.fit_transform(locations)
            
            # Initialize and train SOM
            som = SOMCluster(
                input_len=2,
                grid_size=grid_size,
                sigma=sigma,
                learning_rate=learning_rate
            )
            
            # Train the SOM
            som.train(normalized_locations)
            
            # Assign clusters
            staff_data['cluster'] = -1
            for i, location in enumerate(normalized_locations):
                cluster = som.get_cluster(location)
                staff_data.iloc[i, staff_data.columns.get_loc('cluster')] = cluster
            
            # Handle small clusters
            self._handle_small_clusters(staff_data)
            
            return staff_data
            
        except Exception as e:
            st.error(f"Error in clustering: {str(e)}")
            return staff_data

    def _handle_small_clusters(self, staff_data):
        """Handle clusters with fewer than minimum required passengers"""
        cluster_sizes = staff_data['cluster'].value_counts()
        small_clusters = cluster_sizes[cluster_sizes < self.MIN_PASSENGERS].index
        
        if len(small_clusters) > 0:
            for small_cluster in small_clusters:
                small_cluster_points = staff_data[staff_data['cluster'] == small_cluster]
                
                for idx, row in small_cluster_points.iterrows():
                    distances = []
                    for cluster_id in staff_data['cluster'].unique():
                        if cluster_id not in small_clusters:
                            cluster_points = staff_data[staff_data['cluster'] == cluster_id]
                            if not cluster_points.empty:
                                avg_dist = cluster_points.apply(
                                    lambda x: geodesic(
                                        (row['latitude'], row['longitude']),
                                        (x['latitude'], x['longitude'])
                                    ).km,
                                    axis=1
                                ).mean()
                                distances.append((cluster_id, avg_dist))
                    
                    if distances:
                        nearest_cluster = min(distances, key=lambda x: x[1])[0]
                        staff_data.at[idx, 'cluster'] = nearest_cluster

    def optimize_routes(self, staff_data):
        """Optimize routes within each SOM cluster"""
        routes = defaultdict(list)
        route_counter = 0
        
        try:
            # Calculate distances to office for all staff
            staff_data['distance_to_office'] = staff_data.apply(
                lambda row: geodesic(
                    (row['latitude'], row['longitude']),
                    (self.office_location['lat'], self.office_location['lon'])
                ).km,
                axis=1
            )
            
            for cluster_id in staff_data['cluster'].unique():
                cluster_group = staff_data[staff_data['cluster'] == cluster_id].copy()
                
                while len(cluster_group) >= self.MIN_PASSENGERS:
                    current_route = []
                    remaining = cluster_group.copy()
                    
                    # Start with furthest person from office in cluster
                    start_person = remaining.nlargest(1, 'distance_to_office').iloc[0]
                    current_route.append(start_person.to_dict())
                    remaining = remaining.drop(start_person.name)
                    
                    # Build route using nearest neighbor approach
                    while len(current_route) < self.MAX_PASSENGERS and not remaining.empty:
                        last_point = current_route[-1]
                        
                        # Calculate distances to remaining points
                        remaining['temp_distance'] = remaining.apply(
                            lambda row: geodesic(
                                (last_point['latitude'], last_point['longitude']),
                                (row['latitude'], row['longitude'])
                            ).km,
                            axis=1
                        )
                        
                        next_person = remaining.nsmallest(1, 'temp_distance').iloc[0]
                        current_route.append(next_person.to_dict())
                        remaining = remaining.drop(next_person.name)
                        
                        if len(current_route) >= self.MIN_PASSENGERS:
                            break
                    
                    if len(current_route) >= self.MIN_PASSENGERS:
                        route_name = f'Route {route_counter + 1}'
                        routes[route_name] = current_route
                        route_counter += 1
                        # Remove assigned staff from cluster group
                        assigned_ids = [p['staff_id'] for p in current_route]
                        cluster_group = cluster_group[~cluster_group['staff_id'].isin(assigned_ids)]
                    else:
                        break
                
                # Handle remaining staff
                if len(cluster_group) > 0:
                    self._assign_remaining_staff(cluster_group, routes)
            
            return routes
            
        except Exception as e:
            st.error(f"Error in route optimization: {str(e)}")
            return {}

    def _assign_remaining_staff(self, remaining_staff, routes):
        """Assign remaining staff to existing routes"""
        for _, row in remaining_staff.iterrows():
            best_route = None
            min_detour = float('inf')
            
            for route_name, route_group in routes.items():
                if len(route_group) < self.MAX_PASSENGERS:
                    # Calculate potential detour
                    current_distance = self.calculate_route_metrics(route_group)[0]
                    test_route = route_group + [row.to_dict()]
                    new_distance = self.calculate_route_metrics(test_route)[0]
                    detour = new_distance - current_distance
                    
                    if detour < min_detour:
                        min_detour = detour
                        best_route = route_name
            
            if best_route:
                routes[best_route].append(row.to_dict())

    def calculate_route_metrics(self, route):
        """Calculate total distance and cost for a route"""
        if not route:
            return 0, 0
            
        total_distance = 0
        points = [(p['latitude'], p['longitude']) for p in route]
        points.append((self.office_location['lat'], self.office_location['lon']))
        
        for i in range(len(points) - 1):
            distance = geodesic(points[i], points[i + 1]).km
            total_distance += distance
            
        return total_distance, total_distance * self.COST_PER_KM

    def get_route_directions(self, origin, destination, waypoints=None):
        """Get route directions using Google Maps Directions API"""
        try:
            if waypoints:
                waypoints = [f"{point['lat']},{point['lng']}" for point in waypoints]
                directions = self.gmaps.directions(
                    origin,
                    destination,
                    waypoints=waypoints,
                    optimize_waypoints=True,
                    mode="driving",
                    departure_time=datetime.now()
                )
            else:
                directions = self.gmaps.directions(
                    origin,
                    destination,
                    mode="driving",
                    departure_time=datetime.now()
                )

            if directions:
                route = directions[0]
                # Extract encoded polyline
                route_polyline = route['overview_polyline']['points']
                # Get duration and distance
                duration = sum(leg['duration']['value'] for leg in route['legs'])
                distance = sum(leg['distance']['value'] for leg in route['legs'])
                
                return {
                    'polyline': route_polyline,
                    'duration': duration,  # in seconds
                    'distance': distance,  # in meters
                    'directions': directions
                }
            return None
        except Exception as e:
            st.error(f"Error getting directions: {str(e)}")
            return None

    def create_map(self, routes):
        """Create an interactive map with optimized route visualization using Google Maps data"""
        try:
            m = folium.Map(
                location=[self.office_location['lat'], self.office_location['lon']],
                zoom_start=13,
                tiles="cartodbpositron"
            )
            
            # Add office marker
            folium.Marker(
                [self.office_location['lat'], self.office_location['lon']],
                popup='Office',
                icon=folium.Icon(color='red', icon='building', prefix='fa'),
                tooltip="Office Location"
            ).add_to(m)
            
            colors = ['blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue']
            
            for route_idx, (route_name, group) in enumerate(routes.items()):
                color = colors[route_idx % len(colors)]
                route_group = folium.FeatureGroup(name=route_name)
                
                # Prepare waypoints for Google Maps
                waypoints = [{'lat': staff['latitude'], 'lng': staff['longitude']} for staff in group]
                
                # Get route from Google Maps
                route_data = self.get_route_directions(
                    f"{waypoints[0]['lat']},{waypoints[0]['lng']}",
                    f"{self.office_location['lat']},{self.office_location['lon']}",
                    waypoints[1:] if len(waypoints) > 1 else None
                )
                
                if route_data:
                    # Decode polyline and add to map
                    route_coords = polyline.decode(route_data['polyline'])
                    
                    folium.PolyLine(
                        route_coords,
                        weight=2,
                        color=color,
                        opacity=0.8,
                        popup=f"{route_name}<br>Distance: {route_data['distance']/1000:.2f} km<br>"
                              f"Duration: {route_data['duration']/60:.0f} min"
                    ).add_to(route_group)
                    
                    # Add markers for each stop
                    for idx, staff in enumerate(group, 1):
                        folium.CircleMarker(
                            [staff['latitude'], staff['longitude']],
                            radius=6,
                            popup=f"{staff['name']}<br>{staff['address']}<br>Stop #{idx}",
                            color=color,
                            fill=True,
                            tooltip=f"Stop #{idx}: {staff['name']}"
                        ).add_to(route_group)
                
                route_group.add_to(m)
            
            folium.LayerControl().add_to(m)
            return m
            
        except Exception as e:
            st.error(f"Error creating map: {str(e)}")
            return None
def main():
    st.title("Staff Transportation Optimizer")
    
    # Initialize optimizer
    optimizer = StaffTransportOptimizer(google_maps_key="AIzaSyC8Vzow3LdOOKZByIetQ4LV-vQEuSQk9Mc")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Data Input")
        data_option = st.radio(
            "Choose data input method",
            ["Upload CSV", "Use Sample Data"]
        )
        
        if data_option == "Upload CSV":
            uploaded_file = st.file_uploader(
                "Upload staff locations CSV",
                type=["csv"]
            )
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    required_columns = ['staff_id', 'name', 'latitude', 'longitude', 'address']
                    if all(col in df.columns for col in required_columns):
                        st.session_state.staff_data = df
                        st.success("Data uploaded successfully!")
                    else:
                        st.error("CSV must contain: staff_id, name, latitude, longitude, address")
                except Exception as e:
                    st.error(f"Error reading CSV: {str(e)}")
        else:
            if st.button("Load Sample Data"):
                st.session_state.staff_data = optimizer.load_sample_data()
                st.success("Sample data loaded successfully!")
        
        st.header("Optimization Parameters")
        grid_size = st.slider("Grid size", 2, 5, 3, 1)
        sigma = st.slider("Neighborhood radius", 0.5, 2.0, 1.0, 0.1)
        learning_rate = st.slider("Learning rate", 0.1, 1.0, 0.5, 0.1)
        
        if st.button("Optimize Routes", type="primary"):
            if 'staff_data' in st.session_state and st.session_state.staff_data is not None:
                with st.spinner("Optimizing routes..."):
                    # Clean and validate data
                    clean_data = st.session_state.staff_data.copy()
                    clean_data['latitude'] = pd.to_numeric(clean_data['latitude'], errors='coerce')
                    clean_data['longitude'] = pd.to_numeric(clean_data['longitude'], errors='coerce')
                    
                    # Remove any invalid coordinates
                    clean_data = clean_data.dropna(subset=['latitude', 'longitude'])
                    
                    if len(clean_data) < optimizer.MIN_PASSENGERS:
                        st.error(f"Need at least {optimizer.MIN_PASSENGERS} valid staff locations")
                        return
                    
                    clustered_data = optimizer.create_clusters(
                        clean_data,
                        grid_size=grid_size,
                        sigma=sigma,
                        learning_rate=learning_rate
                    )
                    
                    if clustered_data is not None:
                        st.session_state.routes = optimizer.optimize_routes(clustered_data)
                        if st.session_state.routes:
                            st.session_state.optimization_done = True
                            st.success("Routes optimized successfully!")
                        else:
                            st.error("Route optimization failed. Please try different parameters.")
                    else:
                        st.error("Clustering failed. Please try different parameters.")
            else:
                st.warning("Please load or upload data first.")
    
    # Display results
    if 'staff_data' in st.session_state and st.session_state.staff_data is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if 'optimization_done' in st.session_state and st.session_state.optimization_done:
                st.subheader("Route Map")
                m = optimizer.create_map(st.session_state.routes)
                if m is not None:
                    st_folium(m, width=800, height=600)
        
        with col2:
            st.subheader("Staff Data")
            display_df = st.session_state.staff_data[['name', 'address']].copy()
            st.dataframe(display_df, height=300)
            
            if 'optimization_done' in st.session_state and st.session_state.optimization_done:
                st.subheader("Route Details")
                total_cost = 0
                total_distance = 0
                
                for route_name, route in st.session_state.routes.items():
                    with st.expander(route_name):
                        route_df = pd.DataFrame(route)
                        distance, cost = optimizer.calculate_route_metrics(route)
                        total_distance += distance
                        total_cost += cost
                        
                        st.write(f"Distance: {distance:.2f} km")
                        st.write(f"Cost: ${cost:.2f}")
                        st.dataframe(
                            route_df[['name', 'address', 'distance_to_office']],
                            height=200
                        )
                
                # Show total metrics
                st.subheader("Total Metrics")
                st.write(f"Total Distance: {total_distance:.2f} km")
                st.write(f"Total Cost: ${total_cost:.2f}")
                st.write(f"Number of Routes: {len(st.session_state.routes)}")
                st.write(f"Average Cost per Route: ${(total_cost/len(st.session_state.routes)):.2f}")

if __name__ == "__main__":
    main()