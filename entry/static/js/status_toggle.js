document.addEventListener('DOMContentLoaded', function() {
    const checkbox = document.getElementById('checkbox');
    const availabilityText = document.getElementById('availability-text');

    checkbox.addEventListener('change', function() {
        if (checkbox.checked) {
            availabilityText.textContent = 'Available';
            toggleRiderStatus(true);
        } else {
            availabilityText.textContent = 'Unavailable';
            toggleRiderStatus(false);
        }
    });

    async function toggleRiderStatus(isAvailable) {
        try {
            const response = await fetch(`/toggle_rider_status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    available: isAvailable
                })
            });
            const data = await response.json();
            console.log(data);
        } catch (error) {
            console.error('Error:', error);
        }
    }
});