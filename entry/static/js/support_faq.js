document.addEventListener("DOMContentLoaded", function() {
    const searchContainer = document.querySelector('.faq-search-container');
    const searchUrl = searchContainer ? searchContainer.dataset.searchUrl : null;

    const searchInput = document.getElementById('faq-search-input');
    const searchButton = document.getElementById('faq-search-button');
    const resultsContainer = document.getElementById('faq-search-results');
    const resultsList = document.getElementById('search-results-list');
    const noResultsMessage = document.getElementById('no-results-message');

    const performSearch = () => {
        if (!searchUrl) {
            console.error("Search URL is missing from data attribute.");
            resultsList.innerHTML = '<p class="text-danger">Configuration error: Cannot perform search.</p>';
            resultsContainer.style.display = 'block';
            noResultsMessage.style.display = 'none';
            return;
        }

        const searchTerm = searchInput.value.trim();

        if (!searchTerm) {
            resultsList.innerHTML = '';
            resultsContainer.style.display = 'none';
            noResultsMessage.style.display = 'none';
            return;
        }

        resultsList.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        resultsContainer.style.display = 'block';
        noResultsMessage.style.display = 'none';

        fetch(`${searchUrl}?search_query=${encodeURIComponent(searchTerm)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                resultsList.innerHTML = '';
                if (data && data.length > 0) {
                    data.forEach(faq => {
                        const itemId = `search-result-${faq.id || Math.random().toString(36).substring(7)}`;
                        const itemDiv = document.createElement('div');
                        itemDiv.classList.add('accordion-item', 'mb-2');

                        const header = document.createElement('h2');
                        header.classList.add('accordion-header');
                        header.id = `heading-${itemId}`;

                        const button = document.createElement('button');
                        button.classList.add('accordion-button', 'collapsed');
                        button.type = 'button';
                        button.dataset.bsToggle = 'collapse';
                        button.dataset.bsTarget = `#collapse-${itemId}`;
                        button.setAttribute('aria-expanded', 'false');
                        button.setAttribute('aria-controls', `collapse-${itemId}`);
                        button.textContent = faq.question;

                        const collapseDiv = document.createElement('div');
                        collapseDiv.id = `collapse-${itemId}`;
                        collapseDiv.classList.add('accordion-collapse', 'collapse');
                        collapseDiv.setAttribute('aria-labelledby', `heading-${itemId}`);

                        const bodyDiv = document.createElement('div');
                        bodyDiv.classList.add('accordion-body', 'text-muted');
                        bodyDiv.textContent = faq.answer;

                        header.appendChild(button);
                        collapseDiv.appendChild(bodyDiv);
                        itemDiv.appendChild(header);
                        itemDiv.appendChild(collapseDiv);
                        resultsList.appendChild(itemDiv);
                    });
                    noResultsMessage.style.display = 'none';
                } else {
                    noResultsMessage.style.display = 'block';
                }
                resultsContainer.style.display = 'block';
            })
            .catch(error => {
                console.error("Error performing search:", error);
                resultsList.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
                resultsContainer.style.display = 'block';
                noResultsMessage.style.display = 'none';
            });
    };

    if (searchButton && searchInput) {
        searchButton.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    } else {
        console.warn("FAQ Search input or button not found.");
    }
});
