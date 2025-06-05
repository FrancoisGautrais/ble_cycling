import dearpygui.dearpygui as dpg

import numpy as np

# Données de base
x = np.linspace(0, 10, 100)
y = np.sin(x)
def on_range_change(sender, app_data, user_data):
    start = dpg.get_value("range_start")
    end = dpg.get_value("range_end")
    print(f"Nouvelle sélection de range : {start:.2f} à {end:.2f}")

def toggle_selection(sender, app_data, user_data):
    visible = not dpg.is_item_shown("range_start")
    dpg.configure_item("range_start", show=visible)
    dpg.configure_item("range_end", show=visible)
    print("Sélection activée" if visible else "Sélection désactivée")

dpg.create_context()

with dpg.window(label="Tutorial"):
    with dpg.plot(label="Courbe", height=500, width=750):
        dpg.add_plot_axis(dpg.mvXAxis, label="X")
        with dpg.plot_axis(dpg.mvYAxis, label="Y"):
            dpg.add_line_series(x, y, label="Courbe sin(x)")
            # Lignes verticales de sélection (range)
        dpg.add_drag_line(label="Start", tag="range_start", default_value=2, color=(255, 0, 0, 255), vertical=True,
                      callback=on_range_change)
        dpg.add_drag_line(label="End", tag="range_end", default_value=6, color=(0, 255, 0, 255), vertical=True,
                          callback=on_range_change)
    dpg.add_button(label="(Dé)sélectionner la zone", callback=toggle_selection)

dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()