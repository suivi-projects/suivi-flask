document.addEventListener('DOMContentLoaded', (event) => {
    const mapElement = document.getElementById('map');
    if (mapElement && typeof L !== 'undefined') {
      try {
        var map = L.map('map').setView([-1.286389, 36.817223], 13);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          attribution:
            '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(map);
  
        let marker, circle, zoomed;
  
        function success(pos) {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          const accuracy = pos.coords.accuracy;
          if (!map) return;
          if (marker) map.removeLayer(marker);
          if (circle) map.removeLayer(circle);
          marker = L.marker([lat, lng]).addTo(map);
          circle = L.circle([lat, lng], { radius: accuracy }).addTo(map);
          if (!zoomed) {
            try {
              map.fitBounds(circle.getBounds());
              zoomed = true;
            } catch (e) {
              map.setView([lat, lng], 15);
              zoomed = true;
            }
          }
        }
  
        function error(err) {
          console.error(`Geolocation error (${err.code}): ${err.message}`);
        }
  
        if (navigator.geolocation) {
          navigator.geolocation.watchPosition(success, error, {
            enableHighAccuracy: true, timeout: 10000, maximumAge: 0,
          });
        } else {
          console.warn('Geolocation is not supported by this browser.');
        }
      } catch (mapError) {
        console.error('Failed to initialize Leaflet map:', mapError);
        mapElement.innerHTML = '<p style="color: red;">Error loading map.</p>';
      }
    }
  
    function animateValue(id, start, end, duration) {
      let obj = document.getElementById(id);
      if (!obj) return;
      let startTimestamp = null;
      const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        let currentValue = Math.floor(progress * (end - start) + start);
        if (id === 'satisfaction-rate') {
          obj.textContent = currentValue + '%';
        } else {
          obj.textContent = currentValue;
        }
        if (progress < 1) {
          window.requestAnimationFrame(step);
        }
      };
      window.requestAnimationFrame(step);
    }
  
    animateValue('completed-deliveries', 0, 1247, 2000);
    animateValue('active-orders', 0, 23, 1500);
    animateValue('satisfaction-rate', 0, 98, 2500);
  });
  