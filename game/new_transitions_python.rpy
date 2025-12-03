init python:
    from renpy.display.layout import DynamicDisplayable

    class _WideningCreditCallable(object):
        def __init__(self, text, start_kerning, end_kerning, duration, text_kwargs):
            self.text = text
            self.start_kerning = float(start_kerning)
            self.end_kerning = float(end_kerning)
            self.duration = float(duration)
            self.text_kwargs = text_kwargs

        def __call__(self, st, at):
            progress = 1.0 if self.duration <= 0 else min(1.0, st / self.duration)
            kerning = self.start_kerning + (self.end_kerning - self.start_kerning) * progress
            displayable = Text(self.text, kerning=kerning, **self.text_kwargs)
            return displayable, 0.0 if progress < 1.0 else None

    def widening_credit_text(
        text,
        start_kerning=2.0,
        end_kerning=26.0,
        duration=2.4,
        **text_kwargs,
    ):
        params = dict(text_kwargs)
        params.setdefault("layout", "nobreak")
        callable_obj = _WideningCreditCallable(text, start_kerning, end_kerning, duration, params)
        return DynamicDisplayable(callable_obj)


# init python:
#     from renpy.display.transition import Transition, null_render
#     from renpy.display.render import render as _render, Render as _Render
#     from renpy.curry import curry

#     def _ease_out_cubic(t):
#         t = max(0.0, min(1.0, float(t)))
#         return 1.0 - (1.0 - t) ** 3

#     class SplitGateTransition(Transition):
#         """Wing-style split transition that can open or close."""

#         def __init__(
#             self,
#             time=0.75,
#             gap=0.08,
#             gate_mode="open",
#             time_warp=None,
#             old_widget=None,
#             new_widget=None,
#             **properties,
#         ):
#             super(SplitGateTransition, self).__init__(time, **properties)
#             self.time = time
#             self.gap = max(0.0, gap)
#             self.time_warp = time_warp
#             self.old_widget = old_widget
#             self.new_widget = new_widget
#             self.events = False
#             self.opening = (gate_mode or "open").lower() != "close"

#         def render(self, width, height, st, at):
#             if renpy.game.less_updates:
#                 return null_render(self, width, height, st, at)

#             if st >= self.time:
#                 self.events = True
#                 return _render(self.new_widget, width, height, st, at)

#             progress = max(0.0, min(1.0, st / self.time))
#             if self.time_warp is not None:
#                 progress = self.time_warp(progress)

#             new_surface = _render(self.new_widget, width, height, st, at)
#             old_surface = _render(self.old_widget, width, height, st, at)

#             base_surface = new_surface if self.opening else old_surface
#             overlay_surface = old_surface if self.opening else new_surface

#             full_width = max(new_surface.width, old_surface.width, width)
#             full_height = max(new_surface.height, old_surface.height, height)
#             canvas = _Render(full_width, full_height)
#             canvas.blit(base_surface, (0, 0), focus=not self.opening)

#             left_width = max(1, overlay_surface.width // 2)
#             right_width = max(1, overlay_surface.width - left_width)
#             gap_pixels = full_width * self.gap

#             travel = progress if self.opening else 1.0 - progress

#             left_strip = overlay_surface.subsurface((0, 0, left_width, overlay_surface.height), focus=True)
#             left_x = -int(travel * (left_width + gap_pixels))
#             canvas.blit(left_strip, (left_x, 0), focus=True)

#             right_strip = overlay_surface.subsurface((overlay_surface.width - right_width, 0, right_width, overlay_surface.height), focus=True)
#             right_base = overlay_surface.width - right_width
#             right_x = int(right_base + travel * (right_width + gap_pixels))
#             canvas.blit(right_strip, (right_x, 0), focus=True)

#             renpy.display.render.redraw(self, 0)
#             return canvas


#     split_enter = curry(SplitGateTransition)(0.75, gap=0.12, gate_mode="open", time_warp=_ease_out_cubic)
#     split_exit = curry(SplitGateTransition)(0.75, gap=0.12, gate_mode="close", time_warp=_ease_out_cubic)

# init python:
#     config.enter_transition = split_enter
#     config.exit_transition = split_exit