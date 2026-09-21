/* =====================================================================
   Earth in Real Time — main.js
   Handles: live clocks, weather search, earth facts, world map, APOD
   ===================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("footer-year").textContent = new Date().getFullYear();

  initLiveClocks();
  initWeatherSearch();
  initEarthFacts();
  initWorldMap();
  initApod();
  initApodLightbox();  
});

/* ---------------------------------------------------------------------
   1. Live world clock + timezone cards (updates every second)
   --------------------------------------------------------------------- */

function initLiveClocks() {
  const clockCards = document.querySelectorAll(".clock-card");
  const tzCards = document.querySelectorAll(".tz-card");

  function tick() {
    const now = new Date();

    clockCards.forEach((card) => {
      const tz = card.dataset.tz;
      try {
        const time = now.toLocaleTimeString("en-US", { timeZone: tz, hour12: true });
        const date = now.toLocaleDateString("en-US", {
          timeZone: tz,
          weekday: "short",
          month: "short",
          day: "numeric",
        });
        card.querySelector(".clock-time").textContent = time;
        card.querySelector(".clock-date").textContent = date;
      } catch (err) {
        card.querySelector(".clock-time").textContent = "--:--:--";
      }
    });

    tzCards.forEach((card) => {
      const tz = card.dataset.tz;
      try {
        const time = now.toLocaleTimeString("en-US", {
          timeZone: tz,
          hour: "2-digit",
          minute: "2-digit",
          hour12: true,
        });
        const offset = getUtcOffsetLabel(tz, now);
        card.querySelector(".tz-time").textContent = time;
        card.querySelector(".tz-offset").textContent = offset;
      } catch (err) {
        card.querySelector(".tz-time").textContent = "--:--";
      }
    });
  }

  tick();
  setInterval(tick, 1000);
}

/** Compute a human readable UTC offset string for a given IANA timezone. */
function getUtcOffsetLabel(timeZone, date) {
  const dtf = new Intl.DateTimeFormat("en-US", {
    timeZone,
    timeZoneName: "shortOffset",
  });
  const parts = dtf.formatToParts(date);
  const offsetPart = parts.find((p) => p.type === "timeZoneName");
  return offsetPart ? offsetPart.value.replace("GMT", "UTC") : "UTC";
}

/* ---------------------------------------------------------------------
   2. Weather search (+ sunrise/sunset + moon info)
   --------------------------------------------------------------------- */

function initWeatherSearch() {
  const form = document.getElementById("weather-form");
  const input = document.getElementById("city-input");
  const statusBox = document.getElementById("weather-status");
  const results = document.getElementById("weather-results");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const city = input.value.trim();
    if (!city) return;

    showStatus("Fetching live weather data…", "loading");
    results.hidden = true;

    try {
      const response = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
      const data = await response.json();

      if (!data.success) {
        showStatus(data.error || "Something went wrong. Please try again.", "error");
        return;
      }

      renderWeather(data);
      hideStatus();
      results.hidden = false;
    } catch (err) {
      showStatus("Network error — please check your connection and try again.", "error");
    }
  });

  function showStatus(message, type) {
    statusBox.textContent = message;
    statusBox.hidden = false;
    statusBox.className = "status-message" + (type === "loading" ? " loading" : "");
  }

  function hideStatus() {
    statusBox.hidden = true;
  }

  function renderWeather(data) {
    document.getElementById("w-city").textContent = `${data.city}${data.country ? ", " + data.country : ""}`;
    document.getElementById("w-condition").textContent = data.condition;
    document.getElementById("w-temp").textContent = `${data.temperature}°C`;
    document.getElementById("w-feels").textContent = `${data.feels_like}°C`;
    document.getElementById("w-humidity").textContent = `${data.humidity}%`;
    document.getElementById("w-wind").textContent = `${data.wind_speed} m/s`;

    const iconEl = document.getElementById("w-icon");
    if (data.icon) {
      iconEl.src = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
      iconEl.alt = data.condition;
      iconEl.hidden = false;
    } else {
      iconEl.hidden = true;
    }

    document.getElementById("sun-rise").textContent = data.sunrise;
    document.getElementById("sun-set").textContent = data.sunset;
    document.getElementById("sun-length").textContent = data.day_length;

    const moon = data.moon || {};
    document.getElementById("moon-emoji").textContent = moon.emoji || "🌔";
    document.getElementById("moon-phase").textContent = moon.phase_name || "Unavailable";
    document.getElementById("moon-illum").textContent = moon.illumination != null ? `${moon.illumination}%` : "N/A";
    document.getElementById("moon-rise").textContent = moon.moonrise || "N/A";
    document.getElementById("moon-set").textContent = moon.moonset || "N/A";
  }
}

