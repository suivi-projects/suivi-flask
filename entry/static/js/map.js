document.addEventListener('DOMContentLoaded', function() {
    function initMap() {
        const mapElement = document.getElementById('map');
        const mapDataElement = document.getElementById('map-data');

        const pickupLocation = mapDataElement.dataset.pickupLocation;
        const deliveryLocation = mapDataElement.dataset.deliveryLocation;
        const riderId = mapDataElement.dataset.riderId;
        const pickupLat = parseFloat(mapDataElement.dataset.pickupLat);
        const pickupLng = parseFloat(mapDataElement.dataset.pickupLng);
        const deliveryLat = parseFloat(mapDataElement.dataset.deliveryLat);
        const deliveryLng = parseFloat(mapDataElement.dataset.deliveryLng);

        const map = L.map('map').setView([-1.286389, 36.817223], 13);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);

        if (pickupLocation && deliveryLocation) {
            fetch('/get_coordinates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    pickup_location: pickupLocation,
                    delivery_location: deliveryLocation
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    return;
                }

                const pickupLatLng = [data.pickup_lat, data.pickup_lng];
                const deliveryLatLng = [data.delivery_lat, data.delivery_lng];

                L.marker(pickupLatLng).addTo(map)
                    .bindPopup("Pickup Location")
                    .openPopup();
                L.circle(pickupLatLng, { radius: 100 }).addTo(map);

                L.marker(deliveryLatLng).addTo(map)
                    .bindPopup("Delivery Location")
                    .openPopup();
                L.circle(deliveryLatLng, { radius: 100 }).addTo(map);

                L.Routing.control({
                    waypoints: [
                        L.latLng(pickupLatLng),
                        L.latLng(deliveryLatLng)
                    ],
                    routeWhileDragging: true,
                    createMarker: function() { return null; }
                }).addTo(map);

                map.fitBounds(L.latLngBounds(pickupLatLng, deliveryLatLng));
            })
            .catch(error => console.error('Error fetching coordinates:', error));
        }

        if (navigator.geolocation) {
            navigator.geolocation.watchPosition(success, error);
        } else {
            alert("Geolocation is not supported by your browser.");
        }

        let riderMarker, riderCircle;
        let riderToPickupRoute;

        function success(pos) {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;
            const accuracy = pos.coords.accuracy;

            if (riderMarker) {
                map.removeLayer(riderMarker);
                map.removeLayer(riderCircle);
                if (riderToPickupRoute) {
                    map.removeControl(riderToPickupRoute);
                }
            }

            riderMarker = L.marker([lat, lng]).addTo(map).bindPopup("Rider's Location");
            riderCircle = L.circle([lat, lng], { radius: accuracy });
            riderMarker.addTo(map);
            riderCircle.addTo(map);
            map.setView([lat, lng], 13);

            fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`)
                .then(response => response.json())
                .then(data => {
                    const locationName = data.display_name;
                    console.log("Current location name:", locationName);
                    updateRiderLocation(locationName);
                })
                .catch(error => console.error('Error in reverse geocoding:', error));

            if (pickupLat && pickupLng) {
                riderToPickupRoute = L.Routing.control({
                    waypoints: [
                        L.latLng([lat, lng]),
                        L.latLng([pickupLat, pickupLng])
                    ],
                    routeWhileDragging: true,
                    createMarker: function() { return null; }
                }).addTo(map);
            }
        }

        function error(err) {
            if (err.code === 1) {
                alert("Please allow geolocation access");
            } else {
                alert("Cannot get current location");
            }
        }

        function updateRiderLocation(locationName) {
            fetch('/update_location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    rider_id: riderId,
                    current_location: locationName
                })
            })
            .then(response => response.json())
            .then(data => console.log('Location update response:', data))
            .catch(error => console.error('Error updating location:', error));
        }
    }

    initMap();
});