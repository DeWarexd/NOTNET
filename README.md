# Advanced Discord RAT (ADR) 🐍💬

<p align="center">
  <img src="https://raw.githubusercontent.com/DeWarexd/NOTNET/refs/heads/main/standard.gif" alt="ADR Demo Animation" width="400"/> 
  <br/>
  <b>A feature-rich Remote Administration Tool controlled via Discord, written in Python.</b>
  <br/>
  <br/>
  ⚠️ Intended Strictly for Educational & Ethical Security Research Purposes Only! ⚠️
</p>

---

## 🚨 **EXTREMELY IMPORTANT DISCLAIMER** 🚨

This project is developed **solely for educational purposes** to demonstrate concepts in Python programming, network communication (via Discord API), system interaction, and potential security vulnerabilities.

**‼️ UNAUTHORIZED ACCESS TO ANY COMPUTER SYSTEM IS ILLEGAL AND UNETHICAL ‼️**

*   **DO NOT** use this software on any computer system you do not have explicit, written permission to test.
*   The author(s) of this project assume **NO liability** and are **NOT responsible** for any misuse or damage caused by this program.
*   **YOU** are solely responsible for your actions and any legal consequences that may arise from using this tool improperly.
*   By downloading, cloning, or using this software, you agree that you understand the risks and will use it only in a lawful and ethical manner (e.g., testing on your own systems or systems you have clear authorization for).

**If you intend to use this tool for malicious purposes, STOP NOW and leave this repository.**

---

## ✨ Features

This RAT provides a range of functionalities controllable via simple Discord commands:

*   **💻 Interactive Shell:** (`/shell`) Get a fully interactive command prompt/terminal session on the target machine directly within a Discord channel. (`exit` to close).
*   **⚙️ Single Command Execution:** (`/cmd [command]`) Execute single commands remotely without starting a full shell.
*   **🖥️ System Information:** (`/sysinfo`) Gather detailed information about the target system (OS, Arch, CPU, RAM, Disk, IP, MAC, Uptime, User, Hostname).
*   **📸 Screenshot:** (`/screenshot`) Capture the target's screen and send it back to Discord.
*   **📂 File System Operations:**
    *   **📥 Download:** (`/download [file_path]`) Download files from the target machine.
    *   **📤 Upload:** (`/upload [URL] [target_path]`) Upload files from a direct URL to the target machine.
*   **🌐 Browser Control:** (`/browser [URL or Search Query]`) Open a URL or perform a Google search in the target's default browser.
*   **💬 Message Box:** (`/msgbox '[Title]' '[Message Text]'`) Display a native Windows message box on the target machine (Requires quotes for multi-word title/text).
*   **📈 Process Management:**
    *   **List Processes:** (`/listproc`) View currently running processes with PID, username, and name.
    *   **Kill Process:** (`/kill [PID or Process Name]`) Terminate specific processes.
*   **🌍 Network Information:** (`/getip`) Fetch the target machine's public IP address.
*   **🔒 Persistence (Windows Only):** Automatically copies itself to `%APPDATA%` and adds a registry key (`HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`) to run on startup.
*   **👻 Stealth (Windows Only):** Hides the running script/executable file (`.exe`, `.pyw`) using file attributes.
*   **🚀 Responsive:** Uses asynchronous programming (`discord.py`) for better responsiveness.
*   **📊 Status & Help:**
    *   ` /ping`: Check bot latency.
    *   ` /help`: Display the available commands.
*   **📄 Logging:** Provides console logging for debugging and tracking actions.

---

## 📋 Prerequisites

*   **Target Machine (Victim):**
    *   <img src="https://img.shields.io/badge/-Windows-blue?logo=windows" alt="Windows"> (Recommended for full features like Persistence, Stealth, MsgBox) or Linux/macOS (basic functionality).
    *   <img src="https://img.shields.io/badge/-Python_3.x-blue?logo=python" alt="Python 3"> Installed (if running the `.py` script directly).
    *   Stable Internet Connection.
