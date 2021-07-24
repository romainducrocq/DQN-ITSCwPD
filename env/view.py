# """CHANGE IS PYGLET VIEW HERE""" #####################################################################################
PYGLET = False
########################################################################################################################

# """CHANGE PYGLET VIEW HERE""" ########################################################################################

if PYGLET:
    # """CHANGE CUSTOM ENV UTILS IMPORT HERE""" ########################################################################
    from .custom_env import RES
    ####################################################################################################################

    from pyglet.gl import *

    import time


class PygletView(pyglet.window.Window if PYGLET else object):

    @staticmethod
    def points_to_pyglet_vertex(points, color):
        return pyglet.graphics.vertex_list(len(points),
                                           ('v3f/stream', [item for sublist in
                                                           map(lambda p: [p[0], p[1], 0], points)
                                                           for item in sublist]),
                                           ('c3B', PygletView.color_polygon(len(points), color))
                                           )

    @staticmethod
    def color_polygon(n, color):
        colors = []
        for i in range(n):
            colors.extend(color)
        return colors

    @staticmethod
    def draw_polygons(polygons, color):
        [PygletView.points_to_pyglet_vertex(polygon, color).draw(gl.GL_TRIANGLE_FAN) for polygon in polygons]

    @staticmethod
    def draw_vertices(vertices, color):
        [PygletView.points_to_pyglet_vertex(vertex, color).draw(gl.GL_LINES) for vertex in vertices]

    @staticmethod
    def draw_label_top_left(text, x, y, y_offset=0, margin=50, font_size=40, color=(0, 0, 0, 255)):
        pyglet.text.Label(text, x=x + margin, y=y - y_offset * (font_size + margin) - margin, font_size=font_size,
                          color=color).draw()

    @staticmethod
    def load_sprite(path, anchor_x=0.5, anchor_y=0.5):
        img = pyglet.image.load(path)
        img.anchor_x = int(img.width * anchor_x)
        img.anchor_y = int(img.height * anchor_y)
        return pyglet.sprite.Sprite(img, 0, 0)

    def __init__(self, name, env):
        # """CHANGE VIEW INIT HERE""" ##################################################################################
        (width, height) = RES
        background_color = [255, 255, 255]
        ################################################################################################################

        super(PygletView, self).__init__(width, height, name, resizable=True)
        glClearColor(background_color[0] / 255, background_color[1] / 255, background_color[2] / 255, 1)
        self.zoom = 1
        self.key = None

        self.env = env

        self.setup()

        # """CHANGE VIEW SETUP HERE""" #################################################################################
        ################################################################################################################

    def get_play_action(self):
        play_action = 0

        # """CHANGE GET PLAY ACTION HERE""" ############################################################################
        ################################################################################################################

        return play_action

    def on_draw(self, dt=0.002):
        self.clear()

        self.loop()

        # """CHANGE VIEW LOOP HERE""" ##################################################################################
        ################################################################################################################

    def on_resize(self, width, height):
        glMatrixMode(gl.GL_MODELVIEW)
        glLoadIdentity()
        glOrtho(-width, width, -height, height, -1, 1)
        glViewport(0, 0, width, height)
        glOrtho(-self.zoom, self.zoom, -self.zoom, self.zoom, -1, 1)

    def on_key_press(self, symbol, modifiers):
        self.key = symbol

    def on_key_release(self, symbol, modifiers):
        if self.key == symbol:
            self.key = None

    def setup(self):
        raise NotImplementedError

    def loop(self):
        raise NotImplementedError

    def run(self):
        pyglet.clock.schedule_interval(self.on_draw, 0.002)
        pyglet.app.run()


########################################################################################################################

# """CHANGE CUSTOM VIEW HERE""" ########################################################################################

if not PYGLET:
    import time

    # """CHANGE CLOCK SCHEDULE INTERVAL HERE""" ########################################################################
    DT = 0.
    ####################################################################################################################


class CustomView:
    def __init__(self, name, env):
        self.name = name
        self.env = env

        self.setup()

        # """CHANGE VIEW SETUP HERE""" #################################################################################
        ################################################################################################################

    def get_play_action(self):
        play_action = 0

        # """CHANGE GET PLAY ACTION HERE""" ############################################################################
        ################################################################################################################

        return play_action

    def on_draw(self):
        # """CHANGE VIEW LOOP HERE""" ##################################################################################
        pass
        ################################################################################################################

    def clear(self):
        # """CHANGE CLEAR VIEW HERE""" #################################################################################
        pass
        ################################################################################################################

    def setup(self):
        raise NotImplementedError

    def loop(self):
        raise NotImplementedError

    def run(self):
        while True:
            self.clear()
            self.loop()
            self.on_draw()
            time.sleep(DT)

########################################################################################################################
