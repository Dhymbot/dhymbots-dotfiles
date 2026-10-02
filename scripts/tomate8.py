import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")

from gi.repository import Gtk, Gdk, GtkLayerShell, GLib, GdkPixbuf
import cairo
import os
import subprocess
import json
import time
from PIL import Image


class AnimatedTomato:
    def __init__(self, frames, delays, x, y, size):
        self.frames = frames
        self.delays = delays

        self.x = x - size // 2
        self.y = y - size // 2

        self.frame = 0
        self.elapsed = 0

        self.current_pixbuf = frames[0]
        self.finished = False

    def update(self, dt_ms):
        if self.finished:
            return False

        self.elapsed += dt_ms

        # Puede haber GIFs con varios frames que duren 20, 50, 100 ms...
        while self.elapsed >= self.delays[self.frame]:

            self.elapsed -= self.delays[self.frame]
            self.frame += 2

            # Terminó el GIF
            if self.frame >= len(self.frames):
                self.finished = True
                return True

            self.current_pixbuf = self.frames[self.frame]

        return False


class TomatoOverlay(Gtk.Window):

    def __init__(self):
        super().__init__(title="Tomato Overlay")

        # =========================================================
        # CONFIGURACIÓN
        # =========================================================

        self.tomato_size = 500

        # Tiempo entre tomates
        self.spawn_interval = 100

        # =========================================================
        # GIF
        # =========================================================

        self.image_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "tomate.gif"
        )

        if not os.path.exists(self.image_path):
            print("ERROR: no existe:")
            print(self.image_path)
            Gtk.main_quit()
            return

        try:
            self.frames, self.delays = self.load_gif(
                self.image_path,
                self.tomato_size
            )
        except Exception as e:
            print("ERROR cargando tomate.gif:")
            print(e)
            Gtk.main_quit()
            return

        print(f"GIF cargado: {len(self.frames)} frames")

        # =========================================================
        # LAYER SHELL
        # =========================================================

        GtkLayerShell.init_for_window(self)

        GtkLayerShell.set_layer(
            self,
            GtkLayerShell.Layer.OVERLAY
        )

        GtkLayerShell.set_anchor(
            self,
            GtkLayerShell.Edge.TOP,
            True
        )

        GtkLayerShell.set_anchor(
            self,
            GtkLayerShell.Edge.BOTTOM,
            True
        )

        GtkLayerShell.set_anchor(
            self,
            GtkLayerShell.Edge.LEFT,
            True
        )

        GtkLayerShell.set_anchor(
            self,
            GtkLayerShell.Edge.RIGHT,
            True
        )

        GtkLayerShell.set_exclusive_zone(
            self,
            -1
        )

        GtkLayerShell.set_keyboard_mode(
            self,
            GtkLayerShell.KeyboardMode.NONE
        )

        # =========================================================
        # TRANSPARENCIA
        # =========================================================

        self.set_app_paintable(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()

        if visual:
            self.set_visual(visual)

        # =========================================================
        # ESTADO
        # =========================================================

        self.tomatoes = []

        self.mouse_x = 400
        self.mouse_y = 400

        # =========================================================
        # DRAW
        # =========================================================

        self.connect(
            "draw",
            self.on_draw
        )

        # =========================================================
        # ACTUALIZAR RATÓN
        # =========================================================

        GLib.timeout_add(
            100,
            self.update_mouse_position
        )

        # =========================================================
        # ANIMACIÓN
        # =========================================================

        self.last_time = time.monotonic()

        GLib.timeout_add(
            16,
            self.update_animations
        )

        # =========================================================
        # SPAWN
        # =========================================================

        GLib.timeout_add(
            self.spawn_interval,
            self.spawn_tomato
        )

        self.show_all()

    # =============================================================
    # CARGAR GIF CON PILLOW
    # =============================================================

    def load_gif(self, filename, size):

        gif = Image.open(filename)

        frames = []
        delays = []

        frame_count = getattr(
            gif,
            "n_frames",
            1
        )

        print(f"Frames del GIF: {frame_count}")

        for i in range(frame_count):

            gif.seek(i)

            frame = gif.convert("RGBA")

            frame = frame.resize(
                (size, size),
                Image.Resampling.BILINEAR
            )

            # Pillow -> PNG temporal en memoria
            # -> Pixbuf
            import io

            buffer = io.BytesIO()

            frame.save(
                buffer,
                format="PNG"
            )

            buffer.seek(0)

            loader = GdkPixbuf.PixbufLoader.new_with_type(
                "png"
            )

            loader.write(buffer.read())
            loader.close()

            pixbuf = loader.get_pixbuf()

            if pixbuf:
                # Tomamos una referencia independiente
                frames.append(pixbuf.copy())

            # Duración del frame
            delay = gif.info.get(
                "duration",
                100
            )

            if delay is None or delay <= 0:
                delay = 100

            delays.append(delay)

        return frames, delays

    # =============================================================
    # RATÓN
    # =============================================================

    def update_mouse_position(self):

        try:

            result = subprocess.run(
                [
                    "hyprctl",
                    "cursorpos",
                    "-j"
                ],
                capture_output=True,
                text=True,
                timeout=0.05
            )

            data = json.loads(
                result.stdout
            )

            self.mouse_x = int(
                data.get(
                    "x",
                    self.mouse_x
                )
            )

            self.mouse_y = int(
                data.get(
                    "y",
                    self.mouse_y
                )
            )

        except Exception:
            pass

        return True

    # =============================================================
    # CREAR TOMATE
    # =============================================================

    def spawn_tomato(self):

        if not self.frames:
            return True

        fix = 1920
        if self.mouse_x <= 1920:
            fix = 0
        tomato = AnimatedTomato(
            self.frames,
            self.delays,
            self.mouse_x - fix,
            self.mouse_y,
            self.tomato_size
        )

        self.tomatoes.append(
            tomato
        )

        self.queue_draw()

        return True

    # =============================================================
    # ANIMACIONES
    # =============================================================

    def update_animations(self):

        now = time.monotonic()

        dt_ms = (
            now - self.last_time
        ) * 1000

        self.last_time = now

        # Evitar saltos enormes si algo bloquea GTK
        dt_ms = min(
            dt_ms,
            100
        )

        changed = False

        alive = []

        for tomato in self.tomatoes:

            tomato.update(dt_ms)

            if tomato.finished:
                changed = True
            else:
                alive.append(tomato)

        if len(alive) != len(self.tomatoes):
            self.tomatoes = alive

        # Redibujar solamente cuando sea necesario
        if self.tomatoes:
            self.queue_draw()

        return True

    # =============================================================
    # DRAW
    # =============================================================

    def on_draw(self, widget, cr):

        # Limpiar completamente el overlay
        cr.set_operator(cairo.Operator.SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        cr.set_operator(cairo.Operator.OVER)

        for tomato in self.tomatoes:

            if tomato.current_pixbuf:

                Gdk.cairo_set_source_pixbuf(
                    cr,
                    tomato.current_pixbuf,
                    tomato.x,
                    tomato.y
                )

                cr.paint()

        return False


# ================================================================
# START
# ================================================================

win = TomatoOverlay()

Gtk.main()
