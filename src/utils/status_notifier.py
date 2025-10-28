"""
StatusNotifierItem implementation for GTK4 system tray support.
Uses D-Bus to implement the freedesktop.org StatusNotifierItem specification.
"""

import os
from gi.repository import Gio, GLib
from core.config import get_app_paths


class StatusNotifierItem:
    """
    Implements StatusNotifierItem (SNI) protocol via D-Bus.
    This provides system tray functionality for GTK4 applications.
    """
    
    BUS_NAME = "org.kde.StatusNotifierItem"
    OBJECT_PATH = "/StatusNotifierItem"
    
    # D-Bus introspection XML
    INTROSPECTION_XML = """
    <!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
    "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
    <node>
        <interface name="org.kde.StatusNotifierItem">
            <property name="Category" type="s" access="read"/>
            <property name="Id" type="s" access="read"/>
            <property name="Title" type="s" access="read"/>
            <property name="Status" type="s" access="read"/>
            <property name="WindowId" type="i" access="read"/>
            <property name="IconName" type="s" access="read"/>
            <property name="IconThemePath" type="s" access="read"/>
            <property name="Menu" type="o" access="read"/>
            <property name="ItemIsMenu" type="b" access="read"/>
            <method name="Activate">
                <arg name="x" type="i" direction="in"/>
                <arg name="y" type="i" direction="in"/>
            </method>
            <method name="SecondaryActivate">
                <arg name="x" type="i" direction="in"/>
                <arg name="y" type="i" direction="in"/>
            </method>
            <method name="ContextMenu">
                <arg name="x" type="i" direction="in"/>
                <arg name="y" type="i" direction="in"/>
            </method>
        </interface>
    </node>
    """
    
    def __init__(self, app, main_window):
        """
        Initialize the StatusNotifierItem.
        
        Args:
            app: The Adw.Application instance
            main_window: The MainWindow instance
        """
        self.app = app
        self.main_window = main_window
        self.paths = get_app_paths()
        self.bus = None
        self.registration_id = None
        self.bus_name_id = None
        
        # Properties
        self._category = "ApplicationStatus"
        self._id = "ubuntu-sticky-notes"
        self._title = "Ubuntu Sticky Notes"
        self._status = "Active"
        self._icon_name = "note"
        
        # Try to set custom icon if available
        if os.path.exists(self.paths["APP_ICON_PATH"]):
            self._icon_name = self.paths["APP_ICON_PATH"]
        
        self._setup_dbus()
    
    def _setup_dbus(self):
        """Set up D-Bus connection and register the StatusNotifierItem."""
        try:
            # Get session bus
            self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            
            # Parse introspection XML
            introspection_data = Gio.DBusNodeInfo.new_for_xml(self.INTROSPECTION_XML)
            
            # Register object on the bus
            self.registration_id = self.bus.register_object(
                self.OBJECT_PATH,
                introspection_data.interfaces[0],
                self._handle_method_call,
                self._handle_get_property,
                None  # No settable properties
            )
            
            # Own a unique bus name
            unique_name = f"{self.BUS_NAME}-{os.getpid()}"
            self.bus_name_id = Gio.bus_own_name(
                Gio.BusType.SESSION,
                unique_name,
                Gio.BusNameOwnerFlags.NONE,
                self._on_bus_acquired,
                self._on_name_acquired,
                self._on_name_lost
            )
            
            # Register with StatusNotifierWatcher
            self._register_with_watcher(unique_name)
            
            print(f"✓ System tray icon registered as: {unique_name}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup D-Bus system tray: {e}")
            return False
    
    def _register_with_watcher(self, service_name):
        """Register this item with the StatusNotifierWatcher."""
        try:
            proxy = Gio.DBusProxy.new_sync(
                self.bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.kde.StatusNotifierWatcher",
                "/StatusNotifierWatcher",
                "org.kde.StatusNotifierWatcher",
                None
            )
            
            proxy.call_sync(
                "RegisterStatusNotifierItem",
                GLib.Variant("(s)", (service_name,)),
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )
            
        except Exception as e:
            print(f"Note: StatusNotifierWatcher not available ({e})")
            print("System tray may not appear on this desktop environment.")
    
    def _on_bus_acquired(self, connection, name):
        """Called when the bus is acquired."""
        pass
    
    def _on_name_acquired(self, connection, name):
        """Called when the bus name is acquired."""
        pass
    
    def _on_name_lost(self, connection, name):
        """Called when the bus name is lost."""
        print(f"Warning: Lost D-Bus name: {name}")
    
    def _handle_method_call(self, connection, sender, object_path, interface_name,
                           method_name, parameters, invocation):
        """Handle D-Bus method calls."""
        if method_name == "Activate":
            # Left click - toggle main window
            GLib.idle_add(self._toggle_main_window)
            invocation.return_value(None)
            
        elif method_name == "SecondaryActivate":
            # Right click - show context menu (handled by shell)
            invocation.return_value(None)
            
        elif method_name == "ContextMenu":
            # Context menu request
            invocation.return_value(None)
        
        else:
            invocation.return_error_literal(
                Gio.dbus_error_quark(),
                Gio.DBusError.UNKNOWN_METHOD,
                f"Method {method_name} not implemented"
            )
    
    def _handle_get_property(self, connection, sender, object_path,
                            interface_name, property_name):
        """Handle D-Bus property requests."""
        if property_name == "Category":
            return GLib.Variant("s", self._category)
        elif property_name == "Id":
            return GLib.Variant("s", self._id)
        elif property_name == "Title":
            return GLib.Variant("s", self._title)
        elif property_name == "Status":
            return GLib.Variant("s", self._status)
        elif property_name == "WindowId":
            return GLib.Variant("i", 0)
        elif property_name == "IconName":
            return GLib.Variant("s", self._icon_name)
        elif property_name == "IconThemePath":
            return GLib.Variant("s", "")
        elif property_name == "Menu":
            return GLib.Variant("o", "/")
        elif property_name == "ItemIsMenu":
            return GLib.Variant("b", False)
        
        return None
    
    def _toggle_main_window(self):
        """Toggle main window visibility."""
        if self.main_window.is_visible():
            self.main_window.hide()
        else:
            self.main_window.present()
        return False
    
    def cleanup(self):
        """Clean up D-Bus resources."""
        if self.registration_id:
            self.bus.unregister_object(self.registration_id)
        if self.bus_name_id:
            Gio.bus_unown_name(self.bus_name_id)


def init_status_notifier(app, main_window):
    """
    Initialize the StatusNotifierItem for system tray support.
    
    Args:
        app: The Adw.Application instance
        main_window: The MainWindow instance
        
    Returns:
        StatusNotifierItem instance or None if setup failed
    """
    try:
        return StatusNotifierItem(app, main_window)
    except Exception as e:
        print(f"Could not initialize system tray: {e}")
        return None
