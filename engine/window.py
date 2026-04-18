# engine\window.py
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
    glutCreateWindow(title.encode())

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