/* ---------------------------------------------------------------------
   3. Earth facts
   --------------------------------------------------------------------- */

function initEarthFacts() {
  const factText = document.getElementById("fact-text");
  const factCard = document.getElementById("fact-card");
  const newFactBtn = document.getElementById("new-fact-btn");

  async function loadFact() {
    try {
      const response = await fetch("/api/fact");
      const data = await response.json();
      factCard.style.animation = "none";
      // eslint-disable-next-line no-unused-expressions
      factCard.offsetHeight; // trigger reflow to replay animation
      factCard.style.animation = "fadeSlide 0.5s ease";
      factText.textContent = data.fact;
    } catch (err) {
      factText.textContent = "Earth is the only known planet with life. That's a pretty good fact on its own.";
    }
  }

  newFactBtn.addEventListener("click", loadFact);
  loadFact();
}

/* ---------------------------------------------------------------------
   4. Interactive world map (Leaflet)
   --------------------------------------------------------------------- */

function initWorldMap() {
  const mapEl = document.getElementById("world-map");
  if (!mapEl || typeof L === "undefined") return;

  const map = L.map("world-map", {
    center: [20, 0],
    zoom: 2,
    minZoom: 2,
    worldCopyJump: true,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18,
  }).addTo(map);
}

/* ---------------------------------------------------------------------
   5. NASA Picture of the Day
   --------------------------------------------------------------------- */

let apodItems = [];

async function initApod() {
  const loading = document.getElementById("apod-loading");
  const grid = document.getElementById("apod-grid");
  const errorBox = document.getElementById("apod-error");

  try {
    console.log("🌌 Fetching NASA APOD gallery...");

    const response = await fetch("/api/apod?count=5");
    if (!response.ok) throw new Error(`API returned HTTP ${response.status}`);

    const data = await response.json();
    console.log("🌌 NASA APOD response:", data);

    if (!data.success) throw new Error(data.error || "APOD unavailable");
    if (!data.items || data.items.length === 0) throw new Error("NASA returned no pictures.");

    grid.innerHTML = "";

    data.items.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = "glass-card apod-item";

      const isImage = item.media_type === "image" && item.url;

      card.innerHTML = `
        <div class="apod-item-media${isImage ? " zoomable" : ""}" ${isImage ? `data-index="${index}"` : ""}>
          ${
            isImage
              ? `<img src="${item.url}" alt="${escapeHtml(item.title)}" loading="lazy"><span class="zoom-hint">🔍 Click to enlarge</span>`
              : `<a class="apod-video-link" href="${item.url}" target="_blank" rel="noopener">▶ Watch on NASA</a>`
          }
        </div>
        <div class="apod-item-text">
          <h3>${escapeHtml(item.title)}</h3>
          <p class="apod-date">${escapeHtml(item.date)}</p>
          <p class="apod-explanation">${escapeHtml(item.explanation)}</p>
        </div>
      `;

      grid.appendChild(card);
    });

    apodItems = data.items;

    loading.hidden = true;
    errorBox.hidden = true;
    grid.hidden = false;
  } catch (err) {
    console.error("❌ APOD error:", err);
    loading.hidden = true;
    grid.hidden = true;
    errorBox.hidden = false;
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

/* ---------------------------------------------------------------------
   6. APOD lightbox (click an image to view it full size, full text)
   --------------------------------------------------------------------- */

function initApodLightbox() {
  const grid = document.getElementById("apod-grid");
  const lightbox = document.getElementById("apod-lightbox");
  const backdrop = document.getElementById("apod-lightbox-backdrop");
  const closeBtn = document.getElementById("apod-lightbox-close");
  const lbImg = document.getElementById("apod-lightbox-img");
  const lbTitle = document.getElementById("apod-lightbox-title");
  const lbDate = document.getElementById("apod-lightbox-date");
  const lbExplanation = document.getElementById("apod-lightbox-explanation");

  if (!grid || !lightbox) return;

  grid.addEventListener("click", (event) => {
    const media = event.target.closest(".apod-item-media.zoomable");
    if (!media) return;

    const item = apodItems[Number(media.dataset.index)];
    if (!item) return;

    lbImg.src = item.url;
    lbImg.alt = item.title || "";
    lbTitle.textContent = item.title || "";
    lbDate.textContent = item.date || "";
    lbExplanation.textContent = item.explanation || "";

    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
  });

  function close() {
    lightbox.hidden = true;
    lbImg.src = "";
    document.body.style.overflow = "";
  }

  backdrop.addEventListener("click", close);
  closeBtn.addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !lightbox.hidden) close();
  });
}
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

