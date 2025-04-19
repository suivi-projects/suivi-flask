document.addEventListener('DOMContentLoaded', function() {
    const mapDataElement = document.getElementById('map-data');
    const assignmentId = mapDataElement ? mapDataElement.dataset.assignmentId : null;
    const assignmentStatus = mapDataElement ? mapDataElement.dataset.assignmentStatus : null;

    const actionButtons = document.getElementById('action-buttons');
    const acceptButton = document.querySelector('.accept-btn');
    const rejectButton = document.querySelector('.reject-btn');
    const pickedUpButton = document.querySelector('.picked-up-btn');
    const deliveredButton = document.querySelector('.delivered-btn');

    function showAcceptRejectButtons() {
        if (acceptButton) acceptButton.style.display = 'inline-block';
        if (rejectButton) rejectButton.style.display = 'inline-block';
        if (pickedUpButton) pickedUpButton.style.display = 'none';
        if (deliveredButton) deliveredButton.style.display = 'none';
        if (actionButtons) actionButtons.style.display = 'block';
    }

    function showPickedUpButton() {
        if (acceptButton) acceptButton.style.display = 'none';
        if (rejectButton) rejectButton.style.display = 'none';
        if (pickedUpButton) pickedUpButton.style.display = 'inline-block';
        if (deliveredButton) deliveredButton.style.display = 'none';
        if (actionButtons) actionButtons.style.display = 'block';
    }

    function showDeliveredButton() {
        if (acceptButton) acceptButton.style.display = 'none';
        if (rejectButton) rejectButton.style.display = 'none';
        if (pickedUpButton) pickedUpButton.style.display = 'none';
        if (deliveredButton) deliveredButton.style.display = 'inline-block';
        if (actionButtons) actionButtons.style.display = 'block';
    }

    function hideAllButtons() {
         if (actionButtons) actionButtons.style.display = 'none';
    }

    async function updateAssignment(action) {
        if (!assignmentId) {
            console.error('Cannot update assignment: ID is missing.');
            alert('Error: Assignment ID not found.');
            return;
        }

        const apiUrl = '/update_assignment';
        actionButtons.querySelectorAll('button').forEach(btn => btn.disabled = true);

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    parcel_id: assignmentId,
                    action: action,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `Request failed: ${response.statusText} (${response.status})`);
            }

            console.log('Update response:', data);

            if (action === 'accept') {
                showPickedUpButton();
            } else if (action === 'shipped') {
                showDeliveredButton();
            } else if (action === 'reject' || action === 'arrived') {
                hideAllButtons();
            }

            location.reload();

        } catch (error) {
            console.error('Fetch Error:', error);
            alert(`Error updating assignment: ${error.message}`);
            actionButtons.querySelectorAll('button').forEach(btn => btn.disabled = false);
        }
    }

    if (actionButtons && assignmentId && assignmentStatus) {
        acceptButton.style.display = 'none';
        rejectButton.style.display = 'none';
        pickedUpButton.style.display = 'none';
        deliveredButton.style.display = 'none';
        actionButtons.style.display = 'none';

        if (assignmentStatus === "allocated") {
            showAcceptRejectButtons();
        } else if (assignmentStatus === "in_progress") {
            showPickedUpButton();
        } else if (assignmentStatus === "shipped") {
            showDeliveredButton();
        }
    } else {
         if(actionButtons) actionButtons.style.display = 'none';
         console.log("No assignment data found or action buttons missing.");
    }

    if (acceptButton) acceptButton.addEventListener('click', () => updateAssignment('accept'));
    if (rejectButton) rejectButton.addEventListener('click', () => updateAssignment('reject'));
    if (pickedUpButton) pickedUpButton.addEventListener('click', () => updateAssignment('shipped'));
    if (deliveredButton) deliveredButton.addEventListener('click', () => updateAssignment('arrived'));

});