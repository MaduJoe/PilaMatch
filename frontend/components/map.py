"""
Map display component
"""

import streamlit as st
import streamlit.components.v1 as components
import os
from utils.constants import SEOUL_REGIONS

# Kakao Map Key
KAKAO_MAP_KEY = os.getenv("KAKAO_MAP_KEY", "")

def render_kakao_map(region, height=300):
    """Render Kakao Map for the selected region."""

    if not KAKAO_MAP_KEY:
        st.info(f"📍 선택된 지역: {region}")
        return

    if region not in SEOUL_REGIONS:
        st.warning(f"'{region}' 지역의 좌표를 찾을 수 없습니다.")
        return

    lat, lng = SEOUL_REGIONS[region]

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            #map {{ width: 100%; height: {height}px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_MAP_KEY}"></script>
        <script>
            var container = document.getElementById('map');
            var options = {{
                center: new kakao.maps.LatLng({lat}, {lng}),
                level: 5
            }};

            var map = new kakao.maps.Map(container, options);

            // 마커 생성
            var markerPosition = new kakao.maps.LatLng({lat}, {lng});
            var marker = new kakao.maps.Marker({{
                position: markerPosition
            }});
            marker.setMap(map);

            // 인포윈도우
            var iwContent = '<div style="padding:5px;">{region}</div>';
            var infowindow = new kakao.maps.InfoWindow({{
                content: iwContent
            }});
            infowindow.open(map, marker);
        </script>
    </body>
    </html>
    """

    components.html(map_html, height=height + 20)