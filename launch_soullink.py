import os
import sys
import json
import time
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

IS_MAC = (sys.platform == "darwin")
IS_WIN = (sys.platform == "win32")

try:
    if IS_WIN:
        import pygetwindow as gw
    else:
        gw = None
except Exception:
    gw = None

BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

if IS_MAC:
    APP_DATA_DIR = os.path.expanduser("~/Library/Application Support/SoulLinkHub")
elif getattr(sys, "frozen", False):
    APP_DATA_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DATA_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(APP_DATA_DIR, exist_ok=True)
PROFILES_DIR = os.path.join(APP_DATA_DIR, "profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)
PROFILES_FILE = os.path.join(PROFILES_DIR, "profiles.json")


def sanitize_filename(name):
    cleaned = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name.strip())
    return cleaned.strip("_") or "Default_Run"


def resolve_mgba_binary(path):
    if not path:
        return ""
    path = os.path.normpath(path.strip())
    if IS_MAC and path.endswith(".app"):
        inner = os.path.join(path, "Contents", "MacOS", "mGBA")
        if os.path.exists(inner):
            return inner
    return path


def ensure_save_directory(save_path, rom_path):
    """Ensure mGBA gets a directory and migrate a legacy single .sav file."""
    save_path = os.path.abspath(os.path.expanduser(os.path.normpath(save_path)))
    if os.path.isfile(save_path):
        migrated_dir = save_path + "_files"
        os.makedirs(migrated_dir, exist_ok=True)
        rom_stem = os.path.splitext(os.path.basename(rom_path))[0]
        target = os.path.join(migrated_dir, rom_stem + ".sav")
        if not os.path.exists(target):
            shutil.move(save_path, target)
        save_path = migrated_dir
    else:
        os.makedirs(save_path, exist_ok=True)
    return save_path


def prepare_instance_script(lua_script, save_dir):
    """Copy the Lua script into a save folder so its Poke Ball file stays there.

    Returns the copy's path, or the original script if the copy cannot be made.
    """
    try:
        with open(lua_script, "rb") as f:
            source = f.read()
        marker = b"local SAVE_DIR = nil"
        if marker not in source:
            return lua_script
        folder = os.path.abspath(save_dir).replace("\\", "/")
        line = b"local SAVE_DIR = [==[" + folder.encode("utf-8") + b"]==]"
        target = os.path.join(save_dir, "soullink_p1.lua")
        with open(target, "wb") as f:
            f.write(source.replace(marker, line, 1))
        # Carry over unlocks written next to the script by the previous version.
        old = os.path.join(os.path.dirname(lua_script), "soullink_balls_p1.txt")
        new = os.path.join(save_dir, "soullink_balls_p1.txt")
        if os.path.isfile(old) and not os.path.exists(new):
            shutil.copyfile(old, new)
        return os.path.normpath(target)
    except OSError:
        return lua_script


def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("mgba_exe", "")
                    data.setdefault("runs", {})
                    return data
        except Exception:
            pass
    return {"mgba_exe": "", "runs": {}}


def save_profiles(data):
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
def get_window_dpi_scale(hwnd):
    if not IS_WIN or not hwnd:
        return 1.0
    try:
        import ctypes
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
        return (dpi / 96.0) if dpi else 1.0
    except Exception:
        return 1.0


