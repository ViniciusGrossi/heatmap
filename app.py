import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from datetime import datetime, time, timedelta
from streamlit_folium import folium_static

# Page configuration
st.set_page_config(page_title="Ride Heatmap", layout="wide")

# Title and description
st.title("Ride Analysis by Time and Location")
st.markdown("""
Heatmap showing:
- 🔵 Pickup locations (blue)
- 🔴 Drop-off locations (red)
Intensity of colors varies based on the ride time
""")

# Function to parse times with various formats
def parse_time(time_str):
    try:
        # Remove timezone information
        time_part = str(time_str).split('(')[0].strip()
        # Add a leading zero if hour has one digit
        if len(time_part.split(':')[0]) == 1:
            time_part = '0' + time_part
        return datetime.strptime(time_part, '%H:%M:%S').time()
    except:
        return None

# Read and process the Excel file
try:
    df = pd.read_excel(
        'Data.xlsx',
        sheet_name='Sheet1',
        skiprows=3,  # Skip metadata rows
        usecols='A,D,E',  # Select columns: Time, Pickup coords, Drop-off coords
        names=['Time', 'Pickup', 'Dropoff']
    )
except Exception as e:
    st.error(f"Error reading file: {e}")
    st.stop()

# Time filter for the user (range between 00:00 and 23:59)
start_time, end_time = st.sidebar.slider(
    "Select time range",
    min_value=time(0, 0),
    max_value=time(23, 59),
    value=(time(0, 0), time(23, 59)),
    step=timedelta(minutes=1)
)

# Option to select the type of data to display
data_option = st.sidebar.radio(
    "Select the data you want to visualize:",
    options=["Both", "Only Pickup", "Only Dropoff"]
)

# Option to display pin points (markers)
show_markers = st.sidebar.checkbox("Show pin points", value=True)

# Process coordinates and times based on the selected time range
pickup_data = []
dropoff_data = []

for _, row in df.iterrows():
    time_obj = parse_time(row['Time'])
    if not time_obj:
        continue
    
    # Filter data based on the selected time range
    if not (start_time <= time_obj <= end_time):
        continue
    
    intensity = (time_obj.hour + time_obj.minute/60 + time_obj.second/3600) / 24
    
    # Process Pickup
    if pd.notna(row['Pickup']):
        try:
            lat, lon = map(float, str(row['Pickup']).replace(' ', '').split(','))
            pickup_data.append([lat, lon, intensity])
        except:
            pass
    
    # Process Dropoff
    if pd.notna(row['Dropoff']):
        try:
            lat, lon = map(float, str(row['Dropoff']).replace(' ', '').split(','))
            dropoff_data.append([lat, lon, intensity])
        except:
            pass

# Create the map
m = folium.Map(location=[50.850346, 4.351721], zoom_start=12)

# Add heatmaps and markers based on the user's selection
if data_option in ["Both", "Only Pickup"]:
    # Pickup heatmap
    HeatMap(
        pickup_data,
        radius=15,
        gradient={'0.1': 'blue', '0.5': 'royalblue', '0.9': 'darkblue'},
        blur=15,
        name='Pickup'
    ).add_to(m)
    
    # Add pickup markers only if the option is enabled
    if show_markers:
        for point in pickup_data:
            folium.Marker(
                location=[point[0], point[1]],
                icon=folium.Icon(color='blue', icon='info-sign'),
                popup="Pickup"
            ).add_to(m)

if data_option in ["Both", "Only Dropoff"]:
    # Dropoff heatmap
    HeatMap(
        dropoff_data,
        radius=15,
        gradient={'0.1': 'orange', '0.5': 'red', '0.9': 'darkred'},
        blur=15,
        name='Dropoff'
    ).add_to(m)
    
    # Add dropoff markers only if the option is enabled
    if show_markers:
        for point in dropoff_data:
            folium.Marker(
                location=[point[0], point[1]],
                icon=folium.Icon(color='red', icon='info-sign'),
                popup="Dropoff"
            ).add_to(m)

# Display the map
folium_static(m, width=1200, height=600)

# Legend and instructions
st.markdown("""
**Instructions:**
- Zoom: Mouse scroll or (+/-) buttons
- Move: Drag the map
- Layer control: Icon in the upper right corner
- Darker colors indicate later times
""")
