// ===============================
// CONFIG
// ===============================
const API_BASE_URL = 'https://crptrix-backend.onrender.com';

const FX_RATES = {
    USD: 1,
    INR: 91.61,
    EUR: 0.85
};

let cachedData = null;
let currentCurrency = 'USD';

// ===============================
// DOM ELEMENTS
// ===============================
const el = {
    currency: document.getElementById('currencyDropdown'),
    prob: document.getElementById('probabilityValue'),
    risk: document.getElementById('riskValue'),
    price: document.getElementById('btcPrice'),
    circle: document.querySelector('.progress-ring-circle')
};

// ===============================
// UI HELPERS
// ===============================
function setProgress(p) {
    const r = 95;
    const c = 2 * Math.PI * r;
    el.circle.style.strokeDashoffset = c - (p / 100) * c;
}

function getCurrencySymbol(currency) {
    return { USD: '$', INR: '₹', EUR: '€' }[currency] || '$';
}

function convertPrice(usd, currency) {
    if (usd === null || usd === undefined || isNaN(usd)) {
        return 'Unavailable';
    }
    const rate = FX_RATES[currency] || 1;
    const converted = usd * rate;
    return `${getCurrencySymbol(currency)}${converted.toLocaleString()}`;
}

// ===============================
// API
// ===============================
async function fetchData() {
    try {
        el.prob.textContent = '...';
        el.risk.textContent = 'Loading...';
        el.price.textContent = 'Loading...';

        const res = await fetch(`${API_BASE_URL}/predict`);
        if (!res.ok) throw new Error('API error');

        cachedData = await res.json();
        updateUI();

    } catch (err) {
        console.error('Frontend error:', err);
        el.prob.textContent = '--';
        el.risk.textContent = 'Error';
        el.price.textContent = 'Unavailable';
    }
}

// ===============================
// UI UPDATE
// ===============================
function updateUI() {
    if (!cachedData) return;

    const p = Math.round(cachedData.growth_probability);

    el.prob.textContent = p;
    setProgress(p);

    el.risk.textContent = cachedData.risk_level;
    el.risk.className = 'risk-value';

    if (cachedData.risk_level.includes('Low')) {
        el.risk.classList.add('low');
    } else if (cachedData.risk_level.includes('Medium')) {
        el.risk.classList.add('medium');
    } else {
        el.risk.classList.add('high');
    }

    el.price.textContent = convertPrice(
        cachedData.price_usd,
        currentCurrency
    );
}

// ===============================
// EVENTS
// ===============================
el.currency.addEventListener('change', e => {
    currentCurrency = e.target.value;
    updateUI(); // ✅ NO API CALL
});

window.onload = fetchData;
