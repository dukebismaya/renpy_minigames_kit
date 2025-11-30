# Copyright (c) 2025 Knox Emberlyn. Licensed under the MIT License.
init python:
    import math
    import renpy.display.render as ren_render
    import renpy.display.pgrender as ren_pgrender
    import renpy.pygame as pygame
    from renpy.color import Color


    def _color_to_rgba_tuple(color_value):
        """Convert Ren'Py colors into an RGBA tuple pygame understands."""
        rgba = Color(color_value).rgba
        return (
            int(rgba[0] * 255),
            int(rgba[1] * 255),
            int(rgba[2] * 255),
            int(rgba[3] * 255),
        )


    class CircleDisplayable(renpy.Displayable):
        """Simple displayable that draws a circle using pygame primitives."""

        def __init__(self, radius, fill_color="#ffffff", border_color=None, border_thickness=0, **kwargs):
            super(CircleDisplayable, self).__init__(**kwargs)
            self.radius = max(1, int(radius))
            self.fill_color = fill_color
            self.border_color = border_color
            self.border_thickness = max(0, int(border_thickness))

        def render(self, width, height, st, at):
            diameter = self.radius * 2
            rv = ren_render.Render(diameter, diameter)

            surface = ren_pgrender.surface((diameter, diameter), True)
            surface = surface.convert_alpha()
            surface.fill((0, 0, 0, 0))

            if self.fill_color:
                pygame.draw.circle(
                    surface,
                    _color_to_rgba_tuple(self.fill_color),
                    (self.radius, self.radius),
                    self.radius,
                )

            if self.border_color and self.border_thickness > 0:
                pygame.draw.circle(
                    surface,
                    _color_to_rgba_tuple(self.border_color),
                    (self.radius, self.radius),
                    self.radius,
                    self.border_thickness,
                )

            rv.blit(surface, (0, 0))
            return rv

        def visit(self):
            return []


    class DashedCircleDisplayable(renpy.Displayable):
        def __init__(self, radius, dash_count=48, dash_ratio=0.5, color="#4dc0ff", thickness=4, rotation=0.0, **kwargs):
            super(DashedCircleDisplayable, self).__init__(**kwargs)
            self.radius = max(1, int(radius))
            self.dash_count = max(1, int(dash_count))
            self.dash_ratio = max(0.05, min(1.0, float(dash_ratio)))
            self.color = color
            self.thickness = max(1, int(thickness))
            self.rotation = float(rotation)

        def render(self, width, height, st, at):
            diameter = self.radius * 2
            size = diameter + self.thickness * 2
            rv = ren_render.Render(size, size)
            surface = ren_pgrender.surface((size, size), True)
            surface = surface.convert_alpha()
            surface.fill((0, 0, 0, 0))

            dash_span = 2 * math.pi / self.dash_count
            dash_length = dash_span * self.dash_ratio
            base = math.radians(self.rotation)
            center = size / 2.0
            radius = self.radius

            for i in range(self.dash_count):
                start = base + dash_span * i
                end = start + dash_length
                start_pos = (
                    center + math.cos(start) * radius,
                    center + math.sin(start) * radius,
                )
                end_pos = (
                    center + math.cos(end) * radius,
                    center + math.sin(end) * radius,
                )
                pygame.draw.line(
                    surface,
                    _color_to_rgba_tuple(self.color),
                    start_pos,
                    end_pos,
                    self.thickness,
                )

            rv.blit(surface, (0, 0))
            return rv

        def visit(self):
            return []


    class ArcDisplayable(renpy.Displayable):
        """Draw an arc using configurable angles, thickness, and segment resolution."""

        def __init__(
            self,
            radius,
            start_angle=-90,
            end_angle=90,
            color="#50e0ff",
            thickness=8,
            segments=120,
            cap_style="round",
            smooth=False,
            smooth_factor=3.0,
            **kwargs
        ):
            super(ArcDisplayable, self).__init__(**kwargs)
            self.radius = max(1, int(radius))
            self.start_angle = float(start_angle)
            self.end_angle = float(end_angle)
            self.color = color
            self.thickness = max(1, int(thickness))
            self.segments = max(4, int(segments))
            self.cap_style = cap_style
            self.smooth = bool(smooth)
            self.smooth_factor = max(1.0, float(smooth_factor))

        def render(self, width, height, st, at):
            diameter = self.radius * 2
            size = diameter + self.thickness * 2
            rv = ren_render.Render(size, size)

            scale = self.smooth_factor if self.smooth else 1.0
            render_size = int(math.ceil(size * scale))
            surface = ren_pgrender.surface((render_size, render_size), True)
            surface = surface.convert_alpha()
            surface.fill((0, 0, 0, 0))

            start_radians = math.radians(self.start_angle)
            end_radians = math.radians(self.end_angle)
            sweep = end_radians - start_radians
            if abs(sweep) < 1e-4:
                return rv

            effective_segments = int(self.segments * (self.smooth_factor if self.smooth else 1.0))
            steps = max(4, int(abs(sweep) / (2 * math.pi) * effective_segments))
            center = render_size / 2.0
            half_thickness = max(1.0, (self.thickness * scale) / 2.0)
            outer_radius = self.radius * scale + half_thickness
            inner_radius = max(0.0, self.radius * scale - half_thickness)

            outer_points = []
            inner_points = []
            mid_points = []
            for i in range(steps + 1):
                t = start_radians + sweep * (i / float(steps))
                cos_t = math.cos(t)
                sin_t = math.sin(t)
                outer_points.append((center + cos_t * outer_radius, center + sin_t * outer_radius))
                inner_points.append((center + cos_t * inner_radius, center + sin_t * inner_radius))
                mid_points.append((center + cos_t * (self.radius * scale), center + sin_t * (self.radius * scale)))

            polygon_points = outer_points + list(reversed(inner_points))
            pygame.draw.polygon(surface, _color_to_rgba_tuple(self.color), polygon_points)

            if self.cap_style == "round" and inner_radius > 0:
                cap_radius = int(round(half_thickness))
                pygame.draw.circle(surface, _color_to_rgba_tuple(self.color), mid_points[0], cap_radius)
                pygame.draw.circle(surface, _color_to_rgba_tuple(self.color), mid_points[-1], cap_radius)

            if scale != 1.0:
                surface = pygame.transform.smoothscale(surface, (size, size))

            rv.blit(surface, (0, 0))
            return rv

        def visit(self):
            return []


screen circle_demo_screen(fill_color="#5ecbff", border_color="#0f1925"):
    modal True
    add Solid("#000000aa")

    frame:
        align (0.5, 0.5)
        padding (28, 28)
        vbox:
            spacing 16
            text "Circle Demo" size 42
            fixed:
                xysize (320, 320)
                add DashedCircleDisplayable(radius=140, dash_count=56, dash_ratio=0.55, thickness=6, color="#2ac4ff", rotation=90) align (0.5, 0.5)
                add CircleDisplayable(radius=130, fill_color=None, border_color=border_color, border_thickness=12) align (0.5, 0.5)
            hbox:
                spacing 24
                xalign 0.5
                add ArcDisplayable(radius=80, start_angle=-120, end_angle=40, thickness=14, color="#5cffc9", segments=160, smooth=True) xalign 0.5
                add ArcDisplayable(radius=80, start_angle=0, end_angle=360, thickness=5, color="#ff7ea8", segments=200, smooth=True) xalign 0.5
            text "Click or press \"Enter\" to dismiss." size 24

    key "dismiss" action Return(None)


label show_circle_demo:
    "Launching the circle demo screen."
    call screen circle_demo_screen
    "Circle demo complete."
    return
