const helpCopy = {
  storage:
    "SQLite is the default choice for single-node installs. Choose MariaDB if you expect heavier concurrency or multiple dashboards.",
  backups:
    "Backups are recommended for SQLite. Set a short interval for more safety and a retention window that matches your storage budget.",
  owner:
    "The owner account manages devices and configuration. Demo access is read-only and meant for sharing dashboards.",
};

const popup = document.getElementById("helpPopup");
const content = document.getElementById("helpContent");
const closeBtn = document.querySelector(".help-close");

function openHelp(key) {
  content.textContent = helpCopy[key] || "No help available for this section.";
  popup.hidden = false;
}

function closeHelp() {
  popup.hidden = true;
}

for (const btn of document.querySelectorAll(".help-button")) {
  btn.addEventListener("click", () => openHelp(btn.dataset.help));
}

closeBtn.addEventListener("click", closeHelp);
popup.addEventListener("click", (event) => {
  if (event.target === popup) {
    closeHelp();
  }
});
