from __future__ import unicode_literals

from .base import Border

from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window, FloatContainer, Float, ConditionalContainer
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.widgets import Shadow
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.utils import get_cwidth

__all__ = (
    'MenuContainer',
    'MenuItem',
)


class MenuContainer(object):
    """
    :param floats: List of extra Float objects to display.
    """
    def __init__(self, body, menu_items=None, floats=None, key_bindings=None):
        assert isinstance(menu_items, list) and \
            all(isinstance(i, MenuItem) for i in menu_items)
        assert floats is None or all(isinstance(f, Float) for f in floats)

        self.body = body
        self.menu_items = menu_items
        self.selected_menu = [0]

        # Key bindings.
        kb = KeyBindings()

        @Condition
        def in_main_menu(app):
            return len(self.selected_menu) == 1

        @Condition
        def in_sub_menu(app):
            return len(self.selected_menu) > 1

        # Navigation through the main menu.

        @kb.add('left', filter=in_main_menu)
        def _(event):
            self.selected_menu[0] = max(0, self.selected_menu[0] - 1)

        @kb.add('right', filter=in_main_menu)
        def _(event):
            self.selected_menu[0] = min(
                len(self.menu_items) - 1, self.selected_menu[0] + 1)

        @kb.add('down', filter=in_main_menu)
        def _(event):
            self.selected_menu.append(0)

        @kb.add('c-c', filter=in_main_menu)
        @kb.add('c-g', filter=in_main_menu)
        def _(event):
            " Leave menu. "
            layout = event.app.layout
            layout.focus_previous()

        # Sub menu navigation.

        @kb.add('left', filter=in_sub_menu)
        @kb.add('c-g', filter=in_sub_menu)
        @kb.add('c-c', filter=in_sub_menu)
        def _(event):
            " Go back to parent menu. "
            if len(self.selected_menu) > 1:
                self.selected_menu.pop()

        @kb.add('right', filter=in_sub_menu)
        def _(event):
            " go into sub menu. "
            if self._get_menu(len(self.selected_menu) - 1).children:
                self.selected_menu.append(0)

            # If This item does not have a sub menu. Go up in the parent menu.
            elif len(self.selected_menu) == 2 and self.selected_menu[0] < len(self.menu_items) - 1:
                self.selected_menu = [min(
                    len(self.menu_items) - 1, self.selected_menu[0] + 1)]
                if self.menu_items[self.selected_menu[0]].children:
                    self.selected_menu.append(0)

        @kb.add('up', filter=in_sub_menu)
        def _(event):
            if len(self.selected_menu) == 2 and self.selected_menu[1] == 0:
                self.selected_menu.pop()
            elif self.selected_menu[-1] > 0:
                self.selected_menu[-1] -= 1

        @kb.add('down', filter=in_sub_menu)
        def _(event):
            if self.selected_menu[-1] < len(self._get_menu(len(self.selected_menu) - 2).children) - 1:
                self.selected_menu[-1] += 1

        @kb.add('enter')
        def _(event):
            " Click the selected menu item. "
            item = self._get_menu(len(self.selected_menu) - 1)
            if item.handler:
                event.app.layout.focus_previous()
                item.handler(event.app)

        # Controls.
        self.control = FormattedTextControl(
            self._get_menu_fragments,
            key_bindings=kb,
            focussable=True,
            show_cursor=False)

        self.window = Window(
            height=1,
            content=self.control,
            style='class:menu-bar')

        submenu = self._submenu(0)
        submenu2 = self._submenu(1)
        submenu3 = self._submenu(2)

        @Condition
        def has_focus(app):
            return app.layout.current_window == self.window

        self.container = FloatContainer(
            content=HSplit([
                # The titlebar.
                self.window,

                # The 'body', like defined above.
                body,
            ]),
            floats=[
                Float(xcursor=self.window, ycursor=self.window,
                      content=ConditionalContainer(
                          content=Shadow(body=submenu),
                          filter=has_focus)),
                Float(attach_to_window=submenu,
                      xcursor=True, ycursor=True,
                      allow_cover_cursor=True,
                      content=ConditionalContainer(
                          content=Shadow(body=submenu2),
                          filter=has_focus & Condition(lambda app: len(self.selected_menu) >= 1))),
                Float(attach_to_window=submenu2,
                      xcursor=True, ycursor=True,
                      allow_cover_cursor=True,
                      content=ConditionalContainer(
                          content=Shadow(body=submenu3),
                          filter=has_focus & Condition(lambda app: len(self.selected_menu) >= 2))),

                # --
            ] + (floats or []),
            key_bindings=key_bindings,
        )

    def _get_menu(self, level):
        menu = self.menu_items[self.selected_menu[0]]

        for i, index in enumerate(self.selected_menu[1:]):
            if i < level:
                try:
                    menu = menu.children[index]
                except IndexError:
                    return MenuItem('debug')

        return menu

    def _get_menu_fragments(self, app):
        focussed = app.layout.has_focus(self.window)

        # This is called during the rendering. When we discover that this
        # widget doesn't have the focus anymore. Reset menu state.
        if not focussed:
            self.selected_menu = [0]

        # Generate text fragments for the main menu.
        def one_item(i, item):
            def mouse_handler(app, mouse_event):
                if mouse_event.event_type == MouseEventType.MOUSE_UP:
                    # Toggle focus.
                    if app.layout.has_focus(self.window):
                        if self.selected_menu == [i]:
                            app.layout.focus_previous()
                    else:
                        app.layout.focus(self.window)
                    self.selected_menu = [i]

            yield ('class:menu-bar', ' ', mouse_handler)
            if i == self.selected_menu[0] and focussed:
                yield ('[SetMenuPosition]', '', mouse_handler)
                style = 'class:menu-bar.selected-item'
            else:
                style = 'class:menu-bar'
            yield style, item.text, mouse_handler

        result = []
        for i, item in enumerate(self.menu_items):
            result.extend(one_item(i, item))

        return result

    def _submenu(self, level=0):
        def get_text_fragments(app):
            result = []
            if level < len(self.selected_menu):
                menu = self._get_menu(level)
                if menu.children:
                    result.append(('class:menu', Border.TOP_LEFT))
                    result.append(('class:menu', Border.HORIZONTAL * (menu.width + 4)))
                    result.append(('class:menu', Border.TOP_RIGHT))
                    result.append(('', '\n'))
                    try:
                        selected_item = self.selected_menu[level + 1]
                    except IndexError:
                        selected_item = -1

                    def one_item(i, item):
                        def mouse_handler(app, mouse_event):
                            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                                if item.handler:
                                    app.layout.focus_previous()
                                    item.handler(app)
                                else:
                                    self.selected_menu = self.selected_menu[:level + 1] + [i]

                        if i == selected_item:
                            yield ('[SetCursorPosition]', '')
                            style = 'class:menu-bar.selected-item'
                        else:
                            style = ''

                        yield ('class:menu', Border.VERTICAL)
                        if item.text == '-':
                            yield (style + 'class:menu-border',
                                   '{}'.format(Border.HORIZONTAL * (menu.width + 3)),
                                   mouse_handler)
                        else:
                            yield (style, ' {}'.format(item.text).ljust(menu.width + 3),
                                   mouse_handler)

                        if item.children:
                            yield (style, '>', mouse_handler)
                        else:
                            yield (style, ' ', mouse_handler)

                        if i == selected_item:
                            yield ('[SetMenuPosition]', '')
                        yield ('class:menu', Border.VERTICAL)

                        yield ('', '\n')

                    for i, item in enumerate(menu.children):
                        result.extend(one_item(i, item))

                    result.append(('class:menu', Border.BOTTOM_LEFT))
                    result.append(('class:menu', Border.HORIZONTAL * (menu.width + 4)))
                    result.append(('class:menu', Border.BOTTOM_RIGHT))
            return result

        return Window(
            FormattedTextControl(get_text_fragments),
            style='class:menu',
            transparent=False)

    @property
    def floats(self):
        return self.container.floats

    def __pt_container__(self):
        return self.container


class MenuItem(object):
    def __init__(self, text='', handler=None, children=None, shortcut=None,
                 disabled=False):
        self.text = text
        self.handler = handler
        self.children = children or []
        self.shortcut = shortcut
        self.disabled = disabled
        self.selected_item = 0

    @property
    def width(self):
        if self.children:
            return max(get_cwidth(c.text) for c in self.children)
        else:
            return 0
