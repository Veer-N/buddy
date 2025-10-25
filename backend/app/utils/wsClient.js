// buddy/backend/app/utils/wsClient.js

let ws = null;
let listeners = [];

export function connectWebSocket(onMessage) {
  const wsUrl = "ws://192.168.0.199:8000/ws"; // 🔧 Replace with your actual machine IP
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log("✅ WebSocket connected to Buddy backend");
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) onMessage(data);
      listeners.forEach((fn) => fn(data));
    } catch (e) {
      console.error("Invalid WS message", e);
    }
  };

  ws.onclose = () => {
    console.log("❌ WebSocket disconnected. Retrying in 3s...");
    setTimeout(() => connectWebSocket(onMessage), 3000);
  };

  ws.onerror = (err) => {
    console.error("⚠️ WebSocket error:", err.message);
  };
}

export function sendMessage(text, speaker = "user") {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ text, speaker }));
  } else {
    console.warn("WebSocket not ready, message dropped:", text);
  }
}

export function addListener(fn) {
  listeners.push(fn);
}

export function removeListener(fn) {
  listeners = listeners.filter((l) => l !== fn);
}
