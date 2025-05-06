let socket = null;
let token = null;
let currentRecipient = null;

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
    document
      .getElementById("conversationListScreen")
      .classList.remove("hidden");

    loadConversationList(username);
  } else {
    document.getElementById("loginError").classList.remove("hidden");
  }
});

async function loadConversationList() {
  const conversationList = document.getElementById("conversationList");
  conversationList.innerHTML = "";

  const res = await fetch("http://localhost:8000/contacts", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      token: token,
    },
  });

  if (res.ok) {
    const data = await res.json();
    const contacts = data.contacts;

    if (contacts.length === 0) {
      const emptyMsg = document.createElement("li");
      emptyMsg.textContent = "Aucune conversation récente.";
      emptyMsg.className = "text-gray-500 text-center";
      conversationList.appendChild(emptyMsg);
      return;
    }

    contacts.forEach((user) => {
      const li = document.createElement("li");
      li.textContent = user;
      li.className = "p-2 bg-gray-100 rounded hover:bg-gray-200 cursor-pointer";
      li.addEventListener("click", () => openChatWith(user));
      conversationList.appendChild(li);
    });
  } else {
    console.error("Erreur lors du chargement des contacts.");
  }
}

function openChatWith(recipient) {
  currentRecipient = recipient;
  document.getElementById("conversationListScreen").classList.add("hidden");
  document.getElementById("chatScreen").classList.remove("hidden");
  document.getElementById(
    "chatHeader"
  ).textContent = `💬 Chat avec ${recipient}`;

  socket = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
  const messagesBox = document.getElementById("messages");
  messagesBox.innerHTML = "";

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

document.getElementById("sendBtn").addEventListener("click", () => {
  const msgInput = document.getElementById("messageInput");
  const message = msgInput.value.trim();
  if (message && socket && currentRecipient) {
    // Adiciona a mensagem enviada à tela imediatamente
    const messagesBox = document.getElementById("messages");
    const msg = document.createElement("div");
    msg.textContent = `Vous : ${message}`;
    msg.classList.add("text-right", "text-blue-600");
    messagesBox.appendChild(msg);
    messagesBox.scrollTop = messagesBox.scrollHeight;

    // Envia a mensagem ao servidor
    socket.send(JSON.stringify({ to: currentRecipient, message }));
    msgInput.value = "";
    loadConversationList(); // Atualiza a lista para incluir novo contato
  }
});

document.getElementById("backToListBtn").addEventListener("click", () => {
  if (socket) socket.close();
  document.getElementById("chatScreen").classList.add("hidden");
  document.getElementById("conversationListScreen").classList.remove("hidden");
});

const newChatBtn = document.getElementById("newChatBtn");
const newChatModal = document.getElementById("newChatModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const userSearchInput = document.getElementById("userSearchInput");
const userSearchList = document.getElementById("userSearchList");

newChatBtn.addEventListener("click", async () => {
  newChatModal.classList.remove("hidden");
  userSearchInput.value = "";
  await loadAllUsers();
});

closeModalBtn.addEventListener("click", () => {
  newChatModal.classList.add("hidden");
});

userSearchInput.addEventListener("input", () => {
  const query = userSearchInput.value.toLowerCase();
  const items = userSearchList.querySelectorAll("li");
  items.forEach((item) => {
    item.style.display = item.textContent.toLowerCase().includes(query)
      ? "block"
      : "none";
  });
});

async function loadAllUsers() {
  userSearchList.innerHTML = "";

  const res = await fetch("http://localhost:8000/users", {
    headers: { token: token },
  });

  if (res.ok) {
    const data = await res.json();
    data.users.forEach((user) => {
      const li = document.createElement("li");
      li.textContent = user;
      li.className = "p-2 bg-gray-100 rounded hover:bg-gray-200 cursor-pointer";
      li.addEventListener("click", () => {
        newChatModal.classList.add("hidden");
        openChatWith(user);
      });
      userSearchList.appendChild(li);
    });
  } else {
    const error = document.createElement("li");
    error.textContent = "Erreur lors du chargement des utilisateurs.";
    userSearchList.appendChild(error);
  }
}
