(() => {
  "use strict";

  // Set this to the public URL of your Render/Koyeb/Railway FastAPI service.
  // Leave empty when the frontend and API are served from the same origin.
  const API_URL = "";
  const ANALYSIS_ENDPOINT = "/api/v1/campaigns/test";

  const form = document.getElementById("analysisForm");
  const submitButton = document.getElementById("submitButton");
  const buttonText = document.getElementById("buttonText");
  const buttonSpinner = document.getElementById("buttonSpinner");
  const emptyState = document.getElementById("emptyState");
  const resultsContent = document.getElementById("resultsContent");
  const connectionStatus = document.getElementById("connectionStatus");

  if (!(form instanceof HTMLFormElement)) return;

  const apiBase = API_URL.replace(/\/$/, "");
  const endpoint = `${apiBase}${ANALYSIS_ENDPOINT}`;

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#039;",
    '"': "&quot;",
  }[character]));

  const setLoading = (loading) => {
    submitButton.disabled = loading;
    buttonSpinner.classList.toggle("hidden", !loading);
    buttonText.textContent = loading ? "Analyzing…" : "Generate revenue analysis";
  };

  const setConnection = (connected, label) => {
    connectionStatus.innerHTML = `<span class="h-2 w-2 rounded-full ${connected ? "bg-emerald-400" : "bg-rose-400"}"></span>${escapeHtml(label)}`;
  };

  const showError = (message) => {
    emptyState.classList.add("hidden");
    resultsContent.classList.remove("hidden");
    resultsContent.innerHTML = `
      <div class="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6">
        <div class="flex items-start gap-4">
          <div class="text-2xl">⚠️</div>
          <div>
            <h2 class="font-bold text-rose-200">Analysis unavailable</h2>
            <p class="mt-2 text-sm leading-6 text-rose-100/80">${escapeHtml(message)}</p>
            <p class="mt-4 text-xs text-rose-200/60">Check API_URL, the backend health endpoint, CORS settings, and deployment logs.</p>
          </div>
        </div>
      </div>`;
    setConnection(false, "Backend unavailable");
  };

  const number = (value, fallback = "—") => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed.toLocaleString() : fallback;
  };

  const renderResults = (payload, input) => {
    const sent = payload.status === "sent" || Boolean(payload.message_id ?? payload.telegram_message_id);
    const temperature = payload.temp_c ?? input.temperature_c;
    const recipients = payload.recipients ?? 0;
    const statusLabel = sent ? "Campaign sent" : "Campaign recorded";
    const statusClass = sent ? "text-emerald-300 bg-emerald-400/10 border-emerald-400/20" : "text-amber-300 bg-amber-400/10 border-amber-400/20";

    emptyState.classList.add("hidden");
    resultsContent.classList.remove("hidden");
    resultsContent.innerHTML = `
      <div class="mb-7 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p class="text-sm font-semibold text-cyan-300">Live recommendation</p>
          <h2 class="mt-1 text-2xl font-bold">Revenue action generated</h2>
          <p class="mt-2 text-sm text-slate-400">${escapeHtml(input.business_type)} · ${escapeHtml(input.location)}</p>
        </div>
        <span class="inline-flex items-center gap-2 self-start rounded-full border px-3 py-2 text-xs font-semibold ${statusClass}">
          <span class="h-2 w-2 rounded-full ${sent ? "bg-emerald-400" : "bg-amber-400"}"></span>${statusLabel}
        </span>
      </div>
      <div class="grid gap-4 sm:grid-cols-3">
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-5"><p class="text-xs uppercase tracking-wider text-slate-500">Temperature</p><p class="mt-2 text-3xl font-bold">${number(temperature)}<span class="text-lg text-slate-500">°C</span></p></div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-5"><p class="text-xs uppercase tracking-wider text-slate-500">Audience reached</p><p class="mt-2 text-3xl font-bold">${number(recipients)}</p><p class="text-xs text-slate-500">leads</p></div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-5"><p class="text-xs uppercase tracking-wider text-slate-500">Objective</p><p class="mt-2 text-lg font-semibold leading-7">${escapeHtml(input.objective.replaceAll("_", " "))}</p></div>
      </div>
      <div class="mt-6 rounded-2xl border border-brand/20 bg-brand/10 p-6">
        <p class="text-xs font-semibold uppercase tracking-wider text-brand-200">AI analysis</p>
        <p class="mt-3 leading-7 text-slate-200">${sent ? "Favorable conditions detected. Your targeted campaign was delivered to the configured audience. Monitor conversion and adjust the offer as demand changes." : "The campaign was logged, but delivery is not confirmed. Review your Telegram configuration and retry after the messaging service is available."}</p>
      </div>
      <dl class="mt-6 grid gap-3 border-t border-slate-800 pt-5 text-sm sm:grid-cols-2">
        <div><dt class="text-slate-500">Campaign status</dt><dd class="mt-1 font-medium text-slate-200">${escapeHtml(payload.status ?? "unknown")}</dd></div>
        <div><dt class="text-slate-500">Message ID</dt><dd class="mt-1 font-medium text-slate-200">${escapeHtml(payload.message_id ?? payload.telegram_message_id ?? "Not available")}</dd></div>
      </dl>`;
    setConnection(true, "Backend connected");
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setLoading(true);

    const formData = new FormData(form);
    const input = Object.fromEntries(formData.entries());
    input.temperature_c = Number(input.temperature_c);
    input.humidity = input.humidity === "" ? null : Number(input.humidity);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(input),
      });

      let payload = {};
      try { payload = await response.json(); } catch { /* handled below */ }
      if (!response.ok) {
        throw new Error(payload.detail || `Backend returned HTTP ${response.status}`);
      }

      renderResults(payload, input);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected runtime error";
      showError(message.includes("Failed to fetch") ? "The backend could not be reached. Confirm that the service is running and CORS allows this Vercel domain." : message);
    } finally {
      setLoading(false);
    }
  });
})();
