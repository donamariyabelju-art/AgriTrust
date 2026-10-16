/* AgriTrust Client Interactions (Vanilla JavaScript) */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const mobileToggle = document.getElementById('mobileMenuBtn');
  const navMenu = document.querySelector('.nav-menu');
  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
      navMenu.classList.toggle('active');
    });
  }

  // 2. Modal Helper Functions
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  };

  // Close modals when clicking backdrop
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
      }
    });
  });

  // 3. Image Upload Preview for Scanner and Products
  const imageInputs = document.querySelectorAll('input[type="file"][data-preview]');
  imageInputs.forEach(input => {
    input.addEventListener('change', (e) => {
      const file = e.target.files[0];
      const previewId = input.getAttribute('data-preview');
      const previewImg = document.getElementById(previewId);
      if (file && previewImg) {
        const reader = new FileReader();
        reader.onload = (re) => {
          previewImg.src = re.target.result;
          previewImg.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  });

  // 4. AgriTrust AI Chatbot Interactions
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const chatMessages = document.getElementById('chatMessages');

  if (chatForm && chatInput && chatMessages) {
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = chatInput.value.trim();
      if (!message) return;

      // Append user bubble
      appendChatBubble(message, 'user');
      chatInput.value = '';

      // Append temporary typing indicator
      const typingId = 'typing-' + Date.now();
      const typingBubble = document.createElement('div');
      typingBubble.className = 'chat-bubble bot';
      typingBubble.id = typingId;
      typingBubble.innerHTML = '<em>AgriTrust AI is analyzing agronomic knowledge...</em>';
      chatMessages.appendChild(typingBubble);
      chatMessages.scrollTop = chatMessages.scrollHeight;

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        
        // Remove typing indicator
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        if (data.reply) {
          appendChatBubble(data.reply, 'bot');
        } else {
          appendChatBubble('Sorry, could not process request right now. Please try again.', 'bot');
        }
      } catch (err) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        appendChatBubble('Connection error. Please check your network and try again.', 'bot');
      }
    });

    // Pill prompt shortcuts
    document.querySelectorAll('.pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        chatInput.value = btn.innerText;
        chatForm.dispatchEvent(new Event('submit'));
      });
    });
  }

  function appendChatBubble(text, sender) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    // Simple markdown-to-HTML parser for bold, lists, and line breaks
    let formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
    bubble.innerHTML = formatted;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
});