def load_lua_mac(lua_script):
    try:
        subprocess.run(["pbcopy"], input=lua_script.encode("utf-8"), check=False)
    except Exception:
        pass
    applescript = '''
    tell application "mGBA" to activate
    delay 0.6
    tell application "System Events"
        tell process "mGBA"
            click menu item "Scripting..." of menu "Tools" of menu bar 1
            delay 0.7
            click menu item "Load script..." of menu "File" of menu bar 1
            delay 0.7
            keystroke "g" using {command down, shift down}
            delay 0.5
            keystroke "v" using {command down}
            delay 0.3
            keystroke return
            delay 0.5
            keystroke return
            delay 0.5
            if exists window "Scripting" then
                try
                    perform action "AXPress" of (first button of window "Scripting" whose subrole is "AXCloseButton")
                on error
                    keystroke "w" using {command down}
                end try
            end if
        end tell
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", applescript], check=False)
    except Exception:
        pass


def get_mgba_down_key():
    if not IS_WIN:
        return "down"
    try:
        import configparser
        cfg_path = os.path.join(os.environ.get("APPDATA", ""), "mGBA", "config.ini")
        if os.path.exists(cfg_path):
            cp = configparser.ConfigParser(strict=False)
            cp.read(cfg_path, encoding="utf-8")
            for sec in ("gba.input.QT_K", "gb.input.QT_K", "input.QT_K"):
                if cp.has_option(sec, "keyDown"):
                    raw = cp.get(sec, "keyDown").strip()
                    if raw.isdigit():
                        code = int(raw)
                        if 32 <= code <= 126:
                            return chr(code).lower()
                        qt_special = {
                            16777234: "left",
                            16777235: "up",
                            16777236: "right",
                            16777237: "down"
                        }
                        if code in qt_special:
                            return qt_special[code]
    except Exception:
        pass
    return "down"


def load_lua_into_mgba(win, lua_script):
    if IS_MAC:
        load_lua_mac(lua_script)
        return
    try:
        import pyautogui
        import ctypes
        import threading
        
        pyautogui.FAILSAFE = False
        user32 = ctypes.windll.user32
        
        # Shared flag to track if automation completed successfully
        completed = [False]

        # Background watchdog thread to force-unblock after 10 seconds if it hangs
        def safety_watchdog():
            time.sleep(10)
            if not completed[0]:
                try:
                    user32.BlockInput(False)
                except Exception:
                    pass

        watchdog_thread = threading.Thread(target=safety_watchdog, daemon=True)
        watchdog_thread.start()

        # Block user input
        user32.BlockInput(True)
        
        try:
            subprocess.run(["clip"], input=lua_script.encode("utf-16le"), check=False)

            win.activate()
            time.sleep(0.35)
            pyautogui.hotkey("alt", "t")
            time.sleep(0.25)
            pyautogui.press("s")
            time.sleep(0.1)
            for _ in range(4):
                pyautogui.press("down")
                time.sleep(0.08)
            pyautogui.press("enter")
            time.sleep(0.6)

            script_wins = [w for w in gw.getAllWindows() if "Scripting" in w.title]
            if script_wins:
                sw = next(iter(script_wins))
                sw.activate()
                time.sleep(0.25)

                scale = get_window_dpi_scale(getattr(sw, "_hWnd", None))
                pyautogui.click(int(sw.left + round(22 * scale)), int(sw.top + round(42 * scale)))
                time.sleep(0.25)
                pyautogui.click(int(sw.left + round(45 * scale)), int(sw.top + round(68 * scale)))

                dlg = None
                for _ in range(25):
                    time.sleep(0.2)
                    dlg_wins = [w for w in gw.getAllWindows() if "Select script" in w.title or "Load script" in w.title or w.title == "Open"]
                    if dlg_wins:
                        dlg = next(iter(dlg_wins))
                        break

                if dlg:
                    dlg.activate()
                    time.sleep(0.35)
                    pyautogui.click(int(dlg.left + dlg.width * 0.5), int(dlg.top + dlg.height - round(52 * scale)))
                    time.sleep(0.2)

                pyautogui.hotkey("ctrl", "a")
                time.sleep(0.1)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.25)
                pyautogui.press("enter")
                time.sleep(0.5)
                sw.close()
                time.sleep(0.25)
            
            # Mark as completed so the watchdog knows everything went fine
            completed[0] = True
        finally:
            # Always ensure input is unblocked
            user32.BlockInput(False)
            pyautogui.FAILSAFE = True
    except Exception:
        pass


def _window_pid(win):
    """Return the owning process ID for a pygetwindow window (Windows)."""
    if not IS_WIN:
        return None
    try:
        import ctypes
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(
            int(getattr(win, "_hWnd", 0)), ctypes.byref(pid)
        )
        return int(pid.value) or None
    except Exception:
        return None


def position_windows(expected_mgba_count=2, mgba_pids=None):
    if IS_MAC:
        hub_w = 580
        applescript = f"""
        tell application "Finder"
            set screen_bounds to bounds of window of desktop
            set sw to item 3 of screen_bounds
            set sh to item 4 of screen_bounds
        end tell
        set top_y to 28
        tell application "System Events"
            if exists process "mGBA" then
                tell process "mGBA"
                    set game_wins to (every window whose name is not "Scripting")
                    set win_count to count of game_wins
                    if {expected_mgba_count} = 1 and win_count >= 1 then
                        set emu_w to sw - {hub_w}
                        if emu_w < 400 then set emu_w to 400
                        set position of item 1 of game_wins to {{0, top_y}}
                        set size of item 1 of game_wins to {{emu_w, sh - top_y}}
                    else if {expected_mgba_count} >= 2 and win_count >= 2 then
                        set emu_w to (sw - {hub_w}) div 2
                        if emu_w < 320 then set emu_w to 320
                        set position of item 1 of game_wins to {{0, top_y}}
                        set size of item 1 of game_wins to {{emu_w, sh - top_y}}
                        set position of item 2 of game_wins to {{emu_w + {hub_w}, top_y}}
                        set size of item 2 of game_wins to {{emu_w, sh - top_y}}
                    end if
                end tell
            end if
        end tell
        """
        try:
            subprocess.run(["osascript", "-e", applescript], check=False)
        except Exception:
            pass
        return

    if not gw:
        return
    root_tmp = tk.Tk()
    sw = root_tmp.winfo_screenwidth()
    sh = root_tmp.winfo_screenheight() - 40
    root_tmp.destroy()

    hub_w = 580
    wanted_pids = [int(x) for x in (mgba_pids or []) if x]
    for _ in range(35):
        time.sleep(0.3)
        wins = gw.getAllWindows()
        hub_w_obj = next((w for w in wins if "Soul Link Companion" in w.title), None)
        mgba_wins = [w for w in wins if "mGBA" in w.title and "Scripting" not in w.title]
        if not hub_w_obj or len(mgba_wins) < expected_mgba_count:
            continue

        # Match windows to the exact mGBA processes launched for P1 and P2.
        if wanted_pids:
            by_pid = {_window_pid(w): w for w in mgba_wins if _window_pid(w)}
            ordered = [by_pid[pid] for pid in wanted_pids if pid in by_pid]
            if len(ordered) < expected_mgba_count:
                continue
            mgba_wins = ordered[:expected_mgba_count]
        else:
            mgba_wins.sort(key=lambda w: (w.left, w.top, w.title))
            mgba_wins = mgba_wins[:expected_mgba_count]

        try:
            if expected_mgba_count == 1:
                emu_w = max(400, sw - hub_w)
                mgba_wins[0].moveTo(0, 0)
                mgba_wins[0].resizeTo(emu_w, sh)
                hub_w_obj.moveTo(emu_w, 0)
                hub_w_obj.resizeTo(hub_w, sh)
            else:
                emu_w = max(320, (sw - hub_w) // 2)
                # P1 is always placed left; P2 is always placed right.
                mgba_wins[0].moveTo(0, 0)
                mgba_wins[0].resizeTo(emu_w, sh)
                hub_w_obj.moveTo(emu_w, 0)
                hub_w_obj.resizeTo(hub_w, sh)
                mgba_wins[1].moveTo(emu_w + hub_w, 0)
                mgba_wins[1].resizeTo(emu_w, sh)
        except Exception:
            continue
        break

def launch_run(profile_name, run_cfg, mode="local"):
    profiles_data = load_profiles()
    mgba_exe = resolve_mgba_binary(run_cfg.get("mgba") or profiles_data.get("mgba_exe", ""))
    saves_dir = os.path.join(PROFILES_DIR, "saves")
    os.makedirs(saves_dir, exist_ok=True)
    slug = sanitize_filename(profile_name)
    save_file = os.path.normpath(run_cfg.get("save_file", os.path.join(PROFILES_DIR, f"{slug}.json")))

    if not mgba_exe or not os.path.exists(mgba_exe):
        messagebox.showerror("mGBA Not Found", f"Invalid mGBA path:\n{mgba_exe}")
        return

    lua_script = os.path.normpath(os.path.join(BUNDLE_DIR, "soullink_p1.lua"))
    hub_script = os.path.normpath(os.path.join(BUNDLE_DIR, "soullink_hub.py"))

    # Guest mode opens ONLY the Hub first; mGBA + matching .sav opens once connected to Host!
    if mode == "join":
        if IS_MAC:
            sys.argv = [hub_script, "--profile", profile_name, "--save", save_file, "--mode", "join"]
            import importlib
            import soullink_hub
            importlib.reload(soullink_hub)
            hub_root = tk.Tk()
            soullink_hub.SoulLinkHubApp(hub_root)
            hub_root.mainloop()
        else:
            if getattr(sys, "frozen", False):
                hub_cmd = [sys.executable, "--run-hub", "--profile", profile_name, "--save", save_file, "--mode", "join"]
            else:
                hub_cmd = [sys.executable, hub_script, "--profile", profile_name, "--save", save_file, "--mode", "join"]
            subprocess.Popen(hub_cmd, cwd=APP_DATA_DIR, start_new_session=True)
        return

    if mode == "local":
        p1_rom = os.path.normpath(run_cfg.get("local_p1_rom") or run_cfg.get("p1_rom", ""))
        p2_rom = os.path.normpath(run_cfg.get("local_p2_rom") or run_cfg.get("p2_rom", ""))
        if not p1_rom or not os.path.exists(p1_rom):
            picked1 = filedialog.askopenfilename(title=f"[{profile_name}] Select Player 1 ROM (Local)", filetypes=(("GB/GBC/GBA ROMs", "*.gb *.gbc *.gba"), ("All Files", "*.*")))
            if not picked1:
                return
            p1_rom = os.path.normpath(picked1)
        if not p2_rom or not os.path.exists(p2_rom):
            picked2 = filedialog.askopenfilename(title=f"[{profile_name}] Select Player 2 ROM (Local)", filetypes=(("GB/GBC/GBA ROMs", "*.gb *.gbc *.gba"), ("All Files", "*.*")))
            if not picked2:
                return
            p2_rom = os.path.normpath(picked2)

        # mGBA's savegamePath is a DIRECTORY, not an individual .sav filename.
        p1_save = os.path.normpath(run_cfg.get("local_p1_save") or os.path.join(saves_dir, f"{slug}_P1"))
        p2_save = os.path.normpath(run_cfg.get("local_p2_save") or os.path.join(saves_dir, f"{slug}_P2"))
        p1_save = ensure_save_directory(p1_save, p1_rom)
        p2_save = ensure_save_directory(p2_save, p2_rom)
        run_cfg["local_p1_rom"], run_cfg["local_p2_rom"] = p1_rom, p2_rom
        run_cfg["local_p1_save"], run_cfg["local_p2_save"] = p1_save, p2_save
    else:
        online_rom = os.path.normpath(run_cfg.get("online_rom") or run_cfg.get("p1_rom", ""))
        if not online_rom or not os.path.exists(online_rom):
            picked = filedialog.askopenfilename(title=f"[{profile_name}] Select YOUR ROM (Online Host)", filetypes=(("GB/GBC/GBA ROMs", "*.gb *.gbc *.gba"), ("All Files", "*.*")))
            if not picked:
                return
            online_rom = os.path.normpath(picked)
        online_save = os.path.normpath(run_cfg.get("online_save") or os.path.join(saves_dir, f"{slug}_online"))
        online_save = ensure_save_directory(online_save, online_rom)
        run_cfg["online_rom"] = online_rom
        run_cfg["online_save"] = online_save

    if profile_name in profiles_data.get("runs", {}):
        profiles_data["runs"][profile_name] = run_cfg
        save_profiles(profiles_data)

    if IS_MAC:
        app_bundle = None
        if ".app/Contents/MacOS/" in mgba_exe:
            prefix, _ = mgba_exe.split(".app/Contents/MacOS/", 1)
            app_bundle = prefix + ".app"

        def spawn_mac_mgba(rom_path, custom_save):
            if app_bundle:
                subprocess.Popen(
                    ["open", "-n", "-a", app_bundle, rom_path, "--args", "-C", f"savegamePath={custom_save}"],
                    start_new_session=True
                )
            else:
                subprocess.Popen(
                    [mgba_exe, "-C", f"savegamePath={custom_save}", rom_path],
                    start_new_session=True
                )

        if mode == "local":
            spawn_mac_mgba(p1_rom, p1_save)
            time.sleep(0.8)
            spawn_mac_mgba(p2_rom, p2_save)
        else:
            spawn_mac_mgba(online_rom, online_save)

        time.sleep(1.5)
        # With two windows we cannot tell which one macOS will load into, so
        # local mode keeps the shared script.
        if mode == "local":
            load_lua_mac(lua_script)
        else:
            load_lua_mac(prepare_instance_script(lua_script, online_save))
        position_windows(expected_mgba_count=2 if mode == "local" else 1)

        sys.argv = [hub_script, "--profile", profile_name, "--save", save_file, "--mode", mode]
        import importlib
        import soullink_hub
        importlib.reload(soullink_hub)
        hub_root = tk.Tk()
        soullink_hub.SoulLinkHubApp(hub_root)
        hub_root.mainloop()
    else:
        mgba_processes = []
        if mode == "local":
            mgba_processes.append(subprocess.Popen([mgba_exe, "-C", f"savegamePath={p1_save}", p1_rom], start_new_session=True))
            time.sleep(0.8)
            mgba_processes.append(subprocess.Popen([mgba_exe, "-C", f"savegamePath={p2_save}", p2_rom], start_new_session=True))
        else:
            mgba_processes.append(subprocess.Popen([mgba_exe, "-C", f"savegamePath={online_save}", online_rom], start_new_session=True))

        if getattr(sys, "frozen", False):
            hub_cmd = [sys.executable, "--run-hub", "--profile", profile_name, "--save", save_file, "--mode", mode]
        else:
            hub_cmd = [sys.executable, hub_script, "--profile", profile_name, "--save", save_file, "--mode", mode]
        subprocess.Popen(hub_cmd, cwd=APP_DATA_DIR, start_new_session=True)
        mgba_pids = [proc.pid for proc in mgba_processes]
        position_windows(expected_mgba_count=2 if mode == "local" else 1, mgba_pids=mgba_pids)
        if gw:
            time.sleep(0.4)
            mgba_wins = [w for w in gw.getAllWindows() if "mGBA" in w.title and "Scripting" not in w.title]
            if IS_WIN:
                pid_to_window = {_window_pid(w): w for w in mgba_wins if _window_pid(w)}
                mgba_wins = [pid_to_window[pid] for pid in mgba_pids if pid in pid_to_window]
            else:
                mgba_wins.sort(key=lambda w: (w.left, w.top, w.title))
            save_dirs = [p1_save, p2_save] if mode == "local" else [online_save]
            scripts = {
                proc.pid: prepare_instance_script(lua_script, folder)
                for proc, folder in zip(mgba_processes, save_dirs)
            }
            for w in mgba_wins:
                load_lua_into_mgba(w, scripts.get(_window_pid(w), lua_script))

            import pyautogui
            down_key = get_mgba_down_key()
            for w in mgba_wins:
                try:
                    pyautogui.click(int(w.left + w.width // 2), int(w.top + w.height // 2))
                    time.sleep(0.15)
                    pyautogui.keyDown(down_key)
                    time.sleep(0.06)
                    pyautogui.keyUp(down_key)
                except Exception:
                    pass


class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Soul Link Run Manager")
        self.root.geometry("520x510")
        self.bg_main = "#eceff4" if IS_MAC else "#1e1e2e"
        self.bg_card = "#e5e9f0" if IS_MAC else "#181825"
        self.fg_text = "#11111b" if IS_MAC else "#ffffff"
        self.fg_title = "#5e35b1" if IS_MAC else "#cba6f7"
        self.fg_sub = "#b45309" if IS_MAC else "#f9e2af"
        self.root.configure(bg=self.bg_main)

        self.data = load_profiles()
        self.build_ui()
        self.root.after(200, lambda: self.ensure_mgba_path(force=False))

    def build_ui(self):
        hdr = tk.Frame(self.root, bg=self.bg_card, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="POKÉMON SOUL LINK LAUNCHER", font=("Segoe UI", 13, "bold"), bg=self.bg_card, fg=self.fg_title).pack()

        emu_row = tk.Frame(hdr, bg=self.bg_card)
        emu_row.pack(pady=(4, 0))
        self.lbl_mgba = tk.Label(emu_row, text="mGBA: Not Configured", font=("Segoe UI", 8), bg=self.bg_card, fg=self.fg_sub)
        self.lbl_mgba.pack(side="left", padx=6)
        tk.Button(
            emu_row, text="Change mGBA",
            command=lambda: self.ensure_mgba_path(force=True),
            bg="#45475a", fg="#ffffff", font=("Segoe UI", 8, "bold"), relief="flat", padx=6
        ).pack(side="left")

        body = tk.Frame(self.root, bg=self.bg_main, padx=18, pady=10)
        body.pack(fill="both", expand=True)

        # --- SECTION 1: LOCAL 2-WINDOW CO-OP ---
        local_card = tk.Frame(body, bg=self.bg_card, padx=12, pady=10)
        local_card.pack(fill="x", pady=(0, 10))

        l_top = tk.Frame(local_card, bg=self.bg_card)
        l_top.pack(fill="x", pady=(0, 4))
        tk.Label(l_top, text="LOCAL 2-WINDOW RUNS", font=("Segoe UI", 9, "bold"), bg=self.bg_card, fg="#a6e3a1" if not IS_MAC else "#15803d").pack(side="left")
        tk.Button(l_top, text="Delete", command=lambda: self.delete_run("local"), bg="#f38ba8", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=8).pack(side="right", padx=(4, 0))
        tk.Button(l_top, text="+ New Local Run", command=self.create_local_run, bg="#89b4fa", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=8).pack(side="right")

        self.local_run_var = tk.StringVar()
        self.local_combo = ttk.Combobox(local_card, textvariable=self.local_run_var, state="readonly", font=("Segoe UI", 10))
        self.local_combo.pack(fill="x", pady=(2, 8))

        tk.Button(
            local_card, text="▶ Launch Local 2-Window Co-Op",
            command=lambda: self.start_selected("local"),
            bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 10, "bold"), relief="flat", pady=7
        ).pack(fill="x")

        # --- SECTION 2: ONLINE P2P CO-OP ---
        online_card = tk.Frame(body, bg=self.bg_card, padx=12, pady=10)
        online_card.pack(fill="x")

        o_top = tk.Frame(online_card, bg=self.bg_card)
        o_top.pack(fill="x", pady=(0, 4))
        tk.Label(o_top, text="ONLINE P2P RUNS (HOST / GUEST)", font=("Segoe UI", 9, "bold"), bg=self.bg_card, fg=self.fg_title).pack(side="left")
        tk.Button(o_top, text="Delete", command=lambda: self.delete_run("online"), bg="#f38ba8", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=8).pack(side="right", padx=(4, 0))
        tk.Button(o_top, text="+ New Online Run", command=self.create_online_run, bg="#89b4fa", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=8).pack(side="right")

        self.online_run_var = tk.StringVar()
        self.online_combo = ttk.Combobox(online_card, textvariable=self.online_run_var, state="readonly", font=("Segoe UI", 10))
        self.online_combo.pack(fill="x", pady=(2, 8))

        net_row = tk.Frame(online_card, bg=self.bg_card)
        net_row.pack(fill="x")
        tk.Button(
            net_row, text="🌐 Host Online (P1)",
            command=lambda: self.start_selected("host"),
            bg="#cba6f7", fg="#11111b", font=("Segoe UI", 10, "bold"), relief="flat", pady=7
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(
            net_row, text="🔗 Join Online (P2)",
            command=self.start_guest_join,
            bg="#f9e2af", fg="#11111b", font=("Segoe UI", 10, "bold"), relief="flat", pady=7
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.refresh_run_list()
        self.update_mgba_label()

    def update_mgba_label(self):
        exe = self.data.get("mgba_exe", "")
        if exe and os.path.exists(exe):
            short = "mGBA.app" if ".app/" in exe else os.path.basename(exe)
            self.lbl_mgba.config(text=f"mGBA: {short} ✓", fg="#15803d" if IS_MAC else "#a6e3a1")
        else:
            self.lbl_mgba.config(text="mGBA: Not Configured", fg=self.fg_sub)

    def ensure_mgba_path(self, force=False):
        exe = resolve_mgba_binary(self.data.get("mgba_exe", ""))
        if not force and exe and os.path.exists(exe):
            self.data["mgba_exe"] = exe
            self.update_mgba_label()
            return True

        if IS_MAC and not force:
            for candidate in ("/Applications/mGBA.app", os.path.expanduser("~/Applications/mGBA.app")):
                auto_resolved = resolve_mgba_binary(candidate)
                if auto_resolved and os.path.exists(auto_resolved):
                    self.data["mgba_exe"] = auto_resolved
                    save_profiles(self.data)
                    self.update_mgba_label()
                    return True

        target_label = "mGBA.app" if IS_MAC else "mGBA.exe"
        if not force:
            messagebox.showinfo(
                "One-Time mGBA Setup",
                f"Please select your {target_label} emulator.\n\nThis will be saved permanently so you won't be asked again."
            )
        if IS_MAC:
            picked = filedialog.askopenfilename(title="Select mGBA.app", initialdir="/Applications")
        else:
            picked = filedialog.askopenfilename(title="Locate mGBA.exe", filetypes=(("mGBA Executable", "mGBA.exe"), ("All Executables", "*.exe")))

        resolved = resolve_mgba_binary(picked)
        if resolved and os.path.exists(resolved):
            self.data["mgba_exe"] = resolved
            save_profiles(self.data)
            self.update_mgba_label()
            return True
        self.update_mgba_label()
        return False

    def refresh_run_list(self):
        runs = self.data.get("runs", {})
        local_names = []
        online_names = []
        for k in sorted(runs.keys()):
            cfg = runs[k]
            rtype = cfg.get("run_type")
            if rtype == "online" or ("online_rom" in cfg and "local_p1_rom" not in cfg):
                online_names.append(k)
            else:
                local_names.append(k)

        self.local_combo["values"] = local_names
        if local_names and self.local_run_var.get() not in local_names:
            self.local_run_var.set(next(iter(local_names)))
        elif not local_names:
            self.local_run_var.set("")

        self.online_combo["values"] = online_names
        if online_names and self.online_run_var.get() not in online_names:
            self.online_run_var.set(next(iter(online_names)))
        elif not online_names:
            self.online_run_var.set("")

    def create_local_run(self):
        if not self.ensure_mgba_path(force=False):
            return
        name = simpledialog.askstring("New Local Run", "Enter a name for this Local 2-Window run:", parent=self.root)
        if not name or not name.strip():
            return
        name = name.strip()
        if name in self.data.get("runs", {}):
            messagebox.showwarning("Duplicate Name", f"A run named '{name}' already exists.")
            return

        p1_rom = filedialog.askopenfilename(title=f"[{name}] Select Player 1 ROM (Local)", filetypes=(("GB/GBC/GBA ROMs", "*.gb *.gbc *.gba"), ("All Files", "*.*")))
        if not p1_rom:
            return
        p2_rom = filedialog.askopenfilename(title=f"[{name}] Select Player 2 ROM (Local)", filetypes=(("GB/GBC/GBA ROMs", "*.gb *.gbc *.gba"), ("All Files", "*.*")))
        if not p2_rom:
            return

        saves_dir = os.path.join(PROFILES_DIR, "saves")
        os.makedirs(saves_dir, exist_ok=True)
        slug = sanitize_filename(name)

        self.data.setdefault("runs", {})[name] = {
            "run_type": "local",
            "mgba": self.data.get("mgba_exe", ""),
            "local_p1_rom": p1_rom,
            "local_p2_rom": p2_rom,
            "local_p1_save": os.path.join(saves_dir, f"{slug}_P1"),
            "local_p2_save": os.path.join(saves_dir, f"{slug}_P2"),
            "save_file": os.path.join(PROFILES_DIR, f"{slug}.json")
        }
        save_profiles(self.data)
        self.refresh_run_list()
        self.local_run_var.set(name)

    def create_online_run(self):
        if not self.ensure_mgba_path(force=False):
            return
        name = simpledialog.askstring("New Online Run", "Enter a name for this Online P2P run:", parent=self.root)
        if not name or not name.strip():
            return
        name = name.strip()
        if name in self.data.get("runs", {}):
            messagebox.showwarning("Duplicate Name", f"A run named '{name}' already exists.")
            return

        online_rom = filedialog.askopenfilename(title=f"[{name}] Select YOUR ROM (Online Host)", filetypes=(("GB/GBC/GBA ROMs", "*.gb *.gbc *.gba"), ("All Files", "*.*")))
        if not online_rom:
            return

        saves_dir = os.path.join(PROFILES_DIR, "saves")
        os.makedirs(saves_dir, exist_ok=True)
        slug = sanitize_filename(name)

        self.data.setdefault("runs", {})[name] = {
            "run_type": "online",
            "mgba": self.data.get("mgba_exe", ""),
            "online_rom": online_rom,
                        "online_save": os.path.join(saves_dir, f"{slug}_online"),
            "save_file": os.path.join(PROFILES_DIR, f"{slug}.json")
        }
        save_profiles(self.data)
        self.refresh_run_list()
        self.online_run_var.set(name)
    def delete_run(self, section):
        name = self.local_run_var.get() if section == "local" else self.online_run_var.get()
        if not name or name not in self.data.get("runs", {}):
            return

        if not messagebox.askyesno(
            "Delete Run",
            f"Delete '{name}' and its associated emulator .sav files and project .json file?\\n\\n"
            "This cannot be undone."
        ):
            return

        cfg = self.data["runs"].get(name, {})
        slug = sanitize_filename(name)
        saves_dir = os.path.join(PROFILES_DIR, "saves")

        # Remove explicitly recorded paths, plus the canonical paths generated
        # by older launcher versions when those fields were absent.
        recorded_save_paths = [
            cfg.get("local_p1_save"),
            cfg.get("local_p2_save"),
            cfg.get("online_save"),
        ]
        candidates = [
            *recorded_save_paths,
            cfg.get("save_file"),
            os.path.join(saves_dir, f"{slug}_P1"),
            os.path.join(saves_dir, f"{slug}_P2"),
            os.path.join(saves_dir, f"{slug}_online"),
            # mGBA may create a regular save file by appending .sav to the
            # configured savegamePath. Remove both the path and that file.
            os.path.join(saves_dir, f"{slug}_P1.sav"),
            os.path.join(saves_dir, f"{slug}_P2.sav"),
            os.path.join(saves_dir, f"{slug}_online.sav"),
            os.path.join(PROFILES_DIR, f"{slug}.json"),
        ]
        # Older profiles may store a save *base path* without the .sav suffix,
        # while mGBA writes the actual battery save beside it as <base>.sav.
        for raw_save_path in recorded_save_paths:
            if raw_save_path:
                raw_save_path = os.path.abspath(os.path.expanduser(os.path.normpath(str(raw_save_path))))
                if not raw_save_path.lower().endswith(".sav"):
                    candidates.append(raw_save_path + ".sav")

        removed = []
        failures = []
        seen = set()
        saves_root = os.path.realpath(saves_dir)
        for raw_path in candidates:
            if not raw_path:
                continue
            fpath = os.path.abspath(os.path.expanduser(os.path.normpath(str(raw_path))))
            if fpath in seen:
                continue
            seen.add(fpath)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
                    removed.append(fpath)
                elif os.path.isdir(fpath):
                    # Recursively remove only a run-owned folder under saves/.
                    real_path = os.path.realpath(fpath)
                    if os.path.commonpath([saves_root, real_path]) == saves_root and real_path != saves_root:
                        shutil.rmtree(real_path)
                        removed.append(real_path)
            except (OSError, ValueError) as exc:
                failures.append(f"{fpath}: {exc}")

        # Remove the run entry only after attempting every associated file.
        self.data["runs"].pop(name, None)
        save_profiles(self.data)
        self.refresh_run_list()

        if section == "local":
            self.local_run_var.set("")
        else:
            self.online_run_var.set("")

        if failures:
            messagebox.showwarning(
                "Run Deleted With File Errors",
                "The run entry was deleted, but some files could not be removed:\\n\\n"
                + "\\n".join(failures)
            )
        else:
            messagebox.showinfo(
                "Run Deleted",
                f"Deleted '{name}' and {len(removed)} associated file(s)."
            )

    def start_selected(self, mode):
        if not self.ensure_mgba_path(force=False):
            return
        name = self.local_run_var.get() if mode == "local" else self.online_run_var.get()
        if not name or name not in self.data.get("runs", {}):
            label = "Local" if mode == "local" else "Online"
            messagebox.showwarning(f"No {label} Run Selected", f"Please select or create a {label} run first.")
            return
        run_cfg = dict(self.data["runs"][name])
        self.root.destroy()
        launch_run(name, run_cfg, mode=mode)
    def start_guest_join(self):
        if not self.ensure_mgba_path(force=False):
            return
        guest_save = os.path.join(PROFILES_DIR, "_guest_session.json")
        self.root.destroy()
        launch_run("Online Guest", {"save_file": guest_save}, mode="join")


if __name__ == "__main__":
    if "--run-hub" in sys.argv:
        sys.argv.remove("--run-hub")
        import soullink_hub
        hub_root = tk.Tk()
        soullink_hub.SoulLinkHubApp(hub_root)
        hub_root.mainloop()
    else:
        root = tk.Tk()
        LauncherApp(root)
        root.mainloop()

