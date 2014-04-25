from __future__ import division
import subprocess
import urllib
#import thread
from time import sleep
from gi.repository import Gtk, GdkPixbuf, Nautilus, GObject, GLib
from threading import Thread

try:
    from gi._glib import GError
except ImportError:
    from gi.repository.GLib import GError  # flake8: noqa
emblems = []
debug = 1
__version__ = 0.6


class Emblems(GObject.GObject, Nautilus.PropertyPageProvider):
    def __init__(self):
        self.icons_has_been_loaded = False
        self.icons_file_path = '/usr/share/gnome3-emblems/icons_whitelist.conf'
        self.icons_whitelist = self.get_icons_list_from_file()
        pass

    def get_property_pages(self, files):
        if len(files) > 1:
            return
        self.file = files
        self.path = urllib.unquote(self.file[0].get_uri()[7:])
#      self.actual_emblems = self.get_actual_emblems()
        property_page = self.create_property_page()
        self.connect_signals()
        return property_page

    def create_property_page(self):
        property_label = Gtk.Label('Emblems')
        property_label.show()
        self.Progress = Gtk.ProgressBar()
        self.list_store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)
        self.icon_view = Gtk.IconView()
        self.icon_view.set_model(self.list_store)
        self.icon_view.set_pixbuf_column(0)
        #self.icon_view.set_text_column(1)
        self.setEmblemButton = Gtk.Button('Set Emblem')
        self.setEmblemButton.set_sensitive(False)
        self.clearEmblemButton = Gtk.Button('Clear Emblem')
        self.setIconButton = Gtk.Button('Set Icon')
        self.setIconButton.set_sensitive(False)
        self.clearIconButton = Gtk.Button('Clear Icon')
        self.refreshButton = Gtk.Button(
            None,
            image=Gtk.Image(
                stock=Gtk.STOCK_REFRESH))
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scroll.add(self.icon_view)
        self.vbox = Gtk.VBox(False,  0)
        buttonbox = Gtk.ButtonBox()
        buttonbox.set_layout(Gtk.ButtonBoxStyle.CENTER)
        for button in (
            self.refreshButton,
            self.clearEmblemButton,
            self.setEmblemButton,
            self.clearIconButton,
            self.setIconButton
        ):
            buttonbox.pack_start(button, False, False, 0)
        self.vbox.pack_start(self.Progress, False, False, 0)
        self.vbox.pack_start(scroll, True, True, 0)
        self.vbox.pack_start(buttonbox, False, True, 0)
        self.vbox.show_all()
        GLib.timeout_add(500, self.fill_emblems)
#        self.fill_emblems()
        self.job_id = GLib.timeout_add(100, self.icon_view_refresh)
#        self.icon_view_refresh()
        return Nautilus.PropertyPage(name="NautilusPython::emblems",
                                     label=property_label,
                                     page=self.vbox),

    def get_icons_list_from_file(self):
        try:
            icons = [line.strip() for line in open(self.icons_file_path)]
        except:
            icons = []
        return icons

    def icon_view_refresh(self):
        self.icon_view.set_model(None)
        self.icon_view.set_model(self.list_store)
        if self.icons_has_been_loaded:
            GLib.source_remove(self.job_id)
            return False
        else:
            return True

    def connect_signals(self):
        self.icon_view.connect('selection-changed', self.on_selection_changed)
        self.icon_view.connect('destroy', self.on_propertywindows_quit)
        self.refreshButton.connect('clicked', self.on_refresh_button_clicked)
        self.setEmblemButton.connect('clicked', self.on_set_emblem_clicked)
        self.clearEmblemButton.connect('clicked', self.on_clear_emblem_clicked)
        self.setIconButton.connect('clicked', self.on_set_icon_clicked)
        self.clearIconButton.connect('clicked', self.on_clear_icon_clicked)

    def on_refresh_button_clicked(self, widget):
        self.list_store.clear()
        self.icons_has_been_loaded = False
        GLib.timeout_add(500,self.fill_emblems)
#        self.fill_emblems()
        self.job_id = GLib.timeout_add(100, self.icon_view_refresh)
