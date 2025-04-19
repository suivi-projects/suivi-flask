document.addEventListener('DOMContentLoaded', function() {
    const greetingElement = document.querySelector('.greeting-message');
    const username = greetingElement.dataset.username;
    const currentHour = new Date().getHours();

    let greetingMessage = '';
    if (currentHour < 12) {
        greetingMessage = `Good Morning! ${username}`;
    } else if (currentHour < 18) {
        greetingMessage = `Good Afternoon! ${username}`;
    } else {
        greetingMessage = `Good Evening! ${username}`;
    }

    const h1Element = document.createElement('h1');
    h1Element.textContent = greetingMessage;
    greetingElement.innerHTML = '';
    greetingElement.appendChild(h1Element);
});