const API_BASE_URL = 'https://crptrix-backend.onrender.com';

let currentCurrency = 'USD';

const elements = {
    currencyDropdown: document.getElementById('currencyDropdown'),
    probabilityValue: document.getElementById('probabilityValue'),
    riskValue: document.getElementById('riskValue'),
    btcPrice: document.getElementById('btcPrice'),
    progressCircle: document.querySelector('.progress-ring-circle')
};

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

function getCurrencySymbol(currency) {
    return { USD: '$', INR: '₹', EUR: '€' }[currency] || '$';
}

function formatPrice(price, currency) {
    return `${getCurrencySymbol(currency)}${price.toLocaleString()}`;
}

async function fetchPrediction(currency) {
    try {
        const res = await fetch(`${API_BASE_URL}/predict?currency=${currency}`);
        if (!res.ok) throw new Error('API error');
        const data = await res.json();

        // --- Probability ---
        const probability = Math.round(data.growth_probability);
        animateValue(elements.probabilityValue, 0, probability, 1200);
        setCircularProgress(probability);

        // --- Risk ---
        elements.riskValue.textContent = data.risk_level;
        elements.riskValue.className = 'risk-value';

        // --- Price ---
        elements.btcPrice.textContent = formatPrice(
            data.current_price,
            currency
        );

    } catch (err) {
        console.error(err);
        elements.probabilityValue.textContent = '--';
        elements.riskValue.textContent = 'Error';
        elements.btcPrice.textContent = 'Error';
    }
}

elements.currencyDropdown.addEventListener('change', e => {
    currentCurrency = e.target.value;
    fetchPrediction(currentCurrency);
});

window.addEventListener('load', () => {
    fetchPrediction(currentCurrency);
});
