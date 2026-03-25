import bpy
import os
import time

class VectArtFileWatcher:
    """Monitors SVG files for external changes"""
    _timer = None
    _last_check = 0
    _files_to_watch = {} # {filepath: last_mtime}

    @classmethod
    def start(cls):
        if cls._timer is None:
            cls._timer = bpy.app.timers.register(cls.check_files, first_interval=1.0)
            print("VectArt: Live Sync started")

    @classmethod
    def stop(cls):
        if cls._timer is not None:
            bpy.app.timers.unregister(cls.check_files)
            cls._timer = None
            print("VectArt: Live Sync stopped")

    @classmethod
    def watch_file(cls, filepath):
        if not filepath or not os.path.exists(filepath):
            return
        cls._files_to_watch[filepath] = os.path.getmtime(filepath)

    @classmethod
    def unwatch_file(cls, filepath):
        if filepath in cls._files_to_watch:
            del cls._files_to_watch[filepath]

    @classmethod
    def check_files(cls):
        # Only check every 1 second to save CPU
        current_time = time.time()
        if current_time - cls._last_check < 1.0:
            return 1.0

        for filepath, last_mtime in list(cls._files_to_watch.items()):
            if not os.path.exists(filepath):
                continue
                
            current_mtime = os.path.getmtime(filepath)
            if current_mtime > last_mtime:
                # File changed!
                cls._files_to_watch[filepath] = current_mtime
                cls.on_file_changed(filepath)
        
        cls._last_check = current_time
        return 1.0

    @classmethod
    def on_file_changed(cls, filepath):
        """Trigger reimport logic when file changes"""
        print(f"VectArt: File changed on disk: {filepath}")
        
        try:
            from .operators import _vectart_session
            session_path = _vectart_session.get("svg_edit_path")
            
            if session_path and os.path.normpath(filepath) == os.path.normpath(session_path):
                # We must provide a window context for the operator to run safely from a timer
                window = bpy.context.window_manager.windows[0]
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        with bpy.context.temp_override(window=window, screen=screen, area=area):
                            bpy.ops.object.reimport_edited_svg()
                        break
        except Exception as e:
            print(f"VectArt Sync Error: {str(e)}")
