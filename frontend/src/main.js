const tokenKey = "nebula_token";
const ageKey = "nebula_age_verified";
const apiOverride = import.meta.env && import.meta.env.VITE_API_BASE_URL;
const baseUrl = (apiOverride || "/api").replace(/\/$/, "");

const ageGate = document.getElementById("age-gate");
const ageConfirm = document.getElementById("age-confirm");
const registerForm = document.getElementById("register-form");
const loginForm = document.getElementById("login-form");
const authMessage = document.getElementById("auth-message");
const dashboard = document.getElementById("dashboard");
const statBalance = document.getElementById("stat-balance");
const statLoyalty = document.getElementById("stat-loyalty");
const welcomeLine = document.getElementById("welcome-line");
const loyaltyProgress = document.getElementById("loyalty-progress");
const sessionList = document.getElementById("session-list");
const transactionList = document.getElementById("transaction-list");
const bonusButton = document.getElementById("bonus-button");
const purchaseSelect = document.getElementById("purchase-select");
const purchaseButton = document.getElementById("purchase-button");
const slotsForm = document.getElementById("slots-form");
const blackjackForm = document.getElementById("blackjack-form");
const sportsForm = document.getElementById("sports-form");
const slotsOutput = document.getElementById("slots-output");
const blackjackOutput = document.getElementById("blackjack-output");
const sportsOutput = document.getElementById("sports-output");
const ctaRegister = document.getElementById("cta-register");
const ctaLogin = document.getElementById("cta-login");
const logoutButton = document.getElementById("logout-button");

function showMessage(message, isError = false) {
  authMessage.textContent = message;
  authMessage.style.color = isError ? "var(--danger)" : "var(--success)";
}

function toggleForms(show) {
  registerForm.classList.toggle("hidden", show !== "register");
  loginForm.classList.toggle("hidden", show !== "login");
}

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem(tokenKey);
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });
  if (response.status === 401) {
    logout();
    throw new Error("Session expired. Please log in again.");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || "Unexpected error";
    throw new Error(detail);
  }
  return data;
}

function logout(showAlert = true) {
  localStorage.removeItem(tokenKey);
  dashboard.classList.add("hidden");
  toggleForms("login");
  if (showAlert) {
    showMessage("You have been logged out.");
  }
}

async function loadDashboard() {
  try {
    const snapshot = await apiFetch("/players/dashboard");
    const { profile, recent_sessions, transactions } = snapshot;
    dashboard.classList.remove("hidden");
    toggleForms();
    welcomeLine.textContent = `Welcome back, ${profile.username}.`;
    statBalance.textContent = profile.balance.toLocaleString();
    statLoyalty.textContent = profile.loyalty_points.toLocaleString();

    const tier = loyaltyTier(profile.loyalty_points);
    loyaltyProgress.textContent = `You are shining as a ${tier.label} explorer. ${tier.nextText}`;

    sessionList.innerHTML = recent_sessions.length
      ? recent_sessions
          .map((session) => {
            let details;
            try {
              details = JSON.parse(session.details);
            } catch (error) {
              details = {};
            }
            const bet = Number(session.bet_amount).toLocaleString();
            const net = formatNet(session.net_result);
            const when = formatDate(session.created_at);
            const summary = summarizeDetails(details);
            return `<li><strong>${formatTitle(session.game_type)}</strong> — bet ${bet} • net ${net}<br/><small>${when}</small><br/><small>${summary}</small></li>`;
          })
          .join("")
      : '<li class="empty-state">No sessions logged yet. Try Prism Slots to begin!</li>';

    transactionList.innerHTML = transactions.length
      ? transactions
          .map(
            (txn) =>
              `<li><strong>${formatTitle(txn.type)}</strong> — ${formatNet(txn.amount)} credits<br/><small>${txn.description}</small><br/><small>${formatDate(txn.created_at)}</small></li>`
          )
          .join("")
      : '<li class="empty-state">Play games or claim bonuses to populate your ledger.</li>';
  } catch (error) {
    showMessage(error.message, true);
  }
}

function loyaltyTier(points) {
  if (points > 10000) {
    return { label: "Supernova", nextText: "Legendary bonuses unlocked every weekend." };
  }
  if (points > 5000) {
    return { label: "Nova", nextText: "Reach 10,001 points for exclusive avatar halos." };
  }
  if (points > 2000) {
    return { label: "Comet", nextText: "Push to 5,001 points to access priority missions." };
  }
  if (points > 500) {
    return { label: "Stardust", nextText: "Earn 2,001 points to join the Comet circle." };
  }
  return { label: "Rookie", nextText: "Gather 501 points to unlock Stardust status." };
}

function formatNet(value) {
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return value;
  }
  if (amount > 0) {
    return `+${amount.toLocaleString()}`;
  }
  return amount.toLocaleString();
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) {
    return value;
  }
  return date.toLocaleString();
}

