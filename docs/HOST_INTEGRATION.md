# Host Integration & Daily Workflow (`macOS` + `Windows`)

This guide documents the **HID key contract** and **host-side software setup** for using the 8BitDo Dual Super Buttons and Super Stick with this adapter (and identically during the transitional period when plugged into an 8BitDo Retro Mechanical Keyboard).

---

## 1. Shared HID Key Contract (`F13`–`F18`)

On **macOS** (Firmware **Layer 0 — Calm Blue**), the adapter emits clean, conflict-free extended function keys (`F13`–`F18`) so host automation ([`hammerspoon/button_adapter.lua`](../hammerspoon/button_adapter.lua)) can dispatch context-aware actions based on the active window:

| Physical Input | Matrix Position | Firmware Layer 0 (`macOS` / Blue) | Firmware Layer 1 (`Windows` / Green) |
| :--- | :---: | :---: | :--- |
| **Button A** | `(0, 0)` `GP6` | `F17` | `Ctrl + M` (Antigravity voice toggle) |
| **Button B** | `(0, 1)` `GP7` | `F18` | `Enter` (send immediately after dictation) |
| **Super Stick Up** | `(0, 2)` `GP0` | `F13` | `Win + Tab` (Task View) |
| **Super Stick Down** | `(0, 3)` `GP1` | `F15` | `Win + D` (Show / Toggle Desktop) |
| **Super Stick Left** | `(0, 4)` `GP2` | `F14` | `Ctrl + Win + Left` (Previous Virtual Desktop) |
| **Super Stick Right** | `(0, 5)` `GP4` | `F16` | `Ctrl + Win + Right` (Next Virtual Desktop) |
| **Combo: A + B** | `(0, 0) + (0, 1)` | Toggle Layer 0 ↔ Layer 1 (`TG(1)`) | Toggle Layer 1 ↔ Layer 0 (`TG(1)`) |

> Notice the counter-clockwise numbering on the Super Stick: **Up = `F13`, Left = `F14`, Down = `F15`, Right = `F16`**. If the two Super Stick 3.5mm plugs are swapped during assembly or daily use, you can reassign them live in [vial.rocks](https://vial.rocks) without resoldering or editing Lua.

---

## 2. macOS Setup (Hammerspoon)

Host module: [`hammerspoon/button_adapter.lua`](../hammerspoon/button_adapter.lua)

### Out-of-the-Box Behavior

- **Button A (`F17`) — App-Aware Voice Input**
  - **Antigravity** (`Antigravity` / `Google Antigravity`):
    - **Tap** (`< 0.35s`): sends `Ctrl + M` to toggle dictation on/off.
    - **Hold** (`≥ 0.35s`): Push-to-Talk — sends `Ctrl + M` on press and automatically sends `Ctrl + M` again on release.
  - **Claude Code CLI Terminals** (`Terminal`, `iTerm2`, `Ghostty`, `WezTerm`, `Warp`, `Alacritty`, `kitty`):
    - **Hold**: holds `Space` down for Claude Code `/voice` push-to-talk; releases `Space` on button release.
  - **Claude Desktop** (`Claude`):
    - Searches the focused window's macOS Accessibility tree (`hs.axuielement`) for the mic/dictation button and triggers `AXPress` (with automatic hold-to-release toggle). Falls back to Gemini for Mac if the button is not exposed.
  - **All Other Apps (Global Fallback)**:
    - Triggers `CONFIG.geminiFallback` (**Gemini for Mac** hotkey).

- **Button B (`F18`) — Background Google Meet Controller**
  - Works even while coding in another window (never accidentally triggers `Cmd + D` bookmarking on non-Meet browser tabs):
    - **Tap** (`< 0.35s`): Toggle Mute (`Cmd + D`).
    - **Hold** (`≥ 0.35s`): Toggle Raise / Lower Hand (`Ctrl + Cmd + H`).
  - Default mode briefly focuses the Meet tab via AppleScript, sends the native shortcut, and restores your previous app/tab.
  - Optional **zero-flicker silent mode**: enable **View → Developer → Allow JavaScript from Apple Events** in Chrome and set `CONFIG.meetUseAppleEventsJS = true`.

- **Super Stick (`F13`–`F16`) — macOS Spaces & Mission Control**
  - `F13` (Up): Mission Control (`Ctrl + ↑`)
  - `F14` (Left): Previous Desktop Space (`Ctrl + ←`)
  - `F15` (Down): App Exposé (`Ctrl + ↓`)
  - `F16` (Right): Next Desktop Space (`Ctrl + →`)

### Installation

1. Load the module in `~/.hammerspoon/init.lua`:
   ```lua
   package.path = os.getenv("HOME") .. "/path/to/button-adapter/hammerspoon/?.lua;" .. package.path
   require("button_adapter")
   ```
   *(Alternatively, symlink `hammerspoon/button_adapter.lua` into `~/.hammerspoon/` and call `require("button_adapter")`.)*
2. Open [`hammerspoon/button_adapter.lua`](../hammerspoon/button_adapter.lua) and customize the `CONFIG` table at the top:
   - **`CONFIG.geminiFallback`**: set `mods` and `key` to your actual **Gemini for Mac** shortcut (and set `isToggle = true` if pressing it a second time stops listening).
   - **`CONFIG.meetBrowser`**: defaults to `"Google Chrome"` (change to `"Arc"`, `"Brave Browser"`, etc. if needed).
   - **`CONFIG.antigravity.appNames`**: if your macOS Antigravity build reports a different process name, temporarily uncomment the debug hotkey (`Cmd+Option+Ctrl+I`) at the bottom of the file to print the exact app name.
3. Reload Hammerspoon and grant **Accessibility** + **Automation (Chrome)** permissions when prompted by macOS.

---

## 3. Windows Setup (Zero Host Software Required)

When using the standalone adapter on Windows, press **Button A + Button B simultaneously** to switch to **Layer 1 (`_WIN` — Calm Green LED)**. The adapter sends all Windows shortcuts directly in hardware:

- **Button A** → `Ctrl + M` (Antigravity voice input toggle)
- **Button B** → `Enter` (slap A to speak, slap B to send)
- **Super Stick** → `Win + Tab` (Up), `Win + D` (Down), `Ctrl + Win + Left` (Left), `Ctrl + Win + Right` (Right)

No AutoHotkey or background service is required.

---

## 4. Transitional Setup (Via 8BitDo Retro Mechanical Keyboard)

Before assembling the standalone USB-C adapter, the exact same workflow runs through the 8BitDo Retro Keyboard's rear 3.5mm ports:

1. Program the keyboard's onboard profile once via **8BitDo Ultimate Software V2** so the ports emit `F13`–`F16` (Super Stick Up/Left/Down/Right) and `F17`–`F18` (Button A / Button B).
2. On **macOS**, Kanata ([`yanghu/kanata-config-8bitdo`](https://github.com/yanghu/kanata-config-8bitdo)) passes `F13`–`F18` straight through to `hammerspoon/button_adapter.lua`.
3. On **Windows**, `yanghu/kanata-config-8bitdo` uses `(platform (win winiov2 wintercept) ...)` to translate `F13`–`F18` into the exact same Windows shortcuts listed above.
