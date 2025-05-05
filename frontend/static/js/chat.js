let socket = null;

document.getElementById("sendBtn").addEventListener("click", () => {
  const msgInput = document.getElementById("messageInput");
  const message = msgInput.value.trim();
  if (message && socket) {
    socket.send(message);
    msgInput.value = "";
  }
});

document.getElementById("username").addEventListener("change", () => {
  const username = document.getElementById("username").value.trim();
  if (username) {
    // if (socket) socket.close();
    socket = new WebSocket(`ws://localhost:8000/ws/${username}`);
    const messagesBox = document.getElementById("messages");

    socket.onmessage = (event) => {
      const msg = document.createElement("div");
      msg.textContent = event.data;
      messagesBox.appendChild(msg);
      messagesBox.scrollTop = messagesBox.scrollHeight;
    };

    socket.onclose = () => {
      const msg = document.createElement("div");
      msg.textContent = "❌ Déconnecté du serveur.";
      msg.classList.add("text-red-500");
      messagesBox.appendChild(msg);
    };
  }
});