function formatTitle(text) {
  return text
    .replace(/_/g, " ")
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function summarizeDetails(details) {
  if (details.symbols) {
    return `Reels: ${details.symbols.join(" | ")} (${details.message})`;
  }
  if (details.outcome) {
    const dealer = details.dealer ? ` vs Dealer ${details.dealer.join(", ")}` : "";
    const player = details.player ? details.player.join(", ") : "player";
    return `Outcome: ${formatTitle(details.outcome)} — Player ${player}${dealer}`;
  }
  if (details.selection) {
    return `Picked ${formatTitle(details.selection)} • Winner ${formatTitle(details.winner)}`;
  }
  return "Session details recorded.";
}

function setOutput(target, message, isError = false) {
  target.textContent = message;
  target.classList.toggle("error", isError);
}

registerForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(registerForm);
  const payload = Object.fromEntries(formData.entries());
  payload.age = Number(payload.age);
  try {
    const token = await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    localStorage.setItem(tokenKey, token.access_token);
    showMessage("Registration successful. Welcome aboard!");
    await loadDashboard();
  } catch (error) {
    showMessage(error.message, true);
  }
});

loginForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(loginForm);
  const payload = Object.fromEntries(formData.entries());
  try {
    const token = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    localStorage.setItem(tokenKey, token.access_token);
    showMessage("Login successful. Enjoy the games!");
    await loadDashboard();
  } catch (error) {
    showMessage(error.message, true);
  }
});

bonusButton?.addEventListener("click", async () => {
  try {
    const result = await apiFetch("/players/daily-bonus", { method: "POST" });
    if (result.awarded) {
      showMessage(`Bonus claimed! +${result.amount} credits added.`);
    } else {
      showMessage(`Bonus already claimed. Next recharge at ${new Date(result.next_claim).toLocaleString()}.`);
    }
    await loadDashboard();
  } catch (error) {
    showMessage(error.message, true);
  }
});

purchaseButton?.addEventListener("click", async () => {
  const packageId = purchaseSelect.value;
  if (!packageId) {
    showMessage("Select a credit pack first.", true);
    return;
  }
  try {
    const result = await apiFetch("/players/purchase", {
      method: "POST",
      body: JSON.stringify({ package_id: packageId }),
    });
    showMessage(result.message);
    await loadDashboard();
  } catch (error) {
    showMessage(error.message, true);
  }
});

slotsForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(slotsForm);
  const bet = Number(formData.get("bet"));
  try {
    const result = await apiFetch("/players/games/slots", {
      method: "POST",
      body: JSON.stringify({ bet }),
    });
    setOutput(
      slotsOutput,
      `Symbols: ${result.symbols.join(" | ")}\n${result.message}\nNet: ${formatNet(result.net)}`
    );
    await loadDashboard();
  } catch (error) {
    setOutput(slotsOutput, error.message, true);
  }
});

blackjackForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(blackjackForm);
  const bet = Number(formData.get("bet"));
  try {
    const result = await apiFetch("/players/games/blackjack", {
      method: "POST",
      body: JSON.stringify({ bet }),
    });
    setOutput(
      blackjackOutput,
      `You: ${result.player_hand.join(", ")}\nDealer: ${result.dealer_hand.join(", ")}\nOutcome: ${formatTitle(result.outcome)}\nNet: ${formatNet(result.net)}`
    );
    await loadDashboard();
  } catch (error) {
    setOutput(blackjackOutput, error.message, true);
  }
});

sportsForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(sportsForm);
  const bet = Number(formData.get("bet"));
  const selection = formData.get("selection");
  try {
    const result = await apiFetch("/players/games/virtual-sport", {
      method: "POST",
      body: JSON.stringify({ bet, selection }),
    });
    setOutput(
      sportsOutput,
      `You backed ${formatTitle(result.selection)} at ${result.odds}x\nWinner: ${formatTitle(
        result.winner
      )}\nNet: ${formatNet(result.net)}`
    );
    await loadDashboard();
  } catch (error) {
    setOutput(sportsOutput, error.message, true);
  }
});

ctaRegister?.addEventListener("click", () => toggleForms("register"));
ctaLogin?.addEventListener("click", () => toggleForms("login"));
logoutButton?.addEventListener("click", () => logout());

ageConfirm?.addEventListener("click", () => {
  localStorage.setItem(ageKey, "true");
  ageGate.classList.add("hidden");
});

function initAgeGate() {
  if (localStorage.getItem(ageKey)) {
    ageGate.classList.add("hidden");
  } else {
    ageGate.classList.remove("hidden");
  }
}

function initAuthState() {
  const token = localStorage.getItem(tokenKey);
  if (token) {
    loadDashboard();
  } else {
    toggleForms("register");
  }
}

initAgeGate();
initAuthState();
