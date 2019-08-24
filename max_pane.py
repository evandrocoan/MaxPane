import sublime
import sublime_plugin

import datetime

debug_events = print
debug_events = lambda *args: None

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
    "open_recently_closed_file",
}


class timestamp(object):
    def __repr__(self):
        return "%s" % (
                datetime.datetime.now(),
            )

# Allows to pass get_selections_stack as a function parameter without evaluating/creating its string!
timestamp = timestamp()


# https://stackoverflow.com/questions/128573/using-property-on-classmethods
class StateMeta(type):

    def __init__(cls, *args, **kwargs):
        cls._disable_timeout = False
        cls._can_switch_pane = False

    @property
    def disable_timeout(cls):
        return cls._disable_timeout

    @disable_timeout.setter
    def disable_timeout(cls, value):
        cls._disable_timeout = value
        cls._can_switch_pane = value

    @property
    def can_switch_pane(cls):
        return cls._can_switch_pane

    @can_switch_pane.setter
    def can_switch_pane(cls, timeout):
        cls._can_switch_pane = True

        if not cls.disable_timeout:
            sublime.set_timeout( cls.can_switch_pane_restart, timeout )


class State(metaclass=StateMeta):
    is_fixing_layout = False

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

        debug_events( timestamp, 'max_pane max_pane_maximized %-5s, origami_fraction: %-5s, original_panes_layout, %-5s' % ( max_pane_maximized, origami_fraction, original_panes_layout is not None ) )
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
        State.is_fixing_layout = True

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
        State.is_fixing_layout = False


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
        if command_name in g_allowed_command_to_change_focus:
            State.can_switch_pane = 2000

            # Fix Sublime Text not focusing the active group when using result_file_regex double click
            active_group = window.active_group()
            window.focus_group( active_group )

    def on_activated(self, view):
        debug_events( timestamp, 'Entering State.is_fixing_layout', State.is_fixing_layout )
        if State.is_fixing_layout: return

        # Is the window currently maximized?
        State.is_fixing_layout = True
        window = view.window() or sublime.active_window()

        def disable():
            State.is_fixing_layout = False

        if window and is_pane_maximized( window ):
            settings = window.settings()
            active_group = window.active_group()

            # Is the active group the group that is maximized?
            maximized_pane_group = settings.get( 'maximized_pane_group' )

            debug_events( timestamp, 'maximized_pane_group', maximized_pane_group, 'active_group', active_group )
            if maximized_pane_group is not None and maximized_pane_group != active_group:

                # https://github.com/SublimeTextIssues/Core/issues/2932
                if State.can_switch_pane:
                    origami_fraction = settings.get('origami_fraction')

                    def unmaximize():

                        if origami_fraction:
                            window.run_command('unzoom_pane')

                        else:
                            window.run_command('unmaximize_pane')

                        debug_events( timestamp, 'unmaximize_pane', 'origami_fraction', origami_fraction )
                        sublime.set_timeout( maximize, 100 )

                    def maximize():

                        if origami_fraction:
                            window.run_command('zoom_pane', { 'fraction': origami_fraction })

                        else:
                            window.run_command('maximize_pane')

                        debug_events( timestamp, 'maximize_pane', 'origami_fraction', origami_fraction )
                        sublime.set_timeout( disable, 100 )

                    debug_events( timestamp, 'begin', 'origami_fraction', origami_fraction )
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
                        restore_view( view, window, lambda: None )

                    # sublime.set_timeout( lambda: window.set_view_index( view, view_group, view_index ), 0 )
                    sublime.set_timeout( lambda: window.set_view_index( cloned_view, original_pane_group, original_view_index + 1 ), 100 )
                    sublime.set_timeout( lambda: window.focus_view( cloned_view ), 250 )
                    sublime.set_timeout( fix_view_focus, 500 )
                    sublime.set_timeout( disable, 1000 )

            else:
                debug_events( timestamp, 'end' )
                disable()

        else:
            debug_events( timestamp, 'maximized False' )
            disable()


TIME_AFTER_FOCUS_VIEW = 30
TIME_AFTER_RESTORE_VIEW = 15

def restore_view(view, window, next_target, withfocus=True):
    """ Taken from the https://github.com/evandrocoan/FixProjectSwitchRestartBug package """

    if view.is_loading():
        sublime.set_timeout( lambda: restore_view( view, window, next_target, withfocus=withfocus ), 200 )

    else:
        selections = view.sel()
        file_name = view.file_name()

        if len( selections ):
            first_selection = selections[0].begin()
            original_selections = list( selections )

            def super_refocus():
                view.run_command( "move", {"by": "lines", "forward": False} )
                view.run_command( "move", {"by": "lines", "forward": True} )

                def fix_selections():
                    selections.clear()

                    for selection in original_selections:
                        selections.add( selection )

                    sublime.set_timeout( next_target, TIME_AFTER_RESTORE_VIEW )

                sublime.set_timeout( fix_selections, TIME_AFTER_RESTORE_VIEW )

            if file_name and withfocus:

                def reforce_focus():
                    # https://github.com/SublimeTextIssues/Core/issues/1482
                    group, view_index = window.get_view_index( view )
                    window.set_view_index( view, group, 0 )

                    # https://github.com/SublimeTextIssues/Core/issues/538
                    row, column = view.rowcol( first_selection )
                    window.open_file( "%s:%d:%d" % ( file_name, row + 1, column + 1 ), sublime.ENCODED_POSITION )
                    window.set_view_index( view, group, view_index )

                    # print( 'Super reforce focus focusing...' )
                    sublime.set_timeout( super_refocus, TIME_AFTER_RESTORE_VIEW )

                view.show_at_center( first_selection )
                sublime.set_timeout( reforce_focus, TIME_AFTER_FOCUS_VIEW )

            else:
                view.show_at_center( first_selection )
                sublime.set_timeout( super_refocus, TIME_AFTER_RESTORE_VIEW )
