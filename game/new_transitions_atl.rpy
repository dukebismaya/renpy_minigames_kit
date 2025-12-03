# Wing-style gate transitions implemented in ATL to stay on the public API.
transform split_gate_open(duration=0.75, gap=0.12, *, old_widget=None, new_widget=None):
    delay duration
    subpixel True

    contains:
        new_widget
        events True

    contains:
        old_widget
        events False
        crop (0.0, 0.0, 0.5, 1.0)
        xanchor 0.0
        xpos 0.0
        easeout duration xpos (-(0.5 + gap))

    contains:
        old_widget
        events False
        crop (0.5, 0.0, 0.5, 1.0)
        xanchor 1.0
        xpos 1.0
        easeout duration xpos (1.0 + 0.5 + gap)


transform split_gate_close(duration=0.75, gap=0.12, *, old_widget=None, new_widget=None):
    delay duration
    subpixel True

    contains:
        old_widget
        events False

    contains:
        new_widget
        events True
        crop (0.0, 0.0, 0.5, 1.0)
        xanchor 0.0
        xpos (-(0.5 + gap))
        easeout duration xpos 0.0

    contains:
        new_widget
        events True
        crop (0.5, 0.0, 0.5, 1.0)
        xanchor 1.0
        xpos (1.0 + 0.5 + gap)
        easeout duration xpos 1.0