*   **Controller Machine (Attacker):**
    *   A Discord Account.
    *   A Discord Server/Channel where you have control and can add the bot.
    *   A Discord Bot Token.

---

## 📦 Installation & Setup
1.  **Install Dependencies:**
    Create a `requirements.txt` file with the following content:
    ```txt
    discord.py>=2.0.0
    requests
    Pillow
    psutil
    ```
    Then run:
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure you have Python 3 and Pip installed)*

2.  **Create a Discord Bot:**
    *   Go to the [Discord Developer Portal](https://discord.com/developers/applications).
    *   Create a "New Application".
    *   Go to the "Bot" tab.
    *   Click "Add Bot".
    *   **Crucially:** Under "Privileged Gateway Intents", enable the **"Message Content Intent"**. Without this, the bot cannot read commands!
    *   Copy the Bot Token (Click "Reset Token" if needed, and copy the new one immediately). **Keep this token secure!**

3.  **Configure the Script:**
    *   Open the `notnet.py` (or your main script file) in a text editor.
    *   Find the `TOKEN` variable near the top:
      ```python
      TOKEN: str = 'ENTER_TOKEN_HERE' # 🔴 PASTE YOUR TOKEN!
      ```
    *   Replace `'ENTER_TOKEN_HERE'` with the actual token you copied.
    *   *(Optional)* You can also change the `PREFIX` (default is `/`) or `DEFAULT_PERSISTENCE_FILENAME` if desired.

4.  **Add Bot to Your Server:**
    *   Go back to the Discord Developer Portal -> Your Application -> "OAuth2" -> "URL Generator".
    *   Select the `bot` scope.
    *   Under "Bot Permissions", select `Administrator` (easiest way) or individually select necessary permissions (Send Messages, Read Message History, Embed Links, Attach Files, etc.). **Administrator is required for full functionality without manually checking every needed permission.**
    *   Copy the generated URL and paste it into your browser.
    *   Select the Discord server where you want to control the RAT from and authorize the bot.

---

## ▶️ Usage

1.  **Deploy on Target:**
    *   Transfer the configured `notnet.py` script (and `requirements.txt` if Python isn't pre-installed with these libs) or a compiled `.exe` (using tools like PyInstaller) to the target machine.
    *   **Reminder:** ONLY do this on machines you have EXPLICIT permission to test.
2.  **Run on Target:**
    *   Execute the script/executable on the target machine.
      *   If running the script: `python notnet.py`
      *   If running an executable: Double-click `rests.exe` (or however you compiled it).
    *   If running on Windows, it will attempt to hide itself and set up persistence.
3.  **Control via Discord:**
    *   Go to the Discord channel where you added the bot.
    *   Type commands starting with the defined `PREFIX` (default `/`).
    *   Example:
      ```
      /help        # Show help menu
      /sysinfo     # Get system info
      /screenshot  # Get screenshot
      /shell       # Start interactive shell
      ```

---

## 🛡️ Persistence & Stealth (Windows Only)

*   **Persistence:** The script copies itself to `%APPDATA%\{DEFAULT_PERSISTENCE_FILENAME}` and creates a registry entry in `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`. This makes the script run automatically every time the user logs in.
*   **Stealth:** The script attempts to set the 'Hidden' file attribute on both the original executable (if applicable) and the copy in `%APPDATA%` to make them less visible in File Explorer (if default settings are used).

---

## ⚖️ Ethical Considerations & Liability

Once again, this tool is **powerful** and designed for **educational demonstration only**.
Misusing this tool can lead to severe legal consequences, including hefty fines and imprisonment.

*   Respect privacy and the law.
*   Never deploy or use this tool on systems without clear, unambiguous authorization.
*   The developers provide this code "as-is" without warranty of any kind, express or implied.
*   You assume all responsibility for how you use this software.

---

**By using this software, you acknowledge and agree to these terms and warnings.**
