from PySide6.QtGui import QPalette, QColor


def set_spring_palette(app):
    palette = QPalette()

    # Backgrounds
    palette.setColor(QPalette.Window, QColor("#CDFADB"))         # main background (light yellow)
    palette.setColor(QPalette.Base, QColor("#F6FDC3"))           # input fields (mint green)
    palette.setColor(QPalette.AlternateBase, QColor("#FFCF96"))  # alternate base (peach)

    # Texts
    palette.setColor(QPalette.WindowText, QColor("#3C3C3C"))     # dark gray text for contrast
    palette.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ToolTipText, QColor("#3C3C3C"))
    palette.setColor(QPalette.Text, QColor("#3C3C3C"))
    palette.setColor(QPalette.ButtonText, QColor("#3C3C3C"))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))

    # Buttons
    palette.setColor(QPalette.Button, QColor("#FFCF96"))         # warm peach for buttons
    palette.setColor(QPalette.BrightText, QColor("#FF0000"))     # red for alerts

    # Links and Highlights
    palette.setColor(QPalette.Link, QColor("#FF8080"))           # bold pink for links
    palette.setColor(QPalette.Highlight, QColor("#FF8080"))      # highlight selection

    app.setPalette(palette)


def set_summer_palette(app):
    palette = QPalette()

    # Backgrounds
    palette.setColor(QPalette.Window, QColor("#fffbe6"))            # sunlit cream
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#fff3b0"))

    # Texts
    palette.setColor(QPalette.WindowText, QColor("#3a2f0b"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#3a2f0b"))
    palette.setColor(QPalette.Text, QColor("#3a2f0b"))
    palette.setColor(QPalette.ButtonText, QColor("#3a2f0b"))
    palette.setColor(QPalette.HighlightedText, QColor("#000000"))

    # Buttons
    palette.setColor(QPalette.Button, QColor("#ffd972"))            # pineapple
    palette.setColor(QPalette.BrightText, QColor("#ff0000"))

    # Links and Highlights
    palette.setColor(QPalette.Link, QColor("#2a9d8f"))              # tropical water
    palette.setColor(QPalette.Highlight, QColor("#f7c948"))         # citrus

    app.setPalette(palette)


def set_autumn_palette(app):
    palette = QPalette()

    # BaseBusiness background and text
    palette.setColor(QPalette.Window, QColor("#FFA955"))  # warm orange background
    palette.setColor(QPalette.Base, QColor("#FFD63A"))  # input fields
    palette.setColor(QPalette.AlternateBase, QColor("#6DE1D2"))  # alt rows

    # Text
    palette.setColor(QPalette.Text, QColor("black"))
    palette.setColor(QPalette.WindowText, QColor("black"))
    palette.setColor(QPalette.Button, QColor("#F75A5A"))  # red for buttons
    palette.setColor(QPalette.ButtonText, QColor("white"))
    palette.setColor(QPalette.BrightText, QColor("white"))
    palette.setColor(QPalette.ToolTipBase, QColor("white"))
    palette.setColor(QPalette.ToolTipText, QColor("black"))

    # Highlight
    palette.setColor(QPalette.Highlight, QColor("#6DE1D2"))
    palette.setColor(QPalette.HighlightedText, QColor("black"))

    app.setPalette(palette)


def set_winter_palette(app):
    palette = QPalette()

    # Backgrounds
    palette.setColor(QPalette.Window, QColor("#eef1f5"))            # frosty white
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#dce4ed"))

    # Texts
    palette.setColor(QPalette.WindowText, QColor("#1c2b3a"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#1c2b3a"))
    palette.setColor(QPalette.Text, QColor("#1c2b3a"))
    palette.setColor(QPalette.ButtonText, QColor("#1c2b3a"))
    palette.setColor(QPalette.HighlightedText, QColor("#000000"))

    # Buttons
    palette.setColor(QPalette.Button, QColor("#cbd8e0"))            # snow blue
    palette.setColor(QPalette.BrightText, QColor("#ff0000"))

    # Links and Highlights
    palette.setColor(QPalette.Link, QColor("#2a6f97"))              # icy link
    palette.setColor(QPalette.Highlight, QColor("#a3c3d9"))

    app.setPalette(palette)


def set_dark_palette(app):
    palette = QPalette()

    # Backgrounds
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.Base, QColor(42, 42, 42))
    palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))

    # Texts
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

    # Buttons
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

    # Links and Highlights
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))

    app.setPalette(palette)