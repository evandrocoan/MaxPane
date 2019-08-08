import sublime
import sublime_plugin


g_is_running = False


def fixed_set_layout(window, layout):
    # https://github.com/SublimeTextIssues/Core/issues/2919
    active_group = window.active_group()
    window.set_layout( layout )
    window.focus_group( active_group )


def is_pane_maximized(window):
    return window.settings().get( 'is_panel_maximized' )


def looks_maximized(window):
    layout = window.layout()
    columns = layout['cols']
    rows = layout['rows']

    if window.num_groups() > 1:
        if set(columns + rows) == set([0.0, 1.0]):
            return True
    return False


class MaxPaneCommand(sublime_plugin.WindowCommand):
    """Toggles pane maximization."""

    def run(self):
        window = self.window

        if is_pane_maximized(window):
            window.run_command('unmaximize_pane')

        else:
            num_groups = window.num_groups()

            if num_groups > 1:
                window.run_command( 'maximize_pane' )

            else:
                print( "MaxPane Error: Cannot zoom a window only with '%s' panes!" % num_groups )


class MaximizePaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        global g_is_running
        g_is_running = True

        window = self.window
        settings = window.settings()

        origami_fraction = settings.get( 'origami_fraction' )
        original_panes_layout = settings.get( 'original_panes_layout' )

        if origami_fraction or original_panes_layout:
            print("MaxPane Error: Trying to maximize a maximized pane!")
            window.run_command('unmaximize_pane')
            return

        layout = window.layout()
        active_group = window.active_group()

        settings.set( 'original_panes_layout', layout )
        settings.set( 'maximized_pane_group', active_group )

        new_rows = []
        new_cols = []
        current_col = int(layout['cells'][active_group][2])
        current_row = int(layout['cells'][active_group][3])

        for index, row in enumerate(layout['rows']):
            new_rows.append(0.0 if index < current_row else 1.0)

        for index, col in enumerate(layout['cols']):
            new_cols.append(0.0 if index < current_col else 1.0)

        layout['rows'] = new_rows
        layout['cols'] = new_cols

        settings.set( 'is_panel_maximized', True )
        fixed_set_layout( window, layout )
        g_is_running = False


class UnmaximizePaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = self.window
        settings = window.settings()

        settings.set( 'origami_fraction', None )
        settings.set( 'is_panel_maximized', False )
        settings.set( 'maximized_pane_group', None )

        if settings.get( 'original_panes_layout') :
            layout = settings.get( 'original_panes_layout' )
            settings.set( 'original_panes_layout', None )
            fixed_set_layout( window, layout )

        elif looks_maximized( window ):
            # We don't have a previous layout for this window
            # but it looks like it was maximized, so lets
            # just evenly distribute the layout.
            window.run_command( 'distribute_layout' )


class DistributeLayoutCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = self.window
        layout = window.layout()

        layout['rows'] = self.distribute(layout['rows'])
        layout['cols'] = self.distribute(layout['cols'])
        fixed_set_layout( window, layout )

    def distribute(self, values):
        layout = len(values)
        return [n / float(layout - 1) for n in range(0, layout)]


class ShiftPaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = self.window
        window.focus_group( self.groupToMoveTo() )

    def groupToMoveTo(self):
        window = self.window
        active_group = window.active_group()
        n = window.num_groups() - 1

        if active_group == n:
            m = 0
        else:
            m = active_group + 1

        return m


class UnshiftPaneCommand(ShiftPaneCommand):
    def groupToMoveTo(self):
        window = self.window
        active_group = window.active_group()
        n = window.num_groups() - 1

        if active_group == 0:
            m = n
        else:
            m = active_group - 1

        return m


class MaxPaneEvents(sublime_plugin.EventListener):

    def on_activated(self, view):
        global g_is_running

        # print( 'Entering g_is_running', g_is_running )
        if g_is_running: return

        # Is the window currently maximized?
        g_is_running = True
        window = view.window() or sublime.active_window()

        # print()
        def disable():
            global g_is_running
            g_is_running = False

        if window and is_pane_maximized(window):
            settings = window.settings()
            active_group = window.active_group()

            # Is the active group the group that is maximized?
            maximized_pane_group = settings.get( 'maximized_pane_group' )

            # print( 'maximized_pane_group', maximized_pane_group, 'active_group', active_group )
            if maximized_pane_group is not None and maximized_pane_group != active_group:
                origami_fraction = settings.get('origami_fraction')

                def unmaximize():

                    if origami_fraction:
                        window.run_command('unzoom_pane')

                    else:
                        window.run_command('unmaximize_pane')

                    # print( 'unmaximize_pane', 'origami_fraction', origami_fraction )
                    sublime.set_timeout( maximize, 100 )

                def maximize():

                    if origami_fraction:
                        window.run_command('zoom_pane', { 'fraction': origami_fraction })

                    else:
                        window.run_command('maximize_pane')

                    # print( 'maximize_pane', 'origami_fraction', origami_fraction )
                    sublime.set_timeout( disable, 100 )

                # print( 'begin', 'origami_fraction', origami_fraction )
                sublime.set_timeout( unmaximize, 100 )

            else:
                # print( 'end' )
                disable()

        else:
            # print( 'maximized False' )
            disable()

