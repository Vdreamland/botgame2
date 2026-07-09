const socket = new WebSocket("ws://localhost:8080");
const tabsContainer = document.getElementById("tabs");
const logsArea = document.getElementById("logs-area");

const botsData = {};
let activeBot = null;

function createBotTab(botName) {
  const tabButton = document.createElement("button");
  tabButton.className = "tab-button";
  tabButton.innerText = botName;
  tabButton.onclick = () => switchTab(botName);
  tabsContainer.appendChild(tabButton);

  const botViewport = document.createElement("div");
  botViewport.className = "logs-viewport";
  botViewport.id = `logs-${botName}`;
  logsArea.appendChild(botViewport);

  botsData[botName] = {
    button: tabButton,
    viewport: botViewport,
    currentTurnCard: null,
    detailList: null,
  };

  if (!activeBot) {
    switchTab(botName);
  }
}

function switchTab(botName) {
  if (activeBot && botsData[activeBot]) {
    botsData[activeBot].button.classList.remove("active");
    botsData[activeBot].viewport.classList.remove("active");
  }
  activeBot = botName;
  if (botsData[botName]) {
    botsData[botName].button.classList.add("active");
    botsData[botName].viewport.classList.add("active");
  }
}

socket.onmessage = function (event) {
  const payload = JSON.parse(event.data);
  const botName = payload.bot_name;

  if (!botName) return;

  if (!botsData[botName]) {
    createBotTab(botName);
  }

  const data = botsData[botName];
  const viewport = data.viewport;

  if (payload.type === "turn") {
    const card = document.createElement("div");
    card.className = "turn-card";

    const header = document.createElement("div");
    header.className = "turn-header";
    header.innerText = `Turn ${payload.turn}`;

    const status = document.createElement("div");
    status.className = "turn-status";
    status.innerText = `Status: ${payload.status}`;

    const detailList = document.createElement("div");
    detailList.className = "detail-logs-list";

    card.appendChild(header);
    card.appendChild(status);
    card.appendChild(detailList);

    viewport.appendChild(card);
    viewport.scrollTop = viewport.scrollHeight;

    data.currentTurnCard = card;
    data.detailList = detailList;
  } else if (payload.type === "detail") {
    if (data.detailList) {
      const item = document.createElement("div");
      item.className = "detail-log-item";
      item.innerText = payload.message;
      data.detailList.appendChild(item);
      viewport.scrollTop = viewport.scrollHeight;
    }
  } else if (payload.type === "waiting") {
    const item = document.createElement("div");
    item.className = "system-message";
    item.innerText = `[Turn ${payload.turn}] Waiting for other agents...`;
    viewport.appendChild(item);
    viewport.scrollTop = viewport.scrollHeight;
  } else if (payload.type === "ended") {
    const item = document.createElement("div");
    item.className = "system-message";
    item.innerText = "Game has ended.";
    viewport.appendChild(item);
    viewport.scrollTop = viewport.scrollHeight;
  } else if (payload.type === "finished") {
    const item = document.createElement("div");
    item.className = "system-message";
    item.innerText = `Game finished. Status: ${payload.status}`;
    viewport.appendChild(item);
    viewport.scrollTop = viewport.scrollHeight;
  } else if (payload.type === "reenter") {
    const item = document.createElement("div");
    item.className = "system-message";
    item.innerText = "Gameplay frames detected. Re-entering active loop.";
    viewport.appendChild(item);
    viewport.scrollTop = viewport.scrollHeight;
  }
};
