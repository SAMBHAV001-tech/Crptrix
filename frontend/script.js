// API base injected from index.html
const API_BASE_URL = window.API_BASE_URL;

let currentCurrency = 'USD';

const elements = {
    currencyDropdown: document.getElementById('currencyDropdown'),
    probabilityValue: document.getElementById('probabilityValue'),
    riskValue: document.getElementById('riskValue'),
    btcPrice: document.getElementById('btcPrice'),
    progressCircle: document.querySelector('.progress-ring-circle')
};

// ---------------------------
// Animation helpers
// ---------------------------
function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 16);
}

function setCircularProgress(percentage) {
    const radius = 95;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;
    elements.progressCircle.style.strokeDashoffset = offset;
}

// ---------------------------
// Currency formatting
// ---------------------------
function getCurrencySymbol(currency) {
    const symbols = { USD: '$', INR: '₹', EUR: '€' };
    return symbols[currency] || '';
}

function formatPrice(price, currency) {
    const symbol = getCurrencySymbol(currency);
    return `${symbol}${price.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}

// ---------------------------
// Risk badge mapping
// ---------------------------
function applyRiskStyle(riskText) {
    elements.riskValue.className = 'risk-value';

    if (riskText === 'Low Risk') {
        elements.riskValue.classList.add('low');
    } else if (riskText === 'Medium Risk') {
        elements.riskValue.classList.add('medium');
    } else {
        elements.riskValue.classList.add('high');
    }
}

// ---------------------------
// Fetch prediction
// ---------------------------
async function fetchPrediction(currency) {
    try {
        elements.probabilityValue.textContent = '...';
        elements.riskValue.textContent = 'Loading...';
        elements.btcPrice.textContent = 'Loading...';

        const response = await fetch(
            `${API_BASE_URL}/predict?currency=${currency}`
        );

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        updateUI(data);

    } catch (error) {
        console.error('Prediction fetch failed:', error);
        elements.probabilityValue.textContent = '--';
        elements.riskValue.textContent = 'Unavailable';
        elements.btcPrice.textContent = '--';
    }
}

// ---------------------------
// Update UI from backend data
// ---------------------------
function updateUI(data) {
    const probability = Math.round(data.growth_probability);
    const price = data.current_price;
    const currency = data.currency;

    animateValue(elements.probabilityValue, 0, probability, 1200);
    setCircularProgress(probability);

    elements.riskValue.textContent = data.risk_level;
    applyRiskStyle(data.risk_level);

    elements.btcPrice.textContent = formatPrice(price, currency);
}

// ---------------------------
// Event listeners
// ---------------------------
elements.currencyDropdown.addEventListener('change', (e) => {
    currentCurrency = e.target.value;
    fetchPrediction(currentCurrency);
});

window.addEventListener('load', () => {
    fetchPrediction(currentCurrency);
});
