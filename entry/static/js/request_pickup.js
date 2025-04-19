document.addEventListener('DOMContentLoaded', function() {
    const parcelForm = document.getElementById('parcelForm');
    const stripePublishableKey = parcelForm ? parcelForm.dataset.stripeKey : null;
    const geocodeUrl = "https://nominatim.openstreetmap.org/search?format=json&q=";
    const reverseGeocodeUrl = "https://nominatim.openstreetmap.org/reverse?format=jsonv2";

    let map, pickupMarker, deliveryMarker, routingControl;
    let pickupCoords = null;
    let deliveryCoords = null;
    let pickupLocationText = '';
    let deliveryLocationText = '';

    const pickupInput = document.getElementById('pickup_location');
    const deliveryInput = document.getElementById('delivery_location');
    const currentLocationBtn = document.getElementById('currentLocationBtn');
    const confirmLocationsBtn = document.getElementById('confirmLocationsBtn');
    const editLocationsBtn = document.getElementById('editLocationsBtn');
    const proceedToReceiverBtn = document.getElementById('proceedToReceiverBtn');
    const backToRouteBtn = document.getElementById('backToRouteBtn');
    const proceedToPaymentBtn = document.getElementById('proceedToPaymentBtn');
    const backToReceiverBtn = document.getElementById('backToReceiverBtn');
    const finalPayButton = document.getElementById('final-pay-button');

    const stepLocationsDiv = document.getElementById('step-locations');
    const stepRouteConfirmDiv = document.getElementById('step-route-confirm');
    const stepReceiverDiv = document.getElementById('step-receiver');
    const stepPaymentDiv = document.getElementById('step-payment');
    const stepThankYouDiv = document.getElementById('step-thank-you');
    const allSteps = [stepLocationsDiv, stepRouteConfirmDiv, stepReceiverDiv, stepPaymentDiv, stepThankYouDiv];

    const pickupErrorDiv = document.getElementById('pickup-error');
    const deliveryErrorDiv = document.getElementById('delivery-error');
    const routeInfoDiv = document.getElementById('route-info');


    const mpesaPhoneGroup = document.getElementById('mpesa-phone-group');
    const mpesaPhoneInput = document.getElementById('mpesa_phone');
    const mpesaPhoneError = document.getElementById('mpesa-phone-error');
    const paymentMethodRadios = document.querySelectorAll('input[name="payment_method"]');
    const receiverNameInput = document.getElementById('receiver_name');
    const receiverContactInput = document.getElementById('receiver_contact');

    let stripeHandler = null;

    function initMap() {
        if (document.getElementById('map')) {
            map = L.map('map').setView([-1.286389, 36.817223], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }).addTo(map);

            pickupMarker = L.marker(map.getCenter(), { draggable: true, autoPan: true }).addTo(map).bindPopup("Pickup Location (Drag Me)");
            deliveryMarker = L.marker(map.getCenter(), { draggable: true, autoPan: true }).addTo(map).bindPopup("Delivery Location (Drag Me)");

            pickupMarker.on('dragend', (e) => {
                updateLocationFromMarker(e.target.getLatLng(), 'pickup');
                saveState();
            });
            deliveryMarker.on('dragend', (e) => {
                updateLocationFromMarker(e.target.getLatLng(), 'delivery');
                saveState();
            });
        } else {
            console.error("Map container not found");
        }
    }

    function updateLocationFromMarker(latlng, type) {
        const url = `${reverseGeocodeUrl}&lat=${latlng.lat}&lon=${latlng.lng}`;
        const inputElement = (type === 'pickup') ? pickupInput : deliveryInput;
        const errorDiv = (type === 'pickup') ? pickupErrorDiv : deliveryErrorDiv;
        const otherInputElement = (type === 'pickup') ? deliveryInput : pickupInput;
        const otherErrorDiv = (type === 'pickup') ? deliveryErrorDiv : pickupErrorDiv;
        const otherCoords = (type === 'pickup') ? deliveryCoords : pickupCoords;

        fetch(url)
            .then(response => response.ok ? response.json() : Promise.reject('Network response was not ok.'))
            .then(data => {
                if (data && data.display_name) {
                    const address = data.display_name;
                    inputElement.value = address;
                    if (type === 'pickup') {
                        pickupCoords = latlng;
                        pickupLocationText = address;
                    } else {
                        deliveryCoords = latlng;
                        deliveryLocationText = address;
                    }
                    validateLocationInput(inputElement, errorDiv, (type === 'pickup' ? pickupCoords : deliveryCoords));
                    validateLocationInput(otherInputElement, otherErrorDiv, otherCoords);
                    checkLocationsConfirmed();
                } else {
                    if (type === 'pickup') pickupCoords = null; else deliveryCoords = null;
                    validateLocationInput(inputElement, errorDiv, null, "Could not determine address from map pin.");
                    validateLocationInput(otherInputElement, otherErrorDiv, otherCoords);
                    checkLocationsConfirmed();
                }
            })
            .catch(error => {
                 console.error('Reverse Geocoding Error:', error);
                 if (type === 'pickup') pickupCoords = null; else deliveryCoords = null;
                 validateLocationInput(inputElement, errorDiv, null, "Error finding address.");
                 validateLocationInput(otherInputElement, otherErrorDiv, otherCoords);
                 checkLocationsConfirmed();
            });
    }

    function geocodeAddress(address, type) {
        const inputElement = (type === 'pickup') ? pickupInput : deliveryInput;
        const errorDiv = (type === 'pickup') ? pickupErrorDiv : deliveryErrorDiv;
        const marker = (type === 'pickup') ? pickupMarker : deliveryMarker;
        const otherInputElement = (type === 'pickup') ? deliveryInput : pickupInput;
        const otherErrorDiv = (type === 'pickup') ? deliveryErrorDiv : pickupErrorDiv;
        const otherCoords = (type === 'pickup') ? deliveryCoords : pickupCoords;

        if (!address || address.length < 3) {
             if (type === 'pickup') { pickupCoords = null; validateLocationInput(inputElement, errorDiv, null); }
             else { deliveryCoords = null; validateLocationInput(inputElement, errorDiv, null); }
             validateLocationInput(otherInputElement, otherErrorDiv, otherCoords);
             checkLocationsConfirmed();
             return;
        }

        const url = `${geocodeUrl}${encodeURIComponent(address)}`;

        fetch(url)
            .then(response => response.ok ? response.json() : Promise.reject('Network response was not ok.'))
            .then(data => {
                if (data && data.length > 0) {
                    const bestResult = data[0];
                    const latlng = L.latLng(bestResult.lat, bestResult.lon);
                    if (marker) marker.setLatLng(latlng);
                    if (type === 'pickup') {
                        pickupCoords = latlng;
                        pickupLocationText = inputElement.value;
                    } else {
                        deliveryCoords = latlng;
                        deliveryLocationText = inputElement.value;
                    }
                    validateLocationInput(inputElement, errorDiv, (type === 'pickup' ? pickupCoords : deliveryCoords));
                    validateLocationInput(otherInputElement, otherErrorDiv, otherCoords);

                    if (map) {
                        if (pickupCoords && deliveryCoords) {
                            map.fitBounds(L.latLngBounds(pickupCoords, deliveryCoords), { padding: [50, 50] });
                        } else {
                            map.setView(latlng, 15);
                        }
                    }
                    checkLocationsConfirmed();
                } else {
                    if (type === 'pickup') pickupCoords = null; else deliveryCoords = null;
                    validateLocationInput(inputElement, errorDiv, null, "Address not found.");
                    validateLocationInput(otherInputElement, otherErrorDiv, otherCoords);
                    checkLocationsConfirmed();
                }
            })
            .catch(error => {
                console.error('Geocoding Error:', error);
                if (type === 'pickup') pickupCoords = null; else deliveryCoords = null;
                validateLocationInput(inputElement, errorDiv, null, "Geocoding error.");
                validateLocationInput(otherInputElement, otherErrorDiv, otherCoords);
                checkLocationsConfirmed();
            });
    }

    function validateLocationInput(inputElement, errorDiv, coords, customError = null) {
         if (!inputElement || !errorDiv) return false;
         inputElement.classList.remove('is-valid', 'is-invalid');
         errorDiv.textContent = '';
         if (customError) {
             inputElement.classList.add('is-invalid');
             errorDiv.textContent = customError;
             return false;
         } else if (coords && inputElement.value.trim() !== '') {
             inputElement.classList.add('is-valid');
             return true;
         } else if (inputElement.value.trim() !== '') {
             inputElement.classList.add('is-invalid');
             errorDiv.textContent = 'Address could not be verified.';
             return false;
         }
         return false;
    }

    function checkLocationsConfirmed() {
        if (!pickupInput || !deliveryInput || !confirmLocationsBtn) return;
        const pickupValid = pickupCoords && pickupInput.classList.contains('is-valid');
        const deliveryValid = deliveryCoords && deliveryInput.classList.contains('is-valid');
        confirmLocationsBtn.disabled = !(pickupValid && deliveryValid);
    }

    function showStep(stepToShow) {
        allSteps.forEach(step => {
            if (step) step.style.display = (step === stepToShow) ? 'block' : 'none';
        });
        if (map) {
            setTimeout(() => {
                map.invalidateSize();
                if (stepToShow === stepRouteConfirmDiv && pickupCoords && deliveryCoords) {
                    map.fitBounds(L.latLngBounds(pickupCoords, deliveryCoords), { padding: [50, 50] });
                } else if (stepToShow === stepLocationsDiv && pickupCoords && deliveryCoords) {
                    map.fitBounds(L.latLngBounds(pickupCoords, deliveryCoords), { padding: [50, 50] });
                } else if (stepToShow === stepLocationsDiv && (pickupCoords || deliveryCoords)) {
                    map.setView(pickupCoords || deliveryCoords || map.getCenter(), 15);
                } else if (stepToShow === stepLocationsDiv) {
                    map.setView([-1.286389, 36.817223], 13);
                }
            }, 50);
        }
    }

    function drawRoute() {
        if (!map) return;
        if (routingControl) {
            map.removeControl(routingControl);
            routingControl = null;
        }
        if (!pickupCoords || !deliveryCoords) return;

        if (routeInfoDiv) routeInfoDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>Calculating route...';

        routingControl = L.Routing.control({
            waypoints: [pickupCoords, deliveryCoords],
            routeWhileDragging: false,
            addWaypoints: false,
            draggableWaypoints: false,
            lineOptions: { styles: [{ color: '#1abc9c', opacity: 0.8, weight: 6 }] },
            createMarker: () => null,
            show: false,
            router: L.Routing.osrmv1({ serviceUrl: 'https://router.project-osrm.org/route/v1' })
        })
        .on('routesfound', function(e) {
            if (!routeInfoDiv) return;
            var routes = e.routes;
            if (!routes || routes.length === 0) {
                routeInfoDiv.innerHTML = `<span class="text-danger">No route found.</span>`;
                return;
            }
            var summary = routes[0].summary;
            routeInfoDiv.innerHTML = `Estimated Route: <strong>${(summary.totalDistance / 1000).toFixed(1)} km</strong>, approx. <strong>${Math.round(summary.totalTime / 60)} mins</strong>.`;

            setTimeout(() => {
                 if (map && e.routes[0]) {
                    map.invalidateSize();
                    map.fitBounds(e.routes[0].coordinates.map(c => [c.lat, c.lng]), { padding: [50, 50] });
                 }
            }, 100);
        })
        .on('routingerror', function(e) {
             if (routeInfoDiv) routeInfoDiv.innerHTML = `<span class="text-danger">Could not calculate route. ${e.error?.message || 'Check locations.'}</span>`;
             console.error("Routing Error:", e.error);
        })
        .addTo(map);
    }

     function updateReviewDetails() {
         if (document.getElementById('review-pickup')) document.getElementById('review-pickup').textContent = pickupInput.value;
         if (document.getElementById('review-delivery')) document.getElementById('review-delivery').textContent = deliveryInput.value;
         if (document.getElementById('review-receiver-name')) document.getElementById('review-receiver-name').textContent = receiverNameInput.value;
         if (document.getElementById('review-receiver-contact')) document.getElementById('review-receiver-contact').textContent = receiverContactInput.value;
     }

    function saveState() {
        const state = {
            currentStepId: getCurrentStepId(),
            pickupLocation: pickupInput ? pickupInput.value : '',
            deliveryLocation: deliveryInput ? deliveryInput.value : '',
            pickupCoords: pickupCoords ? { lat: pickupCoords.lat, lng: pickupCoords.lng } : null,
            deliveryCoords: deliveryCoords ? { lat: deliveryCoords.lat, lng: deliveryCoords.lng } : null,
            pickupLocationText: pickupLocationText,
            deliveryLocationText: deliveryLocationText,
            receiverName: receiverNameInput ? receiverNameInput.value : '',
            receiverContact: receiverContactInput ? receiverContactInput.value : '',
            paymentMethod: document.querySelector('input[name="payment_method"]:checked') ? document.querySelector('input[name="payment_method"]:checked').value : 'stripe',
            mpesaPhone: mpesaPhoneInput ? mpesaPhoneInput.value : ''
        };
        sessionStorage.setItem('pickupRequestState', JSON.stringify(state));
    }

    function loadState() {
        const savedState = sessionStorage.getItem('pickupRequestState');
        if (savedState) {
            const state = JSON.parse(savedState);

            if (pickupInput) pickupInput.value = state.pickupLocation || '';
            if (deliveryInput) deliveryInput.value = state.deliveryLocation || '';
            pickupLocationText = state.pickupLocationText || '';
            deliveryLocationText = state.deliveryLocationText || '';
            if (receiverNameInput) receiverNameInput.value = state.receiverName || '';
            if (receiverContactInput) receiverContactInput.value = state.receiverContact || '';
            if (mpesaPhoneInput) mpesaPhoneInput.value = state.mpesaPhone || '';

            if (state.pickupCoords) {
                pickupCoords = L.latLng(state.pickupCoords.lat, state.pickupCoords.lng);
                if(pickupMarker) pickupMarker.setLatLng(pickupCoords);
            }
            if (state.deliveryCoords) {
                deliveryCoords = L.latLng(state.deliveryCoords.lat, state.deliveryCoords.lng);
                 if(deliveryMarker) deliveryMarker.setLatLng(deliveryCoords);
            }

            const paymentMethod = state.paymentMethod || 'stripe';
            const radioToCheck = document.getElementById(`pay_${paymentMethod}`);
            if (radioToCheck) {
                radioToCheck.checked = true;
                const event = new Event('change');
                radioToCheck.dispatchEvent(event);
            }

            validateLocationInput(pickupInput, pickupErrorDiv, pickupCoords);
            validateLocationInput(deliveryInput, deliveryErrorDiv, deliveryCoords);
            checkLocationsConfirmed();

            const stepId = state.currentStepId || 'step-locations';
            const stepToShow = document.getElementById(stepId);

            if (stepToShow) {
                showStep(stepToShow);
                if (stepId === 'step-route-confirm' && pickupCoords && deliveryCoords) {
                    drawRoute();
                }
                 if (stepId === 'step-payment') {
                    updateReviewDetails();
                 }
            } else {
                showStep(stepLocationsDiv);
            }
        } else {
            showStep(stepLocationsDiv);
        }
    }

    function getCurrentStepId() {
        for (const step of allSteps) {
            if (step && step.style.display !== 'none') {
                return step.id;
            }
        }
        return 'step-locations';
    }


    if (currentLocationBtn) {
        currentLocationBtn.addEventListener('click', function() {
            currentLocationBtn.disabled = true;
            currentLocationBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Locating...';
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(position => {
                    const latlng = L.latLng(position.coords.latitude, position.coords.longitude);
                    if (pickupMarker) pickupMarker.setLatLng(latlng);
                    if (map) map.setView(latlng, 15);
                    updateLocationFromMarker(latlng, 'pickup');
                    saveState();
                    currentLocationBtn.disabled = false;
                    currentLocationBtn.innerHTML = '<i class="fas fa-location-crosshairs me-1"></i> Use Current Location';
                }, error => {
                    console.error("Geolocation error:", error);
                    alert("Could not get current location. Please ensure location services are enabled and permissions granted.");
                    validateLocationInput(pickupInput, pickupErrorDiv, null, "Could not get current location.");
                    currentLocationBtn.disabled = false;
                    currentLocationBtn.innerHTML = '<i class="fas fa-location-crosshairs me-1"></i> Use Current Location';
                }, { timeout: 10000 });
            } else {
                alert("Geolocation is not supported by this browser.");
                 validateLocationInput(pickupInput, pickupErrorDiv, null, "Geolocation not supported.");
                 currentLocationBtn.disabled = false;
                 currentLocationBtn.innerHTML = '<i class="fas fa-location-crosshairs me-1"></i> Use Current Location';
            }
        });
    }

    if (pickupInput) {
        pickupInput.addEventListener('blur', () => {
            if (pickupInput.value.trim() !== pickupLocationText) {
                 geocodeAddress(pickupInput.value, 'pickup');
            } else if (pickupInput.value.trim() === '') {
                pickupCoords = null;
                validateLocationInput(pickupInput, pickupErrorDiv, null);
                validateLocationInput(deliveryInput, deliveryErrorDiv, deliveryCoords);
                checkLocationsConfirmed();
            } else {
                validateLocationInput(pickupInput, pickupErrorDiv, pickupCoords);
                validateLocationInput(deliveryInput, deliveryErrorDiv, deliveryCoords);
                checkLocationsConfirmed();
            }
            saveState();
        });
    }

    if (deliveryInput) {
        deliveryInput.addEventListener('blur', () => {
             if (deliveryInput.value.trim() !== deliveryLocationText) {
                geocodeAddress(deliveryInput.value, 'delivery');
             } else if (deliveryInput.value.trim() === '') {
                deliveryCoords = null;
                validateLocationInput(deliveryInput, deliveryErrorDiv, null);
                validateLocationInput(pickupInput, pickupErrorDiv, pickupCoords);
                checkLocationsConfirmed();
             } else {
                validateLocationInput(deliveryInput, deliveryErrorDiv, deliveryCoords);
                validateLocationInput(pickupInput, pickupErrorDiv, pickupCoords);
                checkLocationsConfirmed();
             }
             saveState();
             drawRoute();

        });
        drawRoute();
    }

    if (confirmLocationsBtn) {
        confirmLocationsBtn.addEventListener('click', function() {
            if (pickupCoords && deliveryCoords) {
                showStep(stepRouteConfirmDiv);
                drawRoute();
                saveState();
            } else {
                alert("Please ensure both pickup and delivery locations are set and valid.");
            }
        });
    }

    if (editLocationsBtn) editLocationsBtn.addEventListener('click', () => { showStep(stepLocationsDiv); saveState(); });
    if (proceedToReceiverBtn) proceedToReceiverBtn.addEventListener('click', () => { showStep(stepReceiverDiv); saveState(); });
    if (backToRouteBtn) backToRouteBtn.addEventListener('click', () => { showStep(stepRouteConfirmDiv); saveState(); });

    if (proceedToPaymentBtn) {
        proceedToPaymentBtn.addEventListener('click', () => {
            let isValid = true;
            if (receiverNameInput) receiverNameInput.classList.remove('is-invalid');
            if (receiverContactInput) receiverContactInput.classList.remove('is-invalid');

            if (!receiverNameInput || !receiverNameInput.value.trim()) {
                if (receiverNameInput) receiverNameInput.classList.add('is-invalid');
                isValid = false;
            }
            if (!receiverContactInput || !receiverContactInput.value.trim()) {
                if (receiverContactInput) receiverContactInput.classList.add('is-invalid');
                 isValid = false;
            }

            if (isValid) {
                updateReviewDetails();
                showStep(stepPaymentDiv);
                saveState();
            } else {
                 alert('Please enter valid receiver name and contact.');
            }
        });
    }

    if (backToReceiverBtn) backToReceiverBtn.addEventListener('click', () => { showStep(stepReceiverDiv); saveState(); });

    paymentMethodRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const selectedMethod = this.value;
            if (selectedMethod === 'mpesa') {
                if (mpesaPhoneGroup) mpesaPhoneGroup.style.display = 'block';
                if (finalPayButton) finalPayButton.innerHTML = '<i class="fas fa-mobile-alt me-1"></i> Pay KES 100.00 with M-Pesa';
            } else {
                if (mpesaPhoneGroup) mpesaPhoneGroup.style.display = 'none';
                if (finalPayButton) finalPayButton.innerHTML = '<i class="fab fa-stripe me-1"></i> Pay KES 100.00 with Card';
            }
            saveState();
        });
    });

    if (receiverNameInput) receiverNameInput.addEventListener('input', saveState);
    if (receiverContactInput) receiverContactInput.addEventListener('input', saveState);
    if (mpesaPhoneInput) mpesaPhoneInput.addEventListener('input', saveState);

    if (stripePublishableKey) {
        stripeHandler = StripeCheckout.configure({
            key: stripePublishableKey,
            image: 'URL_LOGO',
            locale: 'auto',
            token: function(token) {
                if (document.getElementById('stripeToken')) document.getElementById('stripeToken').value = token.id;
                console.log("Stripe token received:", token.id);
                sessionStorage.removeItem('pickupRequestState');
                if (parcelForm) parcelForm.submit();
            }
        });
        window.addEventListener('popstate', function() {
            if (stripeHandler) stripeHandler.close();
        });
    } else {
        console.warn("Stripe Publishable Key not found. Stripe payment disabled.");
        const stripeRadio = document.getElementById('pay_stripe');
        const mpesaRadio = document.getElementById('pay_mpesa');
        if (stripeRadio) stripeRadio.disabled = true;
        if (mpesaRadio) mpesaRadio.checked = true;
        if (mpesaPhoneGroup) mpesaPhoneGroup.style.display = 'block';
        if (finalPayButton) finalPayButton.innerHTML = '<i class="fas fa-mobile-alt me-1"></i> Pay KES 100.00 with M-Pesa';
    }

    if (finalPayButton) {
        finalPayButton.addEventListener('click', function(e) {
            e.preventDefault();
            const selectedMethodRadio = document.querySelector('input[name="payment_method"]:checked');
            if (!selectedMethodRadio) {
                alert("Please select a payment method.");
                return;
            }
            const selectedMethod = selectedMethodRadio.value;

            if (document.getElementById('pickup_location_final')) document.getElementById('pickup_location_final').value = pickupInput.value;
            if (document.getElementById('delivery_location_final')) document.getElementById('delivery_location_final').value = deliveryInput.value;
            if (document.getElementById('pickup_lat')) document.getElementById('pickup_lat').value = pickupCoords ? pickupCoords.lat : '';
            if (document.getElementById('pickup_lng')) document.getElementById('pickup_lng').value = pickupCoords ? pickupCoords.lng : '';
            if (document.getElementById('delivery_lat')) document.getElementById('delivery_lat').value = deliveryCoords ? deliveryCoords.lat : '';
            if (document.getElementById('delivery_lng')) document.getElementById('delivery_lng').value = deliveryCoords ? deliveryCoords.lng : '';
            if (document.getElementById('receiver_name_final')) document.getElementById('receiver_name_final').value = receiverNameInput.value;
            if (document.getElementById('receiver_contact_final')) document.getElementById('receiver_contact_final').value = receiverContactInput.value;

            if (selectedMethod === 'stripe') {
                if (stripeHandler) {
                    const paymentAmountCents = 10000;
                    stripeHandler.open({
                        name: 'Suivi Delivery',
                        description: `Delivery to ${receiverNameInput.value || 'Recipient'}`,
                        amount: paymentAmountCents,
                        currency: 'kes'
                    });
                } else {
                    alert("Stripe payment is currently unavailable.");
                }
            } else if (selectedMethod === 'mpesa') {
                const mpesaPhone = mpesaPhoneInput.value.trim();
                const phoneRegex = /^254\d{9}$/;
                if (mpesaPhoneError) mpesaPhoneError.textContent = '';

                if (!mpesaPhone) {
                     if (mpesaPhoneError) mpesaPhoneError.textContent = 'M-Pesa phone number is required.';
                     if (mpesaPhoneInput) mpesaPhoneInput.focus();
                     return;
                }
                if (!phoneRegex.test(mpesaPhone)) {
                     if (mpesaPhoneError) mpesaPhoneError.textContent = 'Please enter phone number in 254xxxxxxxxx format.';
                     if (mpesaPhoneInput) mpesaPhoneInput.focus();
                     return;
                }
                console.log("Submitting form for M-Pesa payment...");
                sessionStorage.removeItem('pickupRequestState');
                if (parcelForm) parcelForm.submit();
            }
        });
    }

    initMap();
    loadState();

});