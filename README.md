## MaxPane

Easily maximize/unmaximize a pane without reseting your multi-pane setup.

Ever use a multi pane setup in Sublime Text and want to maximize a single pane for a bit, *and* be able to switch back to the multi pane layout again when done? *Without losing the positions all your files were in.* You know like how iTerm does.

*Then MaxPane is for you.*

So lets say you have this multi pane setup:

![dual pane](https://raw.github.com/jisaacks/MaxPane/3535650829f9bbb7df2d26428589b9bd47b13591/before.png)

and you want to maximize the active (top left) pane for a sec.

Just press <kbd>cmd</kbd>+<kbd>shift</kbd>+<kbd>enter</kbd> and the active pane is now maximized:

![single pane](https://raw.github.com/jisaacks/MaxPane/3535650829f9bbb7df2d26428589b9bd47b13591/after.png)

Press <kbd>cmd</kbd>+<kbd>shift</kbd>+<kbd>enter</kbd> another time and its back:

![dual pane](https://raw.github.com/jisaacks/MaxPane/3535650829f9bbb7df2d26428589b9bd47b13591/before.png)

***It also works great with [Origami](https://github.com/SublimeText/Origami) and [Distraction Free Window](https://github.com/aziz/DistractionFreeWindow#changing-layout)!***


## Installation

### By Package Control

1. Download & Install **`Sublime Text 3`** (https://www.sublimetext.com/3)
1. Go to the menu **`Tools -> Install Package Control`**, then,
   wait few seconds until the installation finishes up
1. Now,
   Go to the menu **`Preferences -> Package Control`**
1. Type **`Add Channel`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
   input the following address and press <kbd>Enter</kbd>
   ```
   https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json
   ```
1. Go to the menu **`Tools -> Command Palette...
   (Ctrl+Shift+P)`**
1. Type **`Preferences:
   Package Control Settings – User`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
   find the following setting on your **`Package Control.sublime-settings`** file:
   ```js
       "channels":
       [
           "https://packagecontrol.io/channel_v3.json",
           "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
       ],
   ```
1. And,
   change it to the following, i.e.,
   put the **`https://raw.githubusercontent...`** line as first:
   ```js
       "channels":
       [
           "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
           "https://packagecontrol.io/channel_v3.json",
       ],
   ```
   * The **`https://raw.githubusercontent...`** line must to be added before the **`https://packagecontrol.io...`** one, otherwise,
     you will not install this forked version of the package,
     but the original available on the Package Control default channel **`https://packagecontrol.io...`**
1. Now,
   go to the menu **`Preferences -> Package Control`**
1. Type **`Install Package`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
search for **`MaxPane`** and press <kbd>Enter</kbd>

See also:

1. [ITE - Integrated Toolset Environment](https://github.com/evandrocoan/ITE)
1. [Package control docs](https://packagecontrol.io/docs/usage) for details.


### Bonus
When maximized, you can navigate to your other panes with:
<kbd>cmd</kbd>+<kbd>ctrl</kbd>+<kbd>→</kbd> or <kbd>cmd</kbd>+<kbd>ctrl</kbd>+<kbd>←</kbd>
* _Windows / Linux users will need to setup their own key bindings_

### Installation

Install via [Package Control](http://wbond.net/sublime_packages/package_control)