#        self.icon_view_refresh()

    def on_set_emblem_clicked(self, widget):
            self.emblem = ''.join(
                [self.icon_view.get_model()[item][2]
                 for item in self.icon_view.get_selected_items()])
            if self.emblem != '':
                self.clearEmblem()
                self.execute(
                    ["gvfs-set-attribute",
                     "-t",
                     "stringv",
                     self.path,
                     "metadata::emblems",
                     self.emblem])
            else:
                return

    def on_set_icon_clicked(self, widget):
            self.icon = ''.join(
                [self.icon_view.get_model()[item][2]
                    for item in self.icon_view.get_selected_items()])
            if self.icon != '':
                icon_theme = Gtk.IconTheme.get_default()
                icon_path = icon_theme.lookup_icon(self.icon, 48, 0)
                print "icon path: %s" % icon_path.get_filename()
                self.clearIcon()
                self.icon_path_comp = "file://" + icon_path.get_filename()
                self.execute(
                    ["gvfs-set-attribute", "-t", "string",
                     self.path, "metadata::custom-icon",
                     self.icon_path_comp])
            else:
                return

    def on_clear_icon_clicked(self, widget):
        self.clearIcon()

    def clearIcon(self):
        self.execute(
            ["gvfs-set-attribute",
             "-t", "unset",
             self.path,
             "metadata::custom-icon-name"])
        self.execute(
            ["gvfs-set-attribute",
             "-t", "unset",
             self.path,
             "metadata::custom-icon"])

    def on_clear_emblem_clicked(self, widget):
        self.clearEmblem()

    def clearEmblem(self):
        self.execute(
            ["gvfs-set-attribute", "-t", "unset",
             self.path, "metadata::emblems"])

    def execute(self, job):
        p = subprocess.Popen(job, stdout=subprocess.PIPE)
        (out, err) = p.communicate()
        return out

    def refresh(self):
        self.execute(
            ["xte", "keydown Control_L",
             "key R", "keyup Control_L"])

    def on_selection_changed(self, widget):
        if debug:
            item = self.icon_view.get_selected_items()[0]
            with open("/tmp/gnome3-emblems.log", 'a') as icon_file:
                icon_file.write('%s\n' % self.list_store[item][1])
                icon_file.close()
        print item
        self.setEmblemButton.set_sensitive(True)
        self.setIconButton.set_sensitive(True)

    def on_propertywindows_quit(self, widget):
        self.refresh()
        GLib.source_remove(self.job_id)

    def get_actual_emblems(self):
#        info = ["gvfs-info", self.path, "-a", "metadata::emblems"]
#        emblem = self.execute(info)
        return []

#    @staticmethod
    def get_icon_name(name):
        """Returns the name human readable.

        >>> Emblems.get_icon_name('emblem-test-name-emblem')
        Test name
        """
        name = name.replace('-emblem', '')
        name = name.replace('emblem-', '')
        name = name.replace('-', ' ')
        name = name.replace('_', ' ')
        return name[0].upper() + name[1:]

    def decompose_icon_name(self, name):
        name = name.replace('-', ' ')
        name = name.replace('_', ' ')
        name = name.split()
        return name

    def fill_emblems(self):
        """Fill the listore with the proper icons."""
        theme = Gtk.IconTheme.get_default()
        #theme.set_custom_theme("Humanity")
        icons=theme.list_icons(None)
        self.icons_whitelist.sort()
        self.Progress.show()
        f=x=0
        y=len(self.icons_whitelist)
        self.Progress.set_fraction(f)
        for icon in self.icons_whitelist:
            x=x+1
            f=x/y
            self.Progress.set_fraction(f)
            while Gtk.events_pending():
                Gtk.main_iteration()
            try:
                pixbuf = theme.load_icon(icon, 48, 0)
                self.list_store.append([pixbuf, icon, icon])
                with open("/tmp/valid_icons", 'a') as valid_icons:
                    valid_icons.write('%s\n' % icon)
                    valid_icons.close()
            except GError:
                pass
        self.icons_has_been_loaded = True
        self.Progress.hide()
        return False
