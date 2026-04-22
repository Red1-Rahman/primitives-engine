# engine\window.py
import os
import platform as py_platform

from OpenGL import platform as ogl_platform
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from .input import register_input

WIN_W, WIN_H = 800, 600
WORLD_LEFT, WORLD_RIGHT   = -400, 400
WORLD_BOTTOM, WORLD_TOP   = -300, 300

FPS     = 60
FRAME_MS = int(1000 / FPS)

_update_fn  = None
_display_fn = None


def _display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    if _display_fn:
        _display_fn()
    glutSwapBuffers()


def _timer(value):
    if _update_fn:
        _update_fn()
    glutPostRedisplay()
    glutTimerFunc(FRAME_MS, _timer, 0)


def _reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(WORLD_LEFT, WORLD_RIGHT, WORLD_BOTTOM, WORLD_TOP, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def init_window(title, display_fn, update_fn=None):
    """
    Create and open a GLUT window.
    display_fn : called every frame to draw the scene
    update_fn  : called every frame to update game/scene state
    """
    global _display_fn, _update_fn
    _display_fn = display_fn
    _update_fn  = update_fn

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(100, 100)
    window_id = glutCreateWindow(title.encode())
    if window_id <= 0:
        raise RuntimeError(
            "Failed to create GLUT window. "
            f"DISPLAY={os.environ.get('DISPLAY')!r}, "
            f"XDG_SESSION_TYPE={os.environ.get('XDG_SESSION_TYPE')!r}."
        )

    # Linux Wayland+EGL mismatch can create a window without a usable GL context.
    if py_platform.system() == "Linux" and ogl_platform.GetCurrentContext() is None:
        backend = os.environ.get("PYOPENGL_PLATFORM", "<auto>")
        raise RuntimeError(
            "OpenGL context is not current after window creation. "
            f"PYOPENGL_PLATFORM={backend!r}, "
            f"DISPLAY={os.environ.get('DISPLAY')!r}, "
            f"WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY')!r}. "
            "On Linux, run with a GLX backend (for example: "
            "PYOPENGL_PLATFORM=glx /usr/bin/python3.10 main.py)."
        )

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_POINT_SMOOTH)
    glEnable(GL_LINE_SMOOTH)

    glutDisplayFunc(_display)
    glutReshapeFunc(_reshape)
    glutTimerFunc(FRAME_MS, _timer, 0)
    register_input()


def start_loop():
    """Start the GLUT main loop."""
    glutMainLoop()
