import dearpygui.dearpygui as dpg
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

line_color = (255, 0, 0, 255)
fill_color = (255, 0, 0, 80)

# État interne (pas obligatoire, mais pratique)
selection = {"x1": 2, "x2": 6}

def update_visuals():
    """Met à jour lignes, rectangle et point central"""
    x1 = selection["x1"]
    x2 = selection["x2"]
    cx = (x1 + x2) / 2
    dpg.set_value("range_start", x1)
    dpg.set_value("range_end", x2)
    dpg.set_value("center_point", [cx, 0])
    dpg.configure_item("selection_rect", pmin=[x1, -1.5], pmax=[x2, 1.5])

def on_line_moved(sender, app_data, user_data):
    """Quand une ligne est déplacée"""
    selection["x1"] = dpg.get_value("range_start")
    selection["x2"] = dpg.get_value("range_end")
    update_visuals()

def on_center_moved(sender, app_data, user_data):
    """Quand le point central est déplacé"""
    cx_new = app_data[0]
    x1_old = selection["x1"]
    x2_old = selection["x2"]
    cx_old = (x1_old + x2_old) / 2
    dx = cx_new - cx_old
    selection["x1"] += dx
    selection["x2"] += dx
    update_visuals()


dpg.create_context()
with dpg.window(label="Sélection translatable", width=800, height=600):
    with dpg.plot(label="Courbe", height=500, width=750):
        dpg.add_plot_axis(dpg.mvXAxis, label="X")
        with dpg.plot_axis(dpg.mvYAxis, label="Y"):
            dpg.add_line_series(x, y, label="sin(x)")

        # Rectangle de sélection
        dpg.draw_rectangle(
            pmin=[selection["x1"], -1.5],
            pmax=[selection["x2"], 1.5],
            color=line_color,
            fill=fill_color,
            tag="selection_rect"
        )

        # Lignes verticales
        dpg.add_drag_line(tag="range_start", default_value=selection["x1"],
                          color=line_color, vertical=True, callback=on_line_moved)
        dpg.add_drag_line(tag="range_end", default_value=selection["x2"],
                          color=line_color, vertical=True, callback=on_line_moved)

        # Point central pour translater la sélection
        dpg.add_drag_point(tag="center_point", default_value=[(selection["x1"] + selection["x2"]) / 2, 0],
                           label="Déplacer sélection", callback=on_center_moved,
                           color=(255, 255, 255, 255), thickness=8)


dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()