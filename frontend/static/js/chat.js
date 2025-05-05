let socket = null;
let token = null;

document.getElementById("loginBtn").addEventListener("click", async () => {
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;

  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const res = await fetch("http://localhost:8000/login", {
    method: "POST",
    body: formData,
  });

  if (res.ok) {
    const data = await res.json();
    token = data.token;
    document.getElementById("loginScreen").classList.add("hidden");
    document.getElementById("chatScreen").classList.remove("hidden");

    socket = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
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
  } else {
    document.getElementById("loginError").classList.remove("hidden");
  }
});

document.getElementById("sendBtn").addEventListener("click", () => {
  const msgInput = document.getElementById("messageInput");
  const message = msgInput.value.trim();
  if (message && socket) {
    socket.send(message);
    msgInput.value = "";
  }
});
