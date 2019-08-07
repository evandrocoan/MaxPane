import sublime
import sublime_plugin


g_is_running = False
SHARE_OBJECT = 'max_pane_share.sublime-settings'


def fixed_set_layout(window, layout):
    # https://github.com/SublimeTextIssues/Core/issues/2919
    active_group = window.active_group()
    window.set_layout( layout )
    window.focus_group( active_group )


class PaneManager:
    layouts = {}
    maxgroup = {}

    @staticmethod
    def isWindowMaximized(window):
        w = window
        if PaneManager.hasLayout(w):
            return True
        elif PaneManager.looksMaximized(w):
            return True
        return False

    @staticmethod
    def looksMaximized(window):
        w = window
        l = window.get_layout()
        c = l["cols"]
        r = l["rows"]
        if w.num_groups() > 1:
            if set(c + r) == set([0.0, 1.0]):
                return True
        return False

    @staticmethod
    def storeLayout(window):
        w = window
        wid = window.id()
        PaneManager.layouts[wid] = w.get_layout()
        PaneManager.maxgroup[wid] = w.active_group()

    @staticmethod
    def maxedGroup(window):
        wid = window.id()
        if wid in PaneManager.maxgroup:
            return PaneManager.maxgroup[wid]

    @staticmethod
    def popLayout(window):
        wid = window.id()
        l = PaneManager.layouts[wid]
        del PaneManager.layouts[wid]
        del PaneManager.maxgroup[wid]
        return l

    @staticmethod
    def hasLayout(window):
        wid = window.id()
        return wid in PaneManager.layouts


class MaxPaneCommand(sublime_plugin.WindowCommand):
    """Toggles pane maximization."""
    def run(self):
        w = self.window
        if PaneManager.isWindowMaximized(w):
            w.run_command("unmaximize_pane")

        elif w.num_groups() > 1:
            w.run_command("maximize_pane")


class MaximizePaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        global g_is_running
        g_is_running = True

        w = self.window
        g = w.active_group()
        l = w.get_layout()
        PaneManager.storeLayout(w)
        current_col = int(l["cells"][g][2])
        current_row = int(l["cells"][g][3])
        new_rows = []
        new_cols = []
        for index, row in enumerate(l["rows"]):
            new_rows.append(0.0 if index < current_row else 1.0)
        for index, col in enumerate(l["cols"]):
            new_cols.append(0.0 if index < current_col else 1.0)
        l["rows"] = new_rows
        l["cols"] = new_cols
        for view in w.views():
            view.set_status('0_maxpane', 'MAX')

        w.settings().set( "is_panel_maximized", True )
        fixed_set_layout( w, l )
        g_is_running = False


class UnmaximizePaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        w = self.window
        w.settings().set( "is_panel_maximized", False )

        if PaneManager.hasLayout(w):
            l = PaneManager.popLayout(w)
            fixed_set_layout( w, l )
        elif PaneManager.looksMaximized(w):
            # We don't have a previous layout for this window
            # but it looks like it was maximized, so lets
            # just evenly distribute the layout.
            self.evenOutLayout()
        for view in w.views():
            view.erase_status('0_maxpane')

    def evenOutLayout(self):
        w = self.window
        w.run_command("distribute_layout")


class DistributeLayoutCommand(sublime_plugin.WindowCommand):
    def run(self):
        w = self.window
        l = w.get_layout()
        l["rows"] = self.distribute(l["rows"])
        l["cols"] = self.distribute(l["cols"])
        fixed_set_layout( w, l )

    def distribute(self, values):
        l = len(values)
        r = range(0, l)
        return [n / float(l - 1) for n in r]


class ShiftPaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        w = self.window
        w.focus_group(self.groupToMoveTo())

    def groupToMoveTo(self):
        w = self.window
        g = w.active_group()
        n = w.num_groups() - 1
        if g == n:
            m = 0
        else:
            m = g + 1
        return m


class UnshiftPaneCommand(ShiftPaneCommand):
    def groupToMoveTo(self):
        w = self.window
        g = w.active_group()
        n = w.num_groups() - 1
        if g == 0:
            m = n
        else:
            m = g - 1
        return m


class MaxPaneEvents(sublime_plugin.EventListener):

    def on_activated(self, view):
        global g_is_running

        # print('g_is_running', g_is_running)
        if g_is_running: return

        # Is the window currently maximized?
        g_is_running = True
        w = view.window() or sublime.active_window()

        if w and PaneManager.isWindowMaximized(w):
            active_group = w.active_group()

            # Is the active group the group that is maximized?
            if active_group != PaneManager.maxedGroup(w):

                def unmaximize():
                    w.run_command("unmaximize_pane")
                    sublime.set_timeout( maximize, 100 )

                def maximize():
                    w.run_command("maximize_pane")
                    sublime.set_timeout( disable, 100 )

                def disable():
                    global g_is_running
                    g_is_running = False

                # print('active_group', active_group)
                sublime.set_timeout( unmaximize, 100 )

            else:
                g_is_running = False

        else:
            g_is_running = False
