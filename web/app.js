const socketUrl = "ws://127.0.0.1:8080";
let socket;
let agentsData = {};
let activeAgent = null;
let botSearchQuery = "";

function connect() {
  socket = new WebSocket(socketUrl);

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const botName = msg.bot_name;
    if (!botName) return;

    if (!agentsData[botName]) {
      agentsData[botName] = {
        turns: [],
        credits: 0,
        status: "lobby",
        gameId: null,
        entryType: "free",
        isAlive: true,
      };
      updateTabs();
      updateGlobalStats();
      if (!activeAgent) {
        switchAgent(botName);
      }
    }

    const agent = agentsData[botName];

    if (msg.type === "status_update") {
      agent.status = msg.status;
      agent.credits = msg.credits;
      agent.gameId = msg.game_id || agent.gameId;
      agent.entryType = msg.entry_type || agent.entryType;
      if (msg.is_alive !== undefined) {
        agent.isAlive = msg.is_alive;
      }
      updateTabs();
      updateGlobalStats();
    } else if (msg.type === "turn") {
      const turnNum = msg.turn;
      const turnStatus = msg.status;
      agent.gameId = msg.game_id || agent.gameId;

      let turnObj = agent.turns.find((t) => t.turn === turnNum);
      if (!turnObj) {
        turnObj = {
          turn: turnNum,
          status: turnStatus,
          logs: [],
        };
        agent.turns.push(turnObj);
      } else {
        turnObj.status = turnStatus;
      }

      if (activeAgent === botName) {
        renderLogs();
      }
    } else if (msg.type === "waiting") {
      const turnNum = msg.turn;
      let turnObj = agent.turns.find((t) => t.turn === turnNum);
      if (!turnObj) {
        turnObj = {
          turn: turnNum,
          status: "waiting",
          logs: [],
        };
        agent.turns.push(turnObj);
      } else {
        turnObj.status = "waiting";
      }
      if (activeAgent === botName) {
        renderLogs();
      }
    } else if (msg.type === "detail") {
      if (agent.turns.length === 0) {
        agent.turns.push({
          turn: 1,
          status: "running",
          logs: [],
        });
      }
      const currentTurn = agent.turns[agent.turns.length - 1];
      currentTurn.logs.push(msg.message);

      if (activeAgent === botName) {
        renderLogs();
      }
    }

    updateTabs();
  };

  socket.onclose = () => {
    setTimeout(connect, 3000);
  };
}

function updateGlobalStats() {
  const totalBotsElem = document.getElementById("total-bots");
  const totalSmoltzElem = document.getElementById("total-smoltz");
  const botsPlayingElem = document.getElementById("bots-playing");
  const botsAliveElem = document.getElementById("bots-alive");
  const botsMatchingElem = document.getElementById("bots-matching");
  const botsLobbyElem = document.getElementById("bots-lobby");
  const botsDeadElem = document.getElementById("bots-dead");
  const botsFreeElem = document.getElementById("bots-free");
  const botsPaidElem = document.getElementById("bots-paid");

  const botNames = Object.keys(agentsData);
  let totalSmoltz = 0;
  let playingCount = 0;
  let aliveCount = 0;
  let matchingCount = 0;
  let lobbyCount = 0;
  let deadCount = 0;
  let freeCount = 0;
  let paidCount = 0;

  botNames.forEach((name) => {
    const agent = agentsData[name];
    totalSmoltz += agent.credits || 0;

    if (agent.status === "playing") {
      playingCount++;
      if (agent.isAlive) {
        aliveCount++;
      } else {
        deadCount++;
      }

      if (agent.entryType === "paid") {
        paidCount++;
      } else {
        freeCount++;
      }
    } else if (agent.status === "matchmaking") {
      matchingCount++;
    } else if (agent.status === "lobby") {
      lobbyCount++;
    } else if (agent.status === "dead") {
      deadCount++;
    }
  });

  if (totalBotsElem) totalBotsElem.textContent = botNames.length;
  if (totalSmoltzElem)
    totalSmoltzElem.textContent = totalSmoltz.toLocaleString();

  if (botsPlayingElem) botsPlayingElem.textContent = playingCount;
  if (botsAliveElem) botsAliveElem.textContent = aliveCount;
  if (botsMatchingElem) botsMatchingElem.textContent = matchingCount;
  if (botsLobbyElem) botsLobbyElem.textContent = lobbyCount;
  if (botsDeadElem) botsDeadElem.textContent = deadCount;
  if (botsFreeElem) botsFreeElem.textContent = freeCount;
  if (botsPaidElem) botsPaidElem.textContent = paidCount;
}

