# LÖVELY2D

![video demo](demo.gif)

A (WIP) Sublime Text 4 plugin for LÖVE2D development that provides autocomplete and API information.

Based on [LÖVE-API](https://github.com/love2d-community/love-api).

## Installation

**Note: LÖVELY2D is intended to work with Sublime Text versions 4102 and above.** To find out how to download Sublime Text 4, check out [this gist.](https://gist.github.com/jfcherng/7bf4103ea486d1f67b7970e846b3a619)

### Package Control

LÖVELY2D is not on [Package Control](https://packagecontrol.io/) yet. Stay tuned.

### Manually

1. Navigate to your `Packages` folder (easiest way to find it is from within Sublime Text, go to `Preferences > Browse Packages...`).
2. Download the latest release from the [releases page](https://github.com/kevinfiol/LOVELY2D/releases).
3. Unzip the downloaded archive. Copy the directory `LOVELY2D-x.x.x` into your `Packages` folder.

### With Git

Use `git clone` to clone this repository into your `Packages` folder.

```bash
# From within your `Packages` folder
git clone https://github.com/kevinfiol/LOVELY2D.git
```

## Usage

From within a `.lua` file, set the syntax to `LOVELY2D`. Autocomplete and hover tips should function normally.

*Tip:* I recommend setting `"auto_complete_preserve_order": "none"` in your Sublime preferences for more predictable auto-complete behavior.

### Usage with Sublime LSP

[Sublime LSP](https://github.com/sublimelsp/LSP) is an implementation of the Language Server Protocol for Sublime Text. You can use it in conjunction with LÖVELY2D for an even better LÖVE2D development experience.

1. Follow the instructions to install and enable the Lua language server [here](https://lsp.sublimetext.io/language_servers/#lua).
2. In `LSP.sublime-settings`, modify the `selector` and `settings` property so that LÖVELY2D Syntax files are correctly parsed and diagnostics doesn't nag you about the `love` global. Example:

```json
{
    "clients": {
        "lua-ls": {
            "enabled": true,
            "command": [
                "C:\\Users\\johndoe\\lua-lsp\\sumneko.lua-1.19.1\\server\\bin\\Windows\\lua-language-server.exe",
                "-E", "C:\\Users\\johndoe\\lua-lsp\\sumneko.lua-1.19.1\\server\\main.lua"
            ],
            "selector": "source.lovely | source.lua",
            "settings": {
                "Lua": {
                    "diagnostics": {
                        "globals": ["love"]
                    }
                }
            }
        }
    }
}

```

## Known Issues / To-Do

* (Bug) Invoking the API popup on anything under the `love.` namespace closes the autocomplete. This is unintended, and I'm not sure why it happens (help appreciated!)
* Function override signatures not provided in hints
* Hover tips are sometimes overridden by Reference tips
* General clean-up / commenting
* ~~Implement function signature helper while typing in parameters~~ *(Added in 0.6.0)*
