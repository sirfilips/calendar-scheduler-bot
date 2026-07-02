# Senate Meeting Scheduler Bot

A **Telegram bot** designed to streamline the scheduling, management, and notification of Senate meetings. It allows administrators to create new sessions, users to view upcoming meetings, and creators to delete their own scheduled sessions.

---

## ✨ **Features**

### **Meeting Management**

- **Create New Sessions**: Administrators can schedule new Senate meetings with a title, date, and time.
- **Delete Sessions**: Only the creator of a session can delete it, ensuring accountability.
- **View Calendar**: Users can see upcoming meetings for their groups, with privacy controls to ensure they only see relevant events.

### **Automated Notifications**

- **Automatic Reminders**: The bot sends a notification to the group when a scheduled meeting starts.

### **Privacy & Access Control**

- **Group-Specific Access**: Users in private chats can only view meetings from groups they are members of.
- **Admin-Only Commands**: Certain commands (e.g., `/nuovaseduta`) are restricted to group administrators.
- **Creator-Only Deletion**: Only the user who created a session can delete it.

### **User Experience**

- **Private Scheduling**: Admins can schedule meetings in private chats to avoid cluttering the group.
- **Interactive Menus**: Inline keyboard buttons for seamless navigation.
- **Command Menu**: A customizable command menu for easy access to bot features.

---

## 📌 **Commands**


| Command          | Description                                                       | Access Level                         |
| ---------------- | ----------------------------------------------------------------- | ------------------------------------ |
| `/start`         | Shows a welcome message or initiates registration for scheduling. | Public                               |
| `/calendario`    | Displays the upcoming Senate meetings.                            | Public (restricted to group members) |
| `/nuovaseduta`   | Starts the process to schedule a new meeting.                     | Admin Only                           |
| `/eliminaseduta` | Initiates the deletion of a meeting created by the user.          | Creator Only                         |
| `/annulla`       | Cancels an ongoing operation.                                     | Public                               |


---

## 🛠 **Installation & Setup**

### **Prerequisites**

- Python **3.7 or higher**
- `python-telegram-bot` library (version **20.x or higher**)
- A **Telegram Bot Token** (obtainable from [@BotFather](https://t.me/BotFather))

### **Steps**

1. **Clone the Repository** (or download the script):
  ```bash
   git clone https://github.com/sirfilips/calendar-scheduler-bot
   cd senate-bot
  ```
2. **Install Dependencies**:
  ```bash
   pip install python-telegram-bot
  ```
3. **Configure the Bot Token**:
  - Open `senato_bot.py` in a text editor.
  - Replace the placeholder token with your **Telegram Bot Token**:
    ```python
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    ```
4. **Run the Bot**:
  ```bash
   python senato_bot.py
  ```
5. **Add the Bot to Your Group**:
  - Invite the bot to your Telegram group.
  - Ensure the bot has **administrator privileges** to manage meetings effectively.

---

## 🚀 **Usage**

### **Scheduling a New Meeting (Admin Only)**

1. In the group chat, type `/nuovaseduta`.
2. The bot will send a private link to schedule the meeting.
3. Click the link to open a private chat with the bot.
4. Follow the prompts to:
  - Enter the **meeting title** (e.g., "Budget Discussion").
  - Enter the **date and time** in the format `DD/MM/YYYY HH:MM` (e.g., `25/10/2026 21:30`).
5. The meeting will be scheduled, and a confirmation message will be sent.

### **Viewing the Calendar**

- In a **group chat**, type `/calendario` to see upcoming meetings for that group.
- In a **private chat**, type `/calendario` to see meetings from all groups you are a member of.

### **Deleting a Meeting (Creator Only)**

1. Type `/eliminaseduta` in the group or private chat.
2. The bot will list all meetings you created.
3. Reply with the **number** of the meeting you want to delete.
4. The meeting will be removed, and a confirmation message will be sent.

---

## 🔧 **Configuration**

### **Time Zone**

The bot uses the **Europe/Rome** time zone by default. To change it:

```python
TIMEZONE = ZoneInfo("Your/Timezone")  # e.g., "America/New_York"
```

### **Logging**

The bot logs activities to the console. To adjust the logging level:

```python
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO  # Change to DEBUG for more details
)
```

### **Customizing Commands**

To modify the bot's command menu, edit the `imposta_menu_comandi` function:

```python
comandi = [
    BotCommand("start", "Welcome message or start registration"),
    BotCommand("calendario", "View upcoming meetings"),
    # Add or modify commands here
]
```

---

## 📂 **Project Structure**

```
senato_bot.py    # Main bot script
README.md        # This file
```

---

## 🤖 **Technologies Used**

- **Language**: Python 3.7+
- **Library**: [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- **Features**:
  - Asynchronous programming with `asyncio`
  - Job Queue for scheduled notifications
  - Conversation Handlers for multi-step interactions
  - Inline Keyboards for interactive menus

---

## 📜 **License**

This project is **open-source** and available for free use. Feel free to modify and distribute it as needed.

---

## 🙌 **Contributing**

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a clear description of your changes.

---

## 📬 **Contact & Support**

For questions or issues, please open an issue in the repository or contact the maintainer directly.

---

🔹 **Happy Scheduling!** 🔹
