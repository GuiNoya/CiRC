#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
 =========================================================================
 |
 | CiRC (CiRC is to Read Comics) 0.1 - GTK Comic Book Viewer in Python
 | Copyright (C) 2012 Guilherme Pereira Nóya
 | <gui_noya@hotmail.com>
 | <gui.noya@gmail.com>
 |
 =========================================================================
 |
 | This program is free software: you can redistribute it and/or modify
 | it under the terms of the GNU General Public License as published by
 | the Free Software Foundation, either version 3 of the License, or
 | (at your option) any later version.
 |
 | This program is distributed in the hope that it will be useful,
 | but WITHOUT ANY WARRANTY; without even the implied warranty of
 | MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 | GNU General Public License for more details.
 |
 | You should have received a copy of the GNU General Public License
 | along with this program.  If not, see <http://www.gnu.org/licenses/>.
 |
 =========================================================================
"""

#TODO: FIX: press enter on goto dialog
#TODO: ADD: icon
#TODO: FIX: 7z writting things. (Try to use -so on cmd and then
#            get the stream and put on temporary files)
#TODO: ADD: README, INSTRUCTIONS and CHANGELOG files
#TODO: FIX: Better descriptions
#TODO: Better way to "install" the program
#TODO: Rewrite the code to be modularized (I was adding things little by little and became this mess)

from __future__ import division

import os
import sys
import gc
import subprocess

import shutil
import tempfile
import zipfile
import tarfile

try:
    import pygtk
    pygtk.require('2.0')
    import gtk
except:
    print("Couldn't find any version of PyGTK2 on your system!")
    print("Version 2.8.0 of PyGTK is required.")
    sys.exit(1)
try:
    assert gtk.pygtk_version >= (2, 8, 0)
    assert gtk.gtk_version >= (2, 8, 0)
except AssertionError:
    print("Found version " + ".".join(str(num) for num in (gtk.gtk_version)) + \
            " of PyGTK.")
    print("Version 2.8.0 or higher of PyGTK is required!")
    print("Found version " + ".".join(str(num) for num in (gtk.gtk_version)) + \
            " of GTK+.")
    print("Version 2.8.0 or higher of GTK+ is required!")
    sys.exit(1)

RAR_ID = bytes("Rar!\x1a\x07\x00")
SEVENZIP_ID = bytes("7z\xbc\xaf\x27\x1c")

class circ:
    """This class is almost the whole program."""

    prefs = {'start maximized': 1,
            'window x position': -1,
            'window y position': -1,
            'window x size': 600,
            'window y size': 400,
            'window is maximized': 1,
            'open option': 0,
            'first path': os.environ['HOME']}

    version = '0.1'
    files_list = []
    image_index = -1
    is_fullscreen = False
    _temp_dir = tempfile.mkdtemp(dir=tempfile.gettempdir(),
                                    prefix="circ-", suffix=os.sep)
    _config_dir = os.path.join(os.environ['HOME'],
                                os.path.join('.config', 'circ'))

    def create_main_window(self):
        """Creates the main window."""
        #---------------------
        # Create the objects
        #---------------------
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.realize()
        self.image = gtk.Image()
        self.layout = gtk.Layout()
        self.menubar = gtk.MenuBar()
        self.toolbar = gtk.Toolbar()

        #---------------------
        # Setup the MenuBar
        #---------------------
        self.file_menu = gtk.Menu()
        self.view_menu = gtk.Menu()
        self.go_menu = gtk.Menu()
        self.help_menu = gtk.Menu()
        self.accel_group = gtk.AccelGroup()
        self.window.add_accel_group(self.accel_group)

        # File Menu
        self.file_menuitem = gtk.MenuItem('_File')
        self.file_menuitem.set_submenu(self.file_menu)

        self.open_menuitem = gtk.ImageMenuItem(gtk.STOCK_OPEN, self.accel_group)
        self.open_menuitem.connect('activate', self.show_open_dialog)
        self.separator_menuitem = gtk.SeparatorMenuItem()
        self.close_book_menuitem = gtk.ImageMenuItem(gtk.STOCK_CLOSE, self.accel_group)
        self.close_book_menuitem.connect('activate', self.close_book)
        self.close_book_menuitem.set_label('Close book')
        self.separator_menuitem2 = gtk.SeparatorMenuItem()
        self.quit_menuitem = gtk.ImageMenuItem(gtk.STOCK_QUIT, self.accel_group)
        self.quit_menuitem.connect('activate', self.close_program)

        self.file_menu.append(self.open_menuitem)
        self.file_menu.append(self.separator_menuitem)
        self.file_menu.append(self.close_book_menuitem)
        self.file_menu.append(self.separator_menuitem2)
        self.file_menu.append(self.quit_menuitem)

        # View Menu
        self.view_menuitem = gtk.MenuItem('_View')
        self.view_menuitem.set_submenu(self.view_menu)

        self.fullscreen_menuitem = gtk.ImageMenuItem(gtk.STOCK_FULLSCREEN, self.accel_group)
        self.fullscreen_menuitem.connect('activate', self.toggle_fullscreen)
        self.fullscreen_menuitem.add_accelerator('activate', self.accel_group,
                                                gtk.keysyms.F11, 0,
                                                gtk.ACCEL_VISIBLE|gtk.ACCEL_LOCKED)
        self.preferences_menuitem = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES, self.accel_group)
        self.preferences_menuitem.connect('activate', self.show_preferences_dialog)

        self.view_menu.append(self.preferences_menuitem)
        self.view_menu.append(self.fullscreen_menuitem)

        # Go Menu
        self.go_menuitem = gtk.MenuItem('_Go')
        self.go_menuitem.set_submenu(self.go_menu)

        self.first_page_menuitem = gtk.ImageMenuItem(gtk.STOCK_GOTO_FIRST, self.accel_group)
        self.prev_page_menuitem = gtk.ImageMenuItem(gtk.STOCK_GO_BACK, self.accel_group)
        self.next_page_menuitem = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD, self.accel_group)
        self.last_page_menuitem = gtk.ImageMenuItem(gtk.STOCK_GOTO_LAST, self.accel_group)
        self.first_page_menuitem.set_label('_First Page')
        self.prev_page_menuitem.set_label('_Previous Page')
        self.next_page_menuitem.set_label('_Next Page')
        self.last_page_menuitem.set_label('_Last Page')
        self.first_page_menuitem.connect('activate', self.first_page)
        self.prev_page_menuitem.connect('activate', self.previous_page)
        self.next_page_menuitem.connect('activate', self.next_page)
        self.last_page_menuitem.connect('activate', self.last_page)
        self.separator_menuitem3 = gtk.SeparatorMenuItem()
        self.goto_menuitem = gtk.ImageMenuItem(gtk.STOCK_JUMP_TO, self.accel_group)
        self.goto_menuitem.set_label('_Go to page...')
        self.goto_menuitem.connect('activate', self.show_goto_dialog)
        self.first_page_menuitem.add_accelerator('activate', self.accel_group,
                                                gtk.keysyms.Home, 0,
                                                gtk.ACCEL_VISIBLE|gtk.ACCEL_LOCKED)
        self.prev_page_menuitem.add_accelerator('activate', self.accel_group,
                                                gtk.keysyms.Page_Up, 0,
                                                gtk.ACCEL_VISIBLE|gtk.ACCEL_LOCKED)
        self.next_page_menuitem.add_accelerator('activate', self.accel_group,
                                                gtk.keysyms.Page_Down, 0,
                                                gtk.ACCEL_VISIBLE|gtk.ACCEL_LOCKED)
        self.last_page_menuitem.add_accelerator('activate', self.accel_group,
                                                gtk.keysyms.End, 0,
                                                gtk.ACCEL_VISIBLE|gtk.ACCEL_LOCKED)
        self.goto_menuitem.add_accelerator('activate', self.accel_group,
                                            gtk.keysyms.g, 0,
                                            gtk.ACCEL_VISIBLE|gtk.ACCEL_LOCKED)

        self.go_menu.append(self.first_page_menuitem)
        self.go_menu.append(self.prev_page_menuitem)
        self.go_menu.append(self.next_page_menuitem)
        self.go_menu.append(self.last_page_menuitem)
        self.go_menu.append(self.separator_menuitem3)
        self.go_menu.append(self.goto_menuitem)

        # Help Menu
        self.help_menuitem = gtk.MenuItem('_Help')
        self.help_menuitem.set_submenu(self.help_menu)

        self.about_menuitem = gtk.ImageMenuItem(gtk.STOCK_ABOUT, self.accel_group)
        self.about_menuitem.connect('activate', self.show_about_dialog)

        self.help_menu.append(self.about_menuitem)

        # Put the menus on the bar
        self.menubar.append(self.file_menuitem)
        self.menubar.append(self.view_menuitem)
        self.menubar.append(self.go_menuitem)
        self.menubar.append(self.help_menuitem)
        self.menubar.show_all()

        #---------------------
        # Setup the Toolbar
        #---------------------
        self.toolbutton_first_page = gtk.ToolButton(gtk.STOCK_GOTO_FIRST)
        self.toolbutton_previous_page = gtk.ToolButton(gtk.STOCK_GO_BACK)
        self.toolbutton_next_page = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
        self.toolbutton_last_page = gtk.ToolButton(gtk.STOCK_GOTO_LAST)
        self.toolbutton_first_page.connect('clicked', self.first_page)
        self.toolbutton_previous_page.connect('clicked', self.previous_page)
        self.toolbutton_next_page.connect('clicked', self.next_page)
        self.toolbutton_last_page.connect('clicked', self.last_page)
        self.toolitem = gtk.ToolItem()
        self.toolitem.set_expand(True)
        self.toolitem2 = gtk.ToolItem()
        self.toolitem2.set_expand(True)
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.toolbar.insert(self.toolitem, -1)
        self.toolbar.insert(self.toolbutton_first_page, -1)
        self.toolbar.insert(self.toolbutton_previous_page, -1)
        self.toolbar.insert(self.toolbutton_next_page, -1)
        self.toolbar.insert(self.toolbutton_last_page, -1)
        self.toolbar.insert(self.toolitem2, -1)
        self.toolbar.set_can_focus(False)
        self.toolbutton_first_page.set_can_focus(False)
        self.toolbutton_previous_page.set_can_focus(False)
        self.toolbutton_next_page.set_can_focus(False)
        self.toolbutton_last_page.set_can_focus(False)
        self.toolbutton_first_page.set_tooltip_text('First page')
        self.toolbutton_previous_page.set_tooltip_text('Previous page')
        self.toolbutton_next_page.set_tooltip_text('Next page')
        self.toolbutton_last_page.set_tooltip_text('Last page')

        #---------------------
        # Setup the Scrollbars
        #---------------------
        self.vadjust = self.layout.get_vadjustment()
        self.hadjust = self.layout.get_hadjustment()
        self.vadjust.page_increment = 100
        self.vadjust.step_increment = 60
        self.hadjust.page_increment = 100
        self.hadjust.step_increment = 60
        self.vscrollbar = gtk.VScrollbar(self.vadjust)
        self.hscrollbar = gtk.HScrollbar(self.hadjust)

        #---------------------
        # Configure the gtk.Layout
        #---------------------
        self.layout.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("black"))
        self.layout_eventbox = gtk.EventBox()
        self.layout.put(self.image, 0, 0)
        self.layout.put(self.layout_eventbox, 0, 0)
        self.layout.set_events(gtk.gdk.BUTTON1_MOTION_MASK |
            gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.KEY_PRESS_MASK |
            gtk.gdk.KEY_RELEASE_MASK)
        self.layout.connect("scroll-event", self.scroll_wheel_event)
        self.layout.connect("button-press-event", self.button_press_event)
        self.layout.connect("button-release-event", self.button_release_event)
        self.layout.connect("motion-notify-event", self.mouse_motion_event)
        self.layout.connect("key-press-event", self.key_press_event)
        self.layout.set_can_focus(True)

        #---------------------
        # Add the widgets to the window
        #---------------------
        self.table = gtk.Table(2, 2, False)
        self.table.attach(self.layout, 0, 1, 0, 1, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL, 0, 0)
        self.table.attach(self.vscrollbar, 1, 2, 0, 1, gtk.SHRINK|gtk.FILL, gtk.FILL, 0, 0)
        self.table.attach(self.hscrollbar, 0, 1, 1, 2, gtk.FILL, gtk.SHRINK|gtk.FILL, 0, 0)
        self.main_box = gtk.VBox(False, 0)
        self.main_box.pack_start(self.menubar, False, True, 0)
        self.main_box.pack_start(self.table, True, True, 0)
        self.main_box.pack_start(self.toolbar, False, False, 0)
        self.window.add(self.main_box)

        #---------------------
        # Setup the window
        #---------------------
        self.window.set_title("CiRC")
        #self.window.connect("destroy", self.close_program)
        self.window.connect("delete-event", self.close_program)
        self.window.connect("configure-event", self.allocate_image)
        self.window.connect("window-state-event", self.window_state_event)
        self.window.set_resize_mode(gtk.RESIZE_IMMEDIATE)
        self.window.set_size_request(600, 400)
        self.window.set_resizable(True)
        self.window.resize(int(self.prefs['window x size']),
                            int(self.prefs['window y size']))
        if self.prefs['window x position'] >= 0 and \
            self.prefs['window y position'] >= 0:
            self.window.move(int(self.prefs['window x position']),
                            int(self.prefs['window y position']))
        else:
            self.window.set_position(gtk.WIN_POS_CENTER)
        if bool(int(self.prefs['start maximized'])) or \
            bool(int(self.prefs['window is maximized'])):
            self.window.maximize()

    def load_image(self, image):
        """Load and show the image."""
        self.image.set_from_file(str(image))
        self.allocate_image()
        self.vadjust.value = 0
        self.hadjust.value = 0
        self.file_name = os.path.basename(image)
        self.window.set_title("[" + str(self.image_index+1) + "/" + \
                            str(len(self.files_list)) + "] - " + \
                            os.path.join(self.file_parent, self.file_name) + \
                            " - CiRC")
        self.refresh_active_widgets()
        self.layout.grab_focus()

    def recalculate_sizes(self):
        """Recaculate the borders of the window."""
        if not self.is_fullscreen:
            (self.visible_img_hsize,
            self.visible_img_vsize) = self.window.get_size()
            self.visible_img_vsize -= self.menubar.size_request()[1]
            self.visible_img_vsize -= self.hscrollbar.size_request()[1]
            self.visible_img_vsize -= self.toolbar.size_request()[1]
            self.visible_img_hsize -= self.vscrollbar.size_request()[0]
            (self.image_hsize,
            self.image_vsize) = self.image.size_request()
        else:
            (self.visible_img_hsize,
            self.visible_img_vsize) = self.window.get_size()
            (self.image_hsize,
            self.image_vsize) = self.image.size_request()

    def allocate_image(self, event=None, data=None):
        """Handle the work to arrange the image and the layout on the window."""
        self.recalculate_sizes()
        if (not self.image_hsize) or (not self.image_vsize):
            self.layout.set_size(1, 1)
            self.image_v_pos = 0
            self.image_h_pos = 0
        else:
            if self.image_hsize >= self.visible_img_hsize:
                self.image_h_pos = 0
            else:
                self.image_h_pos = (self.visible_img_hsize//2)-(self.image_hsize//2)
            if self.image_vsize >= self.visible_img_vsize:
                self.image_v_pos = 0
            else:
                self.image_v_pos = (self.visible_img_vsize//2)-(self.image_vsize//2)
            self.layout.set_size(self.image_hsize, self.image_vsize)
        self.layout.move(self.image, self.image_h_pos, self.image_v_pos)

    def next_page(self, event=None):
        """Goes to the next page."""
        if self.image_index < len(self.files_list) - 1:
            self.image_index += 1
            self.load_image(self.files_list[self.image_index])
            self.vadjust.value = 0
            self.hadjust.value = 0

    def previous_page(self, event=None):
        """Goes to the previous page."""
        if self.image_index > 0:
            self.image_index -= 1
            self.load_image(self.files_list[self.image_index])
            self.vadjust.value = 0
            self.hadjust.value = 0
            return True

    def first_page(self, event=None):
        """Goes to the first page of the list."""
        self.image_index = 0
        self.load_image(self.files_list[0])
        self.vadjust.value = 0
        self.hadjust.value = 0

    def last_page(self, event=None):
        """Goes to the last page of the list."""
        self.image_index = len(self.files_list) - 1
        self.load_image(self.files_list[self.image_index])
        self.vadjust.value = 0
        self.hadjust.value = 0

    def refresh_active_widgets(self):
        """Reload the widgets that cannot be pressed."""
        if self.files_list:
            self.goto_menuitem.set_sensitive(True)
            self.close_book_menuitem.set_sensitive(True)
            if self.image_index == 0:
                self.toolbutton_first_page.set_sensitive(False)
                self.toolbutton_previous_page.set_sensitive(False)
                self.first_page_menuitem.set_sensitive(False)
                self.prev_page_menuitem.set_sensitive(False)
                self.popup_prev_menuitem.set_sensitive(False)
            else:
                self.toolbutton_first_page.set_sensitive(True)
                self.toolbutton_previous_page.set_sensitive(True)
                self.first_page_menuitem.set_sensitive(True)
                self.prev_page_menuitem.set_sensitive(True)
                self.popup_prev_menuitem.set_sensitive(True)
            if self.image_index == len(self.files_list) - 1:
                self.toolbutton_next_page.set_sensitive(False)
                self.toolbutton_last_page.set_sensitive(False)
                self.next_page_menuitem.set_sensitive(False)
                self.last_page_menuitem.set_sensitive(False)
                self.popup_next_menuitem.set_sensitive(False)
            else:
                self.toolbutton_next_page.set_sensitive(True)
                self.toolbutton_last_page.set_sensitive(True)
                self.next_page_menuitem.set_sensitive(True)
                self.last_page_menuitem.set_sensitive(True)
                self.popup_next_menuitem.set_sensitive(True)
        else:
            self.toolbutton_first_page.set_sensitive(False)
            self.toolbutton_previous_page.set_sensitive(False)
            self.toolbutton_next_page.set_sensitive(False)
            self.toolbutton_last_page.set_sensitive(False)
            self.first_page_menuitem.set_sensitive(False)
            self.prev_page_menuitem.set_sensitive(False)
            self.next_page_menuitem.set_sensitive(False)
            self.last_page_menuitem.set_sensitive(False)
            self.goto_menuitem.set_sensitive(False)
            self.popup_prev_menuitem.set_sensitive(False)
            self.popup_next_menuitem.set_sensitive(False)
            self.close_book_menuitem.set_sensitive(False)

    def toggle_fullscreen(self, widget=None):
        """Toggle fullscreen state."""
        if not self.is_fullscreen:
            (self.window_hsize,
            self.window_vsize) = self.window.get_size()
            self.menubar.hide()
            self.vscrollbar.hide()
            self.hscrollbar.hide()
            self.toolbar.hide()
            self.window.fullscreen()
            self.popup_fullscreen_menuitem.set_active(True)
            self.is_fullscreen = True
        elif self.is_fullscreen:
            self.window.resize(self.window_hsize, self.window_vsize)
            self.menubar.show()
            self.vscrollbar.show()
            self.hscrollbar.show()
            self.toolbar.show()
            self.window.unfullscreen()
            self.popup_fullscreen_menuitem.set_active(False)
            self.is_fullscreen = False
        return True

    def scroll_image(self, v_dif, h_dif):
        """Scroll the image, vertically and horizontally."""
        self.vadjust_value = self.vadjust.get_value()
        self.hadjust_value = self.hadjust.get_value()
        if v_dif > 0:
            if self.visible_img_vsize - v_dif < self.image_vsize:
                if self.image_vsize - self.visible_img_vsize - self.vadjust.get_value() >= v_dif:
                    self.vadjust_value = self.vadjust.get_value() + v_dif
                else:
                    self.vadjust_value = self.image_vsize - self.visible_img_vsize
        elif v_dif < 0:
            if self.vadjust.get_value() > 0 and self.vadjust.get_value() > -v_dif:
                self.vadjust_value = self.vadjust.get_value() + v_dif
            else:
                self.vadjust_value = 0

        if h_dif > 0:
            if self.visible_img_hsize + self.hadjust.get_value() + h_dif < self.image_hsize:
                self.hadjust_value = self.hadjust.get_value() + h_dif
            else:
                self.hadjust_value = self.image_hsize- self.visible_img_hsize
        elif h_dif < 0:
            if self.hadjust.get_value() > 0 and self.hadjust.get_value() > -h_dif:
                self.hadjust_value = self.hadjust.get_value() + h_dif
            else:
                self.hadjust_value = 0
        self.vadjust.set_value(self.vadjust_value)
        self.hadjust.set_value(self.hadjust_value)

    def key_press_event(self, widget, event):
        """Handles the key bindings manually."""

        # Scroll image with the arrows keys
        if event.keyval == gtk.keysyms.Down:
            self.scroll_image(self.vadjust.step_increment, 0)
        elif event.keyval == gtk.keysyms.Up:
            self.scroll_image(-self.vadjust.step_increment, 0)
        elif event.keyval == gtk.keysyms.Right:
            self.scroll_image(0, self.hadjust.step_increment)
        elif event.keyval == gtk.keysyms.Left:
            self.scroll_image(0, -self.hadjust.step_increment)

        # Pressing the space, goes to the next image area to read
        elif event.keyval == gtk.keysyms.space:
            if self.hadjust.value < self.image_hsize - self.visible_img_hsize and \
                    self.image_hsize - self.visible_img_hsize > 0:
                self.scroll_image(0, self.visible_img_hsize - self.hadjust.step_increment)
            elif self.vadjust.value == self.image_vsize - self.visible_img_vsize or \
                    self.image_vsize - self.visible_img_vsize <= 0:
                self.next_page()
            else:
                self.scroll_image(self.visible_img_vsize - self.vadjust.step_increment, -self.hadjust.value)

        # Backspace return to the end of the previous page
        elif event.keyval == gtk.keysyms.BackSpace:
            if self.previous_page():
                self.scroll_image(self.image_vsize, self.image_hsize)

        # Now, take care of the Fullscreen
        elif event.keyval == gtk.keysyms.F11:
            self.toggle_fullscreen()
        elif event.keyval == gtk.keysyms.Escape and self.is_fullscreen:
            self.toggle_fullscreen()

        return True

    def scroll_wheel_event(self, widget, event):
        """Handles the scroll wheel."""
        if event.direction == gtk.gdk.SCROLL_DOWN:
            self.scroll_image(self.vadjust.step_increment, 0)
        elif event.direction == gtk.gdk.SCROLL_UP:
            self.scroll_image(-self.vadjust.step_increment, 0)

    def button_press_event(self, widget, event):
        """Handles the mouse button press."""
        if event.button in (1, 9):
            self.mouse_posx_old = event.x_root
            self.mouse_posy_old = event.y_root
            self.h_dif = 0
            self.v_dif = 0
        elif event.button == 3:
            self.popup_menu.popup(None, None, None, 3, event.time, None)
        elif event.button == 8:
            if self.previous_page():
                self.scroll_image(self.image_vsize, self.image_hsize)

    def button_release_event(self, widget, event):
        """Handles the mouse button release."""
        if event.button in (1, 9):
            if not self.h_dif and not self.v_dif:
                self.next_page()

    def mouse_motion_event(self, widget, event):
        """Handles the motion of the mouse when pressed to move the image."""
        if "GDK_BUTTON1_MASK" in event.state.value_names:
            if event.x_root > self.mouse_posx_old:
                self.h_dif = self.mouse_posx_old - event.x_root
                self.mouse_posx_old = event.x_root
            elif event.x_root < self.mouse_posx_old:
                self.h_dif = self.mouse_posx_old - event.x_root
                self.mouse_posx_old = event.x_root
            if event.y_root > self.mouse_posy_old:
                self.v_dif = self.mouse_posy_old - event.y_root
                self.mouse_posy_old = event.y_root
            elif event.y_root < self.mouse_posy_old:
                self.v_dif = self.mouse_posy_old - event.y_root
                self.mouse_posy_old = event.y_root
            self.scroll_image(self.v_dif, self.h_dif)

    def create_goto_dialog(self):
        """Creates the GoTo dailog."""
        self.goto_dialog = gtk.Dialog('Go to...', self.window, 0,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OK, gtk.RESPONSE_OK))

        self.goto_label = gtk.Label("Go to page...")
        self.goto_label.show()

        self.goto_spinbutton = gtk.SpinButton(None, 1, 0)
        self.goto_spin_adjust = self.goto_spinbutton.get_adjustment()
        self.goto_spinbutton.show()

        self.goto_dialog.vbox.pack_start(self.goto_label, False, False, 0)
        self.goto_dialog.vbox.pack_start(self.goto_spinbutton, False, False, 0)

    def show_goto_dialog(self, widget=None):
        """Show and redirect the GoTo dialog."""
        self.goto_spin_adjust.set_value(self.image_index + 1)
        self.response = self.goto_dialog.run()
        if self.response == gtk.RESPONSE_OK:
            self.goto_dialog_ok()
        else:
            self.goto_dialog_cancel()

    def goto_dialog_ok(self):
        """Handles OK from GoTo dialog."""
        self.goto_dialog.hide()
        self.image_index = int(self.goto_spin_adjust.get_value() - 1)
        self.load_image(self.files_list[int(self.image_index)])

    def goto_dialog_cancel(self):
        """Hide the GoTo dialog."""
        self.goto_dialog.hide()

    def create_open_dialog(self):
        """Creates the open dialog."""
        self.open_dialog = gtk.FileChooserDialog(
        "Open...", self.window,
        gtk.FILE_CHOOSER_ACTION_OPEN,
        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
        gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        # Adding the Preview
        self.preview_box = gtk.VBox(False, 0)
        self.preview_box.set_size_request(150, 150)
        self.preview = gtk.Image()
        self.preview_filename_label = gtk.Label()
        self.preview_file_resolution_label = gtk.Label()
        self.preview_file_size_label = gtk.Label()
        self.preview_box.pack_start(self.preview, False, True, 3)
        self.preview_box.pack_start(self.preview_filename_label, False, True, 3)
        self.preview_box.pack_start(self.preview_file_resolution_label, False, True, 3)
        self.preview_box.pack_start(self.preview_file_size_label, False, True, 1)
        self.preview_box.show_all()
        self.open_dialog.set_use_preview_label(False)
        self.open_dialog.set_preview_widget(self.preview_box)
        self.open_dialog.connect("update-preview", self.open_dialog_update_preview)
        try:
            self.open_dialog.set_current_folder(self.prefs['first path'])
        except:
            self.open_dialog.set_current_folder(os.environ['HOME'])


        # Adding the filter rules
        self.file_filter = gtk.FileFilter()
        self.file_filter.add_pixbuf_formats()
        self.file_filter.add_mime_type("application/zip")
        self.file_filter.add_mime_type("application/x-zip")
        self.file_filter.add_mime_type("application/x-rar")
        self.file_filter.add_mime_type("application/x-tar")
        self.file_filter.add_mime_type("application/x-compressed-tar")
        self.file_filter.add_mime_type("application/x-gzip")
        self.file_filter.add_mime_type("application/x-bzip-compressed-tar")
        self.file_filter.add_mime_type("application/x-bzip2")
        self.file_filter.add_mime_type("application/x-7z-compressed")
        self.file_filter.add_mime_type("application/x-cbr")
        self.file_filter.add_mime_type("application/x-cbt")
        self.file_filter.add_mime_type("application/x-cbz")
        self.file_filter.add_mime_type("application/x-cb7")
        self.file_filter.set_name("Suported Files")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_pattern("*")
        self.file_filter.set_name("All Files")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_pixbuf_formats()
        self.file_filter.set_name("Supported Images Formats")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("application/zip")
        self.file_filter.add_mime_type("application/x-zip")
        self.file_filter.add_mime_type("application/x-rar")
        self.file_filter.add_mime_type("application/x-tar")
        self.file_filter.add_mime_type("application/x-compressed-tar")
        self.file_filter.add_mime_type("application/x-gzip")
        self.file_filter.add_mime_type("application/x-bzip-compressed-tar")
        self.file_filter.add_mime_type("application/x-bzip2")
        self.file_filter.add_mime_type("application/x-7z-compressed")
        self.file_filter.add_mime_type("application/x-cbr")
        self.file_filter.add_mime_type("application/x-cbt")
        self.file_filter.add_mime_type("application/x-cbz")
        self.file_filter.add_mime_type("application/x-cb7")
        self.file_filter.set_name("Compressed Files")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("application/x-cbr")
        self.file_filter.add_mime_type("application/x-cbt")
        self.file_filter.add_mime_type("application/x-cbz")
        self.file_filter.add_mime_type("application/x-cb7")
        self.file_filter.set_name("ComicBook Files")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("application/zip")
        self.file_filter.add_mime_type("application/x-zip")
        self.file_filter.add_mime_type("application/x-cbz")
        self.file_filter.set_name("ZIP Files")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("application/x-rar")
        self.file_filter.add_mime_type("application/x-cbr")
        self.file_filter.set_name("RAR Files")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("application/x-7z-compressed")
        self.file_filter.add_mime_type("application/x-cb7")
        self.file_filter.set_name("7Zip Files")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("application/x-tar")
        self.file_filter.add_mime_type("application/x-compressed-tar")
        self.file_filter.add_mime_type("application/x-gzip")
        self.file_filter.add_mime_type("application/x-bzip-compressed-tar")
        self.file_filter.add_mime_type("application/x-bzip2")
        self.file_filter.add_mime_type("application/x-cbt")
        self.file_filter.set_name("Tar Files")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_pattern("*.jpg")
        self.file_filter.add_pattern("*.jpeg")
        self.file_filter.add_mime_type("image/jpeg")
        self.file_filter.set_name("JPEG Image")
        self.open_dialog.add_filter(self.file_filter)
        
        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("image/png")
        self.file_filter.set_name("PNG Image")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("image/tiff")
        self.file_filter.set_name("TIFF Image")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("image/gif")
        self.file_filter.set_name("GIF Image")
        self.open_dialog.add_filter(self.file_filter)

        self.file_filter = gtk.FileFilter()
        self.file_filter.add_mime_type("image/bmp")
        self.file_filter.set_name("BMP Image")
        self.open_dialog.add_filter(self.file_filter)

    def open_dialog_update_preview(self, data=None):
        """Updates the preview info on the open dialog."""
        self.preview_filename = self.open_dialog.get_preview_filename()
        try:
            self.preview.set_from_pixbuf(
            gtk.gdk.pixbuf_new_from_file_at_size(self.preview_filename, 128, 128))
            self.preview_file_size = os.path.getsize(self.preview_filename)
            self.preview_file_resolution= gtk.gdk.pixbuf_get_file_info(self.preview_filename)[1:]
            self.file_path = os.path.dirname(self.preview_filename)
            self.preview_filename = self.preview_filename.split(os.sep)[-1]
            self.preview_filename_label.set_markup(
            "<b>" + self.preview_filename + "</b>")
            self.preview_file_resolution = str(self.preview_file_resolution[0])+"x"+str(self.preview_file_resolution[1])
            self.preview_file_resolution_label.set_text(self.preview_file_resolution)
            self.preview_file_size_indicator = "KiB"
            self.preview_file_size /= 1000
            if self.preview_file_size >= 1000:
                self.preview_file_size_indicator = "MiB"
                self.preview_file_size /= 1000
            self.preview_file_size = str(format(self.preview_file_size, ".2f"))
            self.preview_file_size_label.set_text(self.preview_file_size+" "+self.preview_file_size_indicator)
            self.preview_filename_label.show()
            self.preview_file_resolution_label.show()
            self.preview_file_size_label.show()
            self.preview.show()
        except:
            self.preview_file_resolution_label.hide()
            self.preview_filename_label.hide()
            self.preview_file_size_label.hide()
            self.preview.hide()


    def show_open_dialog(self, data=None):
        """Handles showing and redirecting the open dialog."""
        self.response = self.open_dialog.run()
        if self.response == gtk.RESPONSE_OK:
            self.open_dialog_ok()
        else:
            self.open_dialog_cancel()

    def open_dialog_ok(self):
        """Handles the OK of the open dialog."""

        self.open_dialog.hide()

        # Close and clear the old open thing
        self.close_book()
        self.file_choosen = self.open_dialog.get_filename()
        self.file_path = os.path.dirname(self.file_choosen)
        if self.pref_sec2_opt4_widget.get_active():
            self.prefs['first path'] = self.file_path
        self.file = None
        self.file_choosen_type = None

        # Check if the file is ZIP
        if zipfile.is_zipfile(self.file_choosen):
            self.file_choosen_type = "zip"
            self.file = zipfile.ZipFile(self.file_choosen, 'r')
            for file in self.file.namelist():
                self.file.extract(file, self._temp_dir)
            self.list_image_files_in_dir(self._temp_dir)

        # Check if the file is TAR (with any compression)
        elif tarfile.is_tarfile(self.file_choosen):
            self.file_choosen_type = "tar"
            self.file = tarfile.open(self.file_choosen, 'r')
            self.file.extractall(self._temp_dir)
            self.list_image_files_in_dir(self._temp_dir)

        # Check if the file is RAR
        elif self.is_rarfile(self.file_choosen):
            if self.rar_version:
                self.file_choosen_type = "rar"
                cmd = self.rar_version + ' x -inul "' + self.file_choosen + '" "' + self._temp_dir + '"'
                subprocess.Popen(cmd, shell=True).wait()
                self.list_image_files_in_dir(self._temp_dir)
            else:
                print('Ignoring RAR file. Rar and UnRar not found!')
                self.close_book()

        # Check if the file is 7zip
        elif self.is_7zfile(self.file_choosen):
            if self.sevenzip_version:
                self.file_choosen_type = "7z"
                cmd = self.sevenzip_version + ' x "' + self.file_choosen + '" -o"' + self._temp_dir + '"'
                subprocess.Popen(cmd, shell=True).wait()
                print("I couldn't find a way to omit this. If you know, tell me.")
                self.list_image_files_in_dir(self._temp_dir)
            else:
                print('Ignoring 7zip file. 7z, 7za, 7zr not found!')
                self.close_book()

        # If not a compacted file, open the image files in folder
        else:
	    if (self.is_image_file(self.file_choosen)):
		self.file_choosen_type = "image"
	    else:
		self.file_choosen_type = "other"
            self.list_image_files_in_dir(self.file_path)

        # Determine the index of the image choosen on the list
        if self.file_choosen_type == "image":
            self.image_index = self.files_list.index(self.file_choosen)
            self.file_parent = os.path.basename(self.file_path)
        elif self.file_choosen_type in ("zip", "tar", "rar", "7z"):
            self.image_index = 0
            self.file_parent = os.path.basename(self.file_choosen)
        else:
            self.image_index = 0
            self.file_parent = os.path.basename(self.file_path)
        self.goto_spin_adjust.configure(self.image_index, 1,
                                        len(self.files_list),
                                        1, 1, 0)
        self.open_dialog.select_filename(self.file_choosen)

        # Try to open to open some file
        try:
            self.load_image(self.files_list[self.image_index])
        except:
            pass

    def open_dialog_cancel(self):
        """Handles the Cancel of the open dialog."""
        self.open_dialog.hide()
        self.file_path = self.prefs['first path']
        try:
            self.open_dialog.select_filename(self.file_choosen)
        except:
            self.open_dialog.set_current_folder(self.file_path)

    def is_rarfile(self, filename):
        """Check if filename is a rar file by checking the magic number."""
        buf = open(filename, "rb").read(len(RAR_ID))
        return buf == RAR_ID

    def is_7zfile(self, filename):
        """Check if filename is a 7zip file by checking the magic number."""
        buf = open(filename, 'rb').read(len(SEVENZIP_ID))
        return buf == SEVENZIP_ID

    def list_image_files_in_dir(self, dir_to_scan):
        """Create the files_list, containing the image files in dir."""
        for file in os.listdir(dir_to_scan):
            if os.path.isfile(os.path.join(dir_to_scan, file)):
                if self.is_image_file(file):
                    self.files_list.append(os.path.join(dir_to_scan, file))
        self.files_list.sort()
	if not self.file_choosen_type in ("other", "image"):
            for path in os.listdir(dir_to_scan):
                if os.path.isdir(os.path.join(dir_to_scan, path)):
                    self.list_image_files_in_dir(os.path.join(dir_to_scan, path))

    def is_image_file(self, filename):
        """Quickly check if the filename is an image file."""
        if (filename[-4:].lower() in ('.jpg', '.jpe', '.jif', '.jfi', '.tif', \
                        '.png', '.gif', '.bmp', '.dib')) or \
            (filename[-5:].lower() in ('.jpeg', '.jfif', '.tiff')):
            return True
        else:
            return False

    def create_preferences_dialog(self):
        self.preferences_dialog = gtk.Dialog("Preferences", self.window, 0, \
                                            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                                            gtk.STOCK_OK, gtk.RESPONSE_APPLY))
        self.preferences_dialog.set_resizable(True)
        self.preferences_dialog.vbox.set_spacing(15)
        self.preferences_dialog.connect('response', self.response_preferences_dialog)
        self.preferences_dialog.connect('delete-event', self.response_preferences_dialog)

        # First Section
        # Start the VBox of the section, where goes the section_label and another VBox
        self.pref_vbox_sec1 = gtk.VBox(False, 3)
        self.pref_section1_label = gtk.Label()
        self.pref_section1_label.set_markup("<b>Main window options: </b>")
        self.pref_section1_label.set_alignment(0, 0)

        # Start the VBox where goes the options
        self.pref_vbox_sec1_items = gtk.VBox(False, 3)

        # Now, set the HBox of which option
        self.pref_sec1_hbox_opt1 = gtk.HBox(False, 3)
        self.pref_sec1_opt1_widget = gtk.CheckButton("Start Maximized.", True)
        self.pref_sec1_hbox_opt1.pack_start(self.pref_sec1_opt1_widget, False, False, 15)

        self.pref_vbox_sec1_items.pack_start(self.pref_sec1_hbox_opt1)
        self.pref_vbox_sec1.pack_start(self.pref_section1_label)
        self.pref_vbox_sec1.pack_start(self.pref_vbox_sec1_items)

        # Second section
        # Start the VBox of the section, where goes the section_label and another VBox
        self.pref_vbox_sec2 = gtk.VBox(False, 3)
        self.pref_section2_label = gtk.Label()
        self.pref_section2_label.set_markup("<b>Open dialog options: </b>")
        self.pref_section2_label.set_alignment(0, 0)

        # Start the VBox where goes the options
        self.pref_vbox_sec2_items = gtk.VBox(False, 3)

        # Now, set the HBox of which option
        self.pref_sec2_hbox_opt1 = gtk.HBox(False, 3)
        self.pref_sec2_opt1_label = gtk.Label("First folder to open in a new session:")
        self.pref_sec2_hbox_opt1.pack_start(self.pref_sec2_opt1_label, False, False, 15)
        self.pref_sec2_hbox_opt2 = gtk.HBox(False, 3)
        self.pref_sec2_opt2_widget = gtk.RadioButton(None, "Home Directory", True)
        self.pref_sec2_opt2_widget.connect('toggled', self.pref_sec2_toggle_event)
        self.pref_sec2_hbox_opt2.pack_start(self.pref_sec2_opt2_widget, False, False, 30)
        self.pref_sec2_hbox_opt3 = gtk.HBox(False, 3)
        self.pref_sec2_opt3_widget1 = gtk.RadioButton(self.pref_sec2_opt2_widget, "Default folder: ", True)
        self.pref_sec2_opt3_widget1.connect('toggled', self.pref_sec2_toggle_event)
        self.pref_sec2_opt3_widget2 = gtk.Button("Choose...", None, True)
        self.pref_sec2_opt3_widget2.connect('clicked', self.first_path_dialog_show)
        self.pref_sec2_hbox_opt3.pack_start(self.pref_sec2_opt3_widget1, False, False, 30)
        self.pref_sec2_hbox_opt3.pack_start(self.pref_sec2_opt3_widget2, False, False, 0)
        self.pref_sec2_hbox_opt4 = gtk.HBox(False, 3)
        self.pref_sec2_opt4_widget = gtk.RadioButton(self.pref_sec2_opt2_widget, 
                                                    "Last path of the last session", True)
        self.pref_sec2_opt4_widget.connect('toggled', self.pref_sec2_toggle_event)
        self.pref_sec2_hbox_opt4.pack_start(self.pref_sec2_opt4_widget, False, False, 30)

        self.pref_vbox_sec2_items.pack_start(self.pref_sec2_hbox_opt1)
        self.pref_vbox_sec2_items.pack_start(self.pref_sec2_hbox_opt2)
        self.pref_vbox_sec2_items.pack_start(self.pref_sec2_hbox_opt3)
        self.pref_vbox_sec2_items.pack_start(self.pref_sec2_hbox_opt4)

        self.pref_vbox_sec2.pack_start(self.pref_section2_label)
        self.pref_vbox_sec2.pack_start(self.pref_vbox_sec2_items)

        # Put all the section on the window
        self.preferences_dialog.vbox.pack_start(self.pref_vbox_sec1)
        self.preferences_dialog.vbox.pack_start(self.pref_vbox_sec2)
        self.preferences_dialog.vbox.show_all()
        self.refresh_preferences_widgets()

    def show_preferences_dialog(self, widget=None):
        self.refresh_preferences_widgets()
        self.preferences_dialog.show_all()

    def response_preferences_dialog(self, widget, response):
        if response == gtk.RESPONSE_APPLY:
            self.preferences_dialog.hide()
            self.save_preferences()
            self.refresh_preferences_widgets()
        else:
            self.refresh_preferences_widgets()
            self.preferences_dialog.hide()
        return True

    def pref_sec2_toggle_event(self, widget):
        if widget == self.pref_sec2_opt3_widget1 and \
            self.pref_sec2_opt3_widget1.get_active():
            self.pref_sec2_opt3_widget2.set_sensitive(True)
        else:
            self.pref_sec2_opt3_widget2.set_sensitive(False)

    def refresh_preferences_widgets(self):
        self.pref_sec1_opt1_widget.set_active(int(self.prefs['start maximized']))
        if int(self.prefs['open option']) == 0:
            self.pref_sec2_opt2_widget.set_active(True)
            self.pref_sec2_opt3_widget2.set_sensitive(False)
        elif int(self.prefs['open option']) == 1:
            self.pref_sec2_opt3_widget1.set_active(True)
            self.pref_sec2_opt3_widget2.set_sensitive(True)
        elif int(self.prefs['open option']) == 2:
            self.pref_sec2_opt4_widget.set_active(True)
            self.pref_sec2_opt3_widget2.set_sensitive(False)

    def create_choose_first_path_dialog(self):
        self.choose_first_path_dialog = gtk.FileChooserDialog("Select folder",
                                            self.preferences_dialog,
                                            gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                            gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.choose_first_path_dialog.set_current_folder(os.environ['HOME'])

    def first_path_dialog_show(self, widget=None):
        try:
            self.choose_first_path_dialog.set_current_folder(self.prefs['first path'])
        except:
            pass
        self.response = self.choose_first_path_dialog.run()
        if self.response == gtk.RESPONSE_OK:
            self.choose_first_path_dialog.hide()
            self.first_path_temp = self.choose_first_path_dialog.get_filename()
        else:
            self.choose_first_path_dialog.hide()

    def create_popup_menu(self):
        """Create the popup menu (Right click of the mouse)"""
        self.popup_menu = gtk.Menu()

        self.popup_prev_menuitem = gtk.ImageMenuItem(gtk.STOCK_GO_BACK, self.accel_group)
        self.popup_next_menuitem = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD, self.accel_group)
        self.popup_prev_menuitem.set_label("_Previous Page")
        self.popup_next_menuitem.set_label("_Next Page")
        self.popup_prev_menuitem.connect('activate', self.previous_page)
        self.popup_next_menuitem.connect('activate', self.next_page)
        self.popup_sep = gtk.SeparatorMenuItem()
        self.popup_fullscreen_menuitem = gtk.CheckMenuItem("_Fullscreen", True)
        self.popup_fullscreen_menuitem.connect('activate', self.toggle_fullscreen)

        self.popup_menu.append(self.popup_prev_menuitem)
        self.popup_menu.append(self.popup_next_menuitem)
        self.popup_menu.append(self.popup_sep)
        self.popup_menu.append(self.popup_fullscreen_menuitem)
        self.popup_menu.show_all()

    def create_about_dialog(self):
        """Creates the About dialog."""
        self.about_dialog = gtk.Dialog('About', self.window, 0, (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.about_dialog.set_resizable(False)
        self.about_dialog.connect('response', self.hide_about_dialog)
        self.about_dialog.connect('delete-event', self.hide_about_dialog)

        self.label_about = gtk.Label()
        self.label_about.set_markup(
        '<big><big><big><b>CiRC</b>\n' +
        '</big></big>CiRC is to Read Comics\n' +
        'version ' + self.version +
        '\n\n</big>CiRC is an image viewer created to handle comic books.' +
        '\nIt opens compressed files as RAR, ZIP, TAR and 7z, and image files too.\n' +
        '\nCiRC is under the GNU General Public License.\n' +
        '\n\n'+
        '<small>Copyright © 2012 Guilherme Pereira Nóya.\n\n' +
        'gui.noya@gmail.com</small>')
        self.label_about.set_justify(gtk.JUSTIFY_CENTER)

        self.about_dialog.vbox.pack_start(self.label_about)
        self.label_about.show()

    def show_about_dialog(self, data=None):
        """Show the About dialog."""
        self.about_dialog.show()

    def hide_about_dialog(self, data=None, data2=None):
        """Hide the About dialog window."""
        self.about_dialog.hide()
        return True

    def close_book(self, event=None):
        """Close the open files, and delete the temporary folder."""
        self.files_list = []
        self.dirs_in_filepath = []
        self.file = None
        self.image.set_from_pixbuf(None)
        self.window.set_title("CiRC")
        self.refresh_active_widgets()
        if os.path.isdir(self._temp_dir):
                for path in os.listdir(self._temp_dir):
                    try:
                        os.remove(os.path.join(self._temp_dir, path))
                    except:
                        shutil.rmtree(os.path.join(self._temp_dir, path))
        gc.collect()

    def close_program(self, event, data=None):
        """Clear temporary files, and close the program."""
        self.close_book()
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)
        self.save_preferences()
        gtk.main_quit()
        sys.exit(0)

    def load_preferences(self):
        if os.path.isdir(self._config_dir):
            if os.path.isfile(os.path.join(self._config_dir, 'preferences')):
                self.prefs_bak = self.prefs
                try:
                    self.pref_file = open(os.path.join(self._config_dir, 'preferences'),
                                            'r')
                    for line in self.pref_file:
                        self.prefs[line.split(':')[0]] = line.split(':')[1][:-1]
                    self.pref_file.close()
                except:
                    self.prefs = self.prefs_bak

    def save_preferences(self):
        if not os.path.isdir(self._config_dir):
            os.makedirs(self._config_dir)
        self.refresh_prefs_to_save()
        self.pref_file = open(os.path.join(self._config_dir, 'preferences'), 'w')
        for option in self.prefs:
            self.pref_file.write(option + ':' + str(self.prefs[option]) + '\n')
        self.pref_file.close()

    def refresh_prefs_to_save(self):
        self.prefs['start maximized'] = int(self.pref_sec1_opt1_widget.get_active())
        self.prefs['window x position'] = self.window.get_position()[0]
        self.prefs['window y position'] = self.window.get_position()[1]
        self.prefs['window x size'] = self.window.get_size()[0]
        self.prefs['window y size'] = self.window.get_size()[1]
        if self.pref_sec2_opt2_widget.get_active():
            self.prefs['open option'] = 0
            self.prefs['first path'] = os.environ['HOME']
        elif self.pref_sec2_opt3_widget1.get_active():
            self.prefs['open option'] = 1
            try:
                self.prefs['first path'] = self.first_path_temp
            except:
                pass
        elif self.pref_sec2_opt4_widget.get_active():
            self.prefs['open option'] = 2
            try:
                self.prefs['first path'] = self.open_dialog.get_current_folder()
            except:
                self.prefs['first path'] = os.environ['HOME']

    def window_state_event(self, widget=None, event=None):
        if event.changed_mask == gtk.gdk.WINDOW_STATE_MAXIMIZED:
            if gtk.gdk.WINDOW_STATE_MAXIMIZED == event.window.get_state():
                self.prefs['window is maximized'] = 1
            elif not gtk.gdk.WINDOW_STATE_MAXIMIZED == event.window.get_state():
                self.prefs['window is maximized'] = 0

    def __init__(self):
        """Check for the external dependencies, and then create and run the program."""

        #--------------------------------
        # Check for dependencies
        #--------------------------------
        # Check rar dependencies
        self.rar_version = None
        self.rar_path = None
        for path in os.environ['PATH'].split(':'):
            if os.path.isfile(os.path.join(path, 'rar')):
                self.rar_version = 'rar'
                self.rar_path = os.path.join(path, 'rar')
                break
            if os.path.isfile(os.path.join(path, 'unrar')):
                self.rar_version = 'unrar'
                self.rar_path = os.path.join(path, 'unrar')
                break
        if not self.rar_version:
            print('Rar and UnRar not found! Please install at least one, to open rar files!')
            print('Rar files (.rar and .cbr) files, will not be open.')

        #Check 7zip dependencies
        self.sevenzip_version = None
        self.sevenzip_path = None
        for path in os.environ['PATH'].split(':'):
            if os.path.isfile(os.path.join(path, '7z')):
                self.sevenzip_version = '7z'
                self.sevenzip_path = os.path.join(path, '7z')
                break
            elif os.path.isfile(os.path.join(path, '7za')):
                self.sevenzip_version = '7za'
                self.sevenzip_path = os.path.join(path, '7za')
                break
            elif os.path.isfile(os.path.join(path, '7zr')):
                self.sevenzip_version = '7zr'
                self.sevenzip_path = os.path.join(path, '7zr')
                break
        if not self.sevenzip_version:
            print('7zip not found! 7z files (.cb7) will be ignored!')
            print('Please install p7zip to open 7zip files.')
            print('Need to have one of these commands: 7z, 7za or 7zr')

        #--------------------------------
        # Create and initiate the program
        #--------------------------------

        self.load_preferences()
        self.create_main_window()
        self.create_about_dialog()
        self.create_open_dialog()
        self.create_preferences_dialog()
        self.create_choose_first_path_dialog()
        self.create_goto_dialog()
        self.create_popup_menu()
        self.refresh_active_widgets()
        self.window.show_all()
        self.layout.grab_focus()
        gc.collect()
        
if __name__ == '__main__':
    circ()
    gtk.main()
