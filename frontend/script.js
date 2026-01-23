// ===============================
// CONFIG
// ===============================
const API_BASE_URL = "https://crptrix-backend.onrender.com";

let currentCurrency = "USD";

const FX_RATES = {
    USD: 1,
    INR: 91.78,
    EUR: 0.85
};

// ===============================
// DOM ELEMENTS
// ===============================
const elements = {
    currencyDropdown: document.getElementById("currencyDropdown"),
    probabilityValue: document.getElementById("probabilityValue"),
    riskValue: document.getElementById("riskValue"),
    btcPrice: document.getElementById("btcPrice"),
    progressCircle: document.querySelector(".progress-ring-circle")
};

// ===============================
// UI HELPERS
// ===============================
function animateValue(element, start, end, duration) {
    const range = end - start;
    let current = start;
    const increment = range / (duration / 16);

    const timer = setInterval(() => {
        current += increment;
        if (
            (increment > 0 && current >= end) ||
            (increment < 0 && current <= end)
        ) {
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
    return { USD: "$", INR: "₹", EUR: "€" }[currency] || "$";
}

function formatPrice(price, currency) {
    if (price === null || isNaN(price)) return "Unavailable";
    return `${getCurrencySymbol(currency)}${price.toLocaleString()}`;
}

// ===============================
// CORE API CALL
// ===============================
async function fetchPrediction(currency) {
    try {
        elements.probabilityValue.textContent = "...";
        elements.riskValue.textContent = "Loading...";
        elements.btcPrice.textContent = "Loading...";

        const res = await fetch(`${API_BASE_URL}/predict`);
        if (!res.ok) throw new Error("API error");

        const data = await res.json();

        // ----- Probability -----
        const probability = Math.round(data.growth_probability * 100);
        animateValue(elements.probabilityValue, 0, probability, 1200);
        setCircularProgress(probability);

        // ----- Risk -----
        elements.riskValue.textContent = data.risk_level;
        elements.riskValue.className = "risk-value";

        if (data.risk_level.includes("Low")) {
            elements.riskValue.classList.add("low");
        } else if (data.risk_level.includes("Medium")) {
            elements.riskValue.classList.add("medium");
        } else {
            elements.riskValue.classList.add("high");
        }

        // ----- Price conversion -----
        if (data.price_usd !== null && data.price_usd !== undefined) {
            const converted =
                data.price_usd * (FX_RATES[currency] || 1);
            elements.btcPrice.textContent =
                formatPrice(converted, currency);
        } else {
            elements.btcPrice.textContent = "Unavailable";
        }

    } catch (err) {
        console.error("Frontend error:", err);
        elements.probabilityValue.textContent = "--";
        elements.riskValue.textContent = "Error";
        elements.btcPrice.textContent = "Unavailable";
    }
}

// ===============================
// EVENTS
// ===============================
elements.currencyDropdown.addEventListener("change", (e) => {
    currentCurrency = e.target.value;
    fetchPrediction(currentCurrency);
});

window.addEventListener("load", () => {
    fetchPrediction(currentCurrency);
});