function updateTabs() {
  const tabsContainer = document.getElementById("tabs");
  if (!tabsContainer) return;
  tabsContainer.innerHTML = "";

  Object.keys(agentsData)
    .filter((name) => name.toLowerCase().includes(botSearchQuery.toLowerCase()))
    .forEach((botName) => {
      const agent = agentsData[botName];
      const btn = document.createElement("button");
      btn.className = "tab-button";
      if (botName === activeAgent) {
        btn.className += " active";
      }

      const nameSpan = document.createElement("span");
      nameSpan.className = "tab-bot-name";
      nameSpan.textContent = botName;

      const metaDiv = document.createElement("div");
      metaDiv.className = "tab-bot-meta";

      const sMoltzVal = (agent.credits || 0).toLocaleString();
      const entryLabel = agent.entryType
        ? ` (${agent.entryType.toUpperCase()})`
        : "";

      let statusText = agent.status.toUpperCase();
      let statusClass = agent.status;
      if (agent.status === "playing" && !agent.isAlive) {
        statusText = "DEAD";
        statusClass = "dead";
      }

      let metaHTML = `sMoltz: ${sMoltzVal} | <span class="status-${statusClass}">${statusText}${entryLabel}</span>`;

      if (agent.gameId && agent.status === "playing") {
        metaHTML += ` | <a class="spectate-link" href="https://www.clawroyale.ai/games/spect/${agent.gameId}" target="_blank">SPECTATE ↗</a>`;
      }
      metaDiv.innerHTML = metaHTML;

      const linkElement = metaDiv.querySelector(".spectate-link");
      if (linkElement) {
        linkElement.onclick = (e) => e.stopPropagation();
      }

      btn.appendChild(nameSpan);
      btn.appendChild(metaDiv);

      btn.onclick = () => switchAgent(botName);
      tabsContainer.appendChild(btn);
    });
}

function switchAgent(botName) {
  activeAgent = botName;
  updateTabs();
  renderLogs();
}

function renderLogs() {
  const container = document.getElementById("log-cards-container");
  const placeholder = document.getElementById("placeholder");
  const viewport = document.getElementById("viewport");
  const header = document.getElementById("viewport-header");
  const title = document.getElementById("viewport-title");
  if (!container) return;

  container.innerHTML = "";

  if (!activeAgent || !agentsData[activeAgent]) {
    if (placeholder) placeholder.style.display = "block";
    if (header) header.style.display = "none";
    return;
  }

  const agent = agentsData[activeAgent];
  if (agent.turns.length === 0) {
    if (placeholder) {
      placeholder.style.display = "block";
      placeholder.textContent = "No turns recorded yet...";
    }
    if (header) header.style.display = "none";
    return;
  }

  if (placeholder) placeholder.style.display = "none";
  if (header) {
    header.style.display = "flex";
    if (title) title.textContent = activeAgent + " Logs";
  }

  const sortedTurns = [...agent.turns].sort((a, b) => a.turn - b.turn);

  sortedTurns.forEach((t) => {
    const card = document.createElement("div");
    card.className = "turn-card";

    const cardHeader = document.createElement("div");
    cardHeader.className = "turn-header";

    const cardTitle = document.createElement("h4");
    cardTitle.className = "turn-title";
    cardTitle.textContent = "Turn " + t.turn;

    const statusLabel = document.createElement("span");
    statusLabel.className = "turn-status";
    if (t.status === "finished") {
      statusLabel.className += " finished";
    }
    statusLabel.textContent = t.status;

    cardHeader.appendChild(cardTitle);
    cardHeader.appendChild(statusLabel);
    card.appendChild(cardHeader);

    if (t.logs && t.logs.length > 0) {
      const list = document.createElement("ul");
      list.className = "detail-list";
      t.logs.forEach((logText) => {
        const item = document.createElement("li");
        item.className = "detail-item";
        let formattedText = logText
          .replace(/\[SafeZone\]/g, '<span class="zone-safe">[SafeZone]</span>')
          .replace(
            /\[DeadZone\]/g,
            '<span class="zone-dead">[DeadZone]</span>',
          );
        item.innerHTML = formattedText;
        list.appendChild(item);
      });
      card.appendChild(list);
    }

    container.appendChild(card);
  });

  const autoScrollChk = document.getElementById("autoscroll");
  if (autoScrollChk && autoScrollChk.checked && viewport) {
    viewport.scrollTop = viewport.scrollHeight;
  }
}

document.getElementById("copy-logs-btn").onclick = () => {
  if (!activeAgent || !agentsData[activeAgent]) return;
  const agent = agentsData[activeAgent];
  if (agent.turns.length === 0) return;

  const sortedTurns = [...agent.turns].sort((a, b) => a.turn - b.turn);
  let copyText = `${activeAgent} GAME LOGS\n`;
  copyText += `=======================\n`;

  const turnBlocks = sortedTurns.map((t) => {
    let block = `Turn ${t.turn}`;
    if (t.logs && t.logs.length > 0) {
      const filteredLogs = t.logs.filter((line) => !line.includes("---"));
      if (filteredLogs.length > 0) {
        block += "\n" + filteredLogs.join("\n");
      }
    }
    return block;
  });

  copyText += turnBlocks.join("\n\n") + "\n";

  navigator.clipboard.writeText(copyText).then(() => {
    const btn = document.getElementById("copy-logs-btn");
    const oldText = btn.textContent;
    btn.textContent = "COPIED!";
    btn.style.borderColor = "var(--success)";
    btn.style.color = "var(--success)";
    setTimeout(() => {
      btn.textContent = oldText;
      btn.style.borderColor = "";
      btn.style.color = "";
    }, 2000);
  });
};

document.getElementById("search-bot").oninput = (e) => {
  botSearchQuery = e.target.value;
  updateTabs();
};

window.onload = connect;
