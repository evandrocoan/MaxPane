import sublime
import sublime_plugin


g_is_running = False
g_allowed_command_to_change_focus = {
    "travel_to_pane",
    "carry_file_to_pane",
    "clone_file_to_pane",
    "create_pane",
    "destroy_pane",
    "create_pane_with_file",
    "set_layout",
    "project_manager",
    "new_pane",
    "focus_group",
    "move_to_group",
    "origami_move_to_group",
    "drag_select",
    "jump_back",
    "jump_forward",
    "my_jump_back",
    "my_jump_forward",
    "context_menu",
}


# https://stackoverflow.com/questions/128573/using-property-on-classmethods
class StateMeta(type):

    def __init__(cls, *args, **kwargs):
        cls._can_switch_pane = False

    @property
    def can_switch_pane(cls):
        return cls._can_switch_pane

    @can_switch_pane.setter
    def can_switch_pane(cls, timeout):
        cls._can_switch_pane = True
        sublime.set_timeout( cls.can_switch_pane_restart, timeout )


class State(metaclass=StateMeta):

    @classmethod
    def can_switch_pane_restart(cls):
        cls._can_switch_pane = False


def fixed_set_layout(window, layout):
    # https://github.com/SublimeTextIssues/Core/issues/2919
    active_group = window.active_group()
    window.set_layout( layout )
    window.focus_group( active_group )


def is_pane_maximized(window):
    return window.settings().get( 'original_panes_layout' )


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
        settings = window.settings()
        max_pane_maximized = settings.get( 'max_pane_maximized' )
        origami_fraction = settings.get( 'origami_fraction' )
        original_panes_layout = settings.get( 'original_panes_layout' )

        # print( 'max_pane max_pane_maximized %-5s, origami_fraction: %-5s, original_panes_layout, %-5s' % ( max_pane_maximized, origami_fraction, original_panes_layout is not None ) )
        if is_pane_maximized( window ):

            if max_pane_maximized:
                    window.run_command( 'unmaximize_pane' )

            else:

                if origami_fraction:
                    window.run_command( 'maximize_pane', { 'skip_saving': True } )

                else:
                    print( "MaxPane Error: Invalid maximizing state!" )
                    window.run_command( 'unmaximize_pane' )

        else:
            num_groups = window.num_groups()

            if num_groups > 1:
                window.run_command( 'maximize_pane' )

            else:
                print( "MaxPane Error: Cannot zoom a window only with '%s' panes!" % num_groups )


class MaximizePaneCommand(sublime_plugin.WindowCommand):
    def run(self, skip_saving=False):
        global g_is_running
        g_is_running = True

        window = self.window
        settings = window.settings()

        origami_fraction = settings.get( 'origami_fraction' )
        original_panes_layout = settings.get( 'original_panes_layout' )

        if not skip_saving and ( origami_fraction or original_panes_layout ):
            print("MaxPane Error: Trying to maximize a maximized pane!")
            window.run_command('unmaximize_pane')
            return

        layout = window.layout()
        active_group = window.active_group()

        if not skip_saving:
            settings.set( 'original_panes_layout', layout )

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

        settings.set( 'origami_fraction', None )
        settings.set( 'max_pane_maximized', True )
        settings.set( 'maximized_pane_group', active_group )

        fixed_set_layout( window, layout )
        g_is_running = False


class UnmaximizePaneCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = self.window
        settings = window.settings()

        settings.set( 'origami_fraction', None )
        settings.set( 'max_pane_maximized', False )
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

    def on_text_command(self, view, command_name, args):
        self.on_window_command( view.window(), command_name, args )

    def on_window_command(self, window, command_name, args):

        # https://github.com/SublimeTextIssues/Core/issues/2932
        if command_name == 'force_restoring_views_scrolling':
            State.can_switch_pane = 10000

        elif command_name in g_allowed_command_to_change_focus:
            State.can_switch_pane = 2000

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

        if window and is_pane_maximized( window ):
            settings = window.settings()
            active_group = window.active_group()

            # Is the active group the group that is maximized?
            maximized_pane_group = settings.get( 'maximized_pane_group' )

            # print( 'maximized_pane_group', maximized_pane_group, 'active_group', active_group )
            if maximized_pane_group is not None and maximized_pane_group != active_group:

                # https://github.com/SublimeTextIssues/Core/issues/2932
                if State.can_switch_pane:
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
                    original_view = window.active_view_in_group( maximized_pane_group )
                    original_pane_group, original_view_index = window.get_view_index( original_view )

                    view = window.active_view()
                    viewport_position = view.viewport_position()
                    view_group, view_index = window.get_view_index( view )

                    print( "[MaxPane] Cloning opened view %s from group %s[%s] to %s[%s]... %s" % (
                            viewport_position,
                            view_group + 1,
                            view_index,
                            original_pane_group + 1,
                            original_view_index + 1,
                            view.file_name() ) )

                    # If we move the cloned file's tab to the left of the original's,
                    # then when we remove it from the group, focus will fall to the
                    # original view.
                    window.run_command( 'clone_file' )
                    cloned_view = window.active_view()

                    def fix_view_focus():
                        cloned_view_selections = cloned_view.sel()
                        cloned_view_selections.clear()

                        for selection in view.sel():
                            cloned_view_selections.add( selection )

                        # if cloned_view_selections: cloned_view.show_at_center( cloned_view_selections[0].begin() )
                        cloned_view.set_viewport_position( viewport_position )

                    # sublime.set_timeout( lambda: window.set_view_index( view, view_group, view_index ), 0 )
                    sublime.set_timeout( lambda: window.set_view_index( cloned_view, original_pane_group, original_view_index + 1 ), 100 )
                    sublime.set_timeout( lambda: window.focus_view( cloned_view ), 250 )
                    sublime.set_timeout( fix_view_focus, 500 )
                    sublime.set_timeout( disable, 1000 )

            else:
                # print( 'end' )
                disable()

        else:
            # print( 'maximized False' )
            disable()

