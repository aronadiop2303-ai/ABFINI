(() => {
  "use strict";

  const conversation = document.getElementById("conversation");
  const composer = document.getElementById("composer");
  const input = document.getElementById("message-input");
  const sendButton = document.getElementById("send-button");
  const refreshButton = document.getElementById("refresh-status");

  let apiUrl = null;

  function setDot(key, state, detail) {
    const dot = document.querySelector(`[data-dot="${key}"]`);
    const label = document.querySelector(`[data-detail="${key}"]`);
    if (dot) dot.dataset.state = state;
    if (label) label.textContent = detail;
  }

  async function loadConfig() {
    try {
      const response = await fetch("/api/config");
      if (!response.ok) throw new Error(`config HTTP ${response.status}`);
      const body = await response.json();
      if (!body.apiUrl) throw new Error("ABFINI_API_URL is not configured on Vercel");
      apiUrl = body.apiUrl;
      return true;
    } catch (err) {
      ["api", "model_router", "embedding", "supabase"].forEach((key) =>
        setDot(key, "error", "config Vercel manquante")
      );
      return false;
    }
  }

  async function refreshStatus() {
    if (!apiUrl) {
      const ok = await loadConfig();
      if (!ok) return;
    }

    try {
      const health = await fetch(`${apiUrl}/health`);
      setDot("api", health.ok ? "ok" : "error", health.ok ? "en ligne" : `HTTP ${health.status}`);
    } catch (err) {
      setDot("api", "error", "injoignable");
      setDot("model_router", "error", "injoignable");
      setDot("embedding", "error", "injoignable");
      setDot("supabase", "error", "injoignable");
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/health/dependencies`);
      const body = await response.json();
      const deps = body.dependencies || {};
      for (const key of ["model_router", "embedding", "supabase"]) {
        const dep = deps[key];
        if (!dep) {
          setDot(key, "error", "absent de la réponse");
          continue;
        }
        setDot(key, dep.status === "ok" ? "ok" : "error", dep.status === "ok" ? "ok" : dep.detail || "erreur");
      }
    } catch (err) {
      ["model_router", "embedding", "supabase"].forEach((key) => setDot(key, "error", "vérification impossible"));
    }
  }

  function appendTurn({ role, text, isError = false }) {
    const emptyState = conversation.querySelector(".empty-state");
    if (emptyState) emptyState.remove();

    const turn = document.createElement("div");
    turn.className = `turn ${role}${isError ? " error" : ""}`;
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    turn.appendChild(bubble);
    conversation.appendChild(turn);
    conversation.scrollTop = conversation.scrollHeight;
    return turn;
  }

  function appendAssistantMeta(turn, { model, sources, latencyMs }) {
    if (model) {
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = `Modèle : ${model}${latencyMs != null ? ` · ${latencyMs} ms` : ""}`;
      turn.appendChild(meta);
    }
    if (sources && sources.length > 0) {
      const block = document.createElement("div");
      block.className = "sources";
      const title = document.createElement("div");
      title.textContent = "Sources :";
      block.appendChild(title);
      const list = document.createElement("ul");
      sources.forEach((source) => {
        const item = document.createElement("li");
        item.textContent = `document=${source.document_id} · chunk=${source.chunk_index} · similarité=${source.similarity.toFixed(3)}`;
        list.appendChild(item);
      });
      block.appendChild(list);
      turn.appendChild(block);
    }
  }

  async function sendMessage(message) {
    appendTurn({ role: "user", text: message });
    const pending = appendTurn({ role: "assistant", text: "ABFINI réfléchit…" });

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const body = await response.json();

      if (!response.ok) {
        pending.classList.add("error");
        pending.querySelector(".bubble").textContent = body.detail || `Erreur ABFINI (HTTP ${response.status})`;
        return;
      }

      pending.querySelector(".bubble").textContent = body.answer;
      appendAssistantMeta(pending, {
        model: body.model,
        sources: body.sources,
        latencyMs: body.latency_ms,
      });
    } catch (err) {
      pending.classList.add("error");
      pending.querySelector(".bubble").textContent = "Impossible de joindre l'API ABFINI.";
    }
  }

  composer.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    sendButton.disabled = true;
    sendMessage(message).finally(() => {
      sendButton.disabled = false;
      input.focus();
    });
  });

  refreshButton.addEventListener("click", refreshStatus);

  refreshStatus();
})();
