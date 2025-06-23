// Animation boutons 3D
const buttons = document.querySelectorAll('button, .btn');
buttons.forEach(btn => {
  btn.addEventListener('mousedown', () => btn.classList.add('active'));
  btn.addEventListener('mouseup', () => btn.classList.remove('active'));
  btn.addEventListener('mouseleave', () => btn.classList.remove('active'));
});

// Notifications dynamiques (exemple)
function showNotification(msg) {
  const notif = document.createElement('div');
  notif.className = 'notif';
  notif.innerText = msg;
  document.body.appendChild(notif);
  setTimeout(() => notif.remove(), 4000);
}

// Exemple d'utilisation :
// showNotification('Bienvenue sur Fellahi !');

// --- Voice Command Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const voiceCommandBtn = document.getElementById('voice-command-btn');
    const voiceFeedback = document.getElementById('voice-feedback');
    const startIrrigationBtn = document.getElementById('start-irrigation-btn');
    const stopIrrigationBtn = document.getElementById('stop-irrigation-btn');

    // Manual Control Button Listeners
    if(startIrrigationBtn && stopIrrigationBtn) {
        startIrrigationBtn.addEventListener('click', () => {
            sendCommandToServer('start irrigation');
            showNotification("Commande de démarrage de l'irrigation envoyée.");
        });

        stopIrrigationBtn.addEventListener('click', () => {
            sendCommandToServer('stop irrigation');
            showNotification("Commande d'arrêt de l'irrigation envoyée.");
        });
    }

    if (voiceCommandBtn) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.lang = 'fr-FR'; // Set language to French

            recognition.onstart = () => {
                voiceFeedback.textContent = 'Écoute en cours...';
                voiceCommandBtn.disabled = true;
                voiceCommandBtn.innerHTML = '<i class="fa fa-microphone-slash"></i> Écoute...';
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript.toLowerCase().trim();
                voiceFeedback.textContent = `Vous avez dit : "${transcript}"`;
                handleVoiceCommand(transcript);
            };

            recognition.onerror = (event) => {
                voiceFeedback.textContent = `Erreur de reconnaissance : ${event.error}`;
            };

            recognition.onend = () => {
                voiceCommandBtn.disabled = false;
                voiceCommandBtn.innerHTML = '<i class="fa fa-microphone"></i> Activer';
            };

            voiceCommandBtn.addEventListener('click', () => {
                recognition.start();
            });

        } else {
            voiceFeedback.textContent = "Désolé, votre navigateur ne supporte pas la reconnaissance vocale.";
            voiceCommandBtn.disabled = true;
        }
    }

    function handleVoiceCommand(command) {
        let recognizedCmd = null;

        if (command.includes("démarre l'irrigation") || command.includes("commence l'irrigation") || command.includes("start irrigation")) {
            recognizedCmd = "start irrigation";
        } else if (command.includes("arrête l'irrigation") || command.includes("stop l'irrigation") || command.includes("stop irrigation")) {
            recognizedCmd = "stop irrigation";
        } else if (command.includes("vérifie le statut") || command.includes("quel est le statut") || command.includes("check status")) {
            recognizedCmd = "check status";
        }

        if (recognizedCmd) {
            voiceFeedback.textContent = `Commande reconnue : "${recognizedCmd}". Envoi au serveur...`;
            sendCommandToServer(recognizedCmd);
        } else {
            voiceFeedback.textContent = `Commande non reconnue. Essayez "démarre l'irrigation", "arrête l'irrigation", ou "vérifie le statut".`;
        }
    }

    function sendCommandToServer(command) {
        fetch('/voice-command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command: command }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                voiceFeedback.textContent = `Réponse du serveur : ${data.message}`;
                // Optionally show a persistent notification
                showNotification(data.message);
            } else {
                voiceFeedback.textContent = `Erreur : ${data.message}`;
            }
        })
        .catch(error => {
            console.error('Error sending voice command:', error);
            voiceFeedback.textContent = 'Erreur lors de la communication avec le serveur.';
        });
    }
});

// Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/service-worker.js')
      .then(reg => console.log('Service Worker registered:', reg))
      .catch(err => console.error('Service Worker registration failed:', err));
  });
}

// Universal Notification Function
function showNotification(message, isError = false) {
  const notificationElement = document.createElement('div');
  notificationElement.className = `notification ${isError ? 'error' : ''}`;
  notificationElement.textContent = message;
  
  document.body.appendChild(notificationElement);
  
  // Show notification
  setTimeout(() => {
    notificationElement.classList.add('show');
  }, 10);
  
  // Hide and remove after a few seconds
  setTimeout(() => {
    notificationElement.classList.remove('show');
    setTimeout(() => {
      document.body.removeChild(notificationElement);
    }, 500);
  }, 4000);
}

// Fade-in animation for .card elements
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.card').forEach((el, i) => {
    el.style.opacity = 0;
    setTimeout(() => {
      el.style.transition = 'opacity 0.7s cubic-bezier(.39,.575,.565,1.000), transform 0.5s ease-out';
      el.style.opacity = 1;
    }, 200 + i * 120);
  });
}); 