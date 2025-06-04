from lxml import etree

# Construction du fichier Glade (GTK3)
glade_xml = etree.Element("interface")

# Fenêtre principale
object_window = etree.SubElement(glade_xml, "object", {"class": "GtkWindow", "id": "main_window"})
etree.SubElement(object_window, "property", name="title").text = "Home Trainer Interface"
etree.SubElement(object_window, "property", name="default_width").text = "800"
etree.SubElement(object_window, "property", name="default_height").text = "600"

# Box verticale principale
main_box = etree.SubElement(object_window, "child")
main_box_object = etree.SubElement(main_box, "object", {"class": "GtkBox", "id": "main_vbox"})
etree.SubElement(main_box_object, "property", name="orientation").text = "vertical"
etree.SubElement(main_box_object, "property", name="spacing").text = "10"
etree.SubElement(main_box_object, "property", name="margin").text = "10"

# 1. Contrôle de session
frame_control = etree.SubElement(main_box_object, "child")
frame_control_obj = etree.SubElement(frame_control, "object", {"class": "GtkFrame", "id": "frame_controls"})
etree.SubElement(frame_control_obj, "property", name="label").text = "Contrôle de la session"
controls_box = etree.SubElement(frame_control_obj, "child")
controls_box_obj = etree.SubElement(controls_box, "object", {"class": "GtkBox", "id": "controls_box"})
etree.SubElement(controls_box_obj, "property", name="orientation").text = "horizontal"
etree.SubElement(controls_box_obj, "property", name="spacing").text = "10"

# Boutons Start/Pause
for label, btn_id in [("Démarrer", "button_start"), ("Pause", "button_pause")]:
    btn = etree.SubElement(etree.SubElement(controls_box_obj, "child"), "object", {"class": "GtkButton", "id": btn_id})
    etree.SubElement(btn, "property", name="label").text = label

# 2. Affichage des données (grande taille)
frame_data = etree.SubElement(main_box_object, "child")
frame_data_obj = etree.SubElement(frame_data, "object", {"class": "GtkFrame", "id": "frame_data"})
etree.SubElement(frame_data_obj, "property", name="label").text = "Données de performance"
data_grid = etree.SubElement(frame_data_obj, "child")
data_grid_obj = etree.SubElement(data_grid, "object", {"class": "GtkGrid", "id": "data_grid"})
etree.SubElement(data_grid_obj, "property", name="column_spacing").text = "20"
etree.SubElement(data_grid_obj, "property", name="row_spacing").text = "10"

# Titres de colonnes
metrics = ["Vitesse", "Cadence", "Puissance"]
types = ["Instantanée", "Moyenne", "Max"]
for i, label in enumerate(["", *metrics]):
    lbl = etree.SubElement(etree.SubElement(data_grid_obj, "child"), "object", {"class": "GtkLabel"})
    etree.SubElement(lbl, "property", name="label").text = label
    etree.SubElement(lbl, "property", name="xalign").text = "0"
    if i > 0:
        etree.SubElement(lbl, "property", name="justify").text = "center"
        etree.SubElement(lbl, "property", name="margin_bottom").text = "5"

# Valeurs
for row, t in enumerate(types, start=1):
    label_title = etree.SubElement(etree.SubElement(data_grid_obj, "child"), "object", {"class": "GtkLabel"})
    etree.SubElement(label_title, "property", name="label").text = t
    etree.SubElement(label_title, "property", name="xalign").text = "0"
    for col, m in enumerate(metrics, start=1):
        label_value = etree.SubElement(etree.SubElement(data_grid_obj, "child"), "object", {"class": "GtkLabel", "id": f"label_{m.lower()}_{t.lower()}"})
        etree.SubElement(label_value, "property", name="label").text = "0"
        etree.SubElement(label_value, "attributes").text = '<attributes><attribute name="scale" value="2"/></attributes>'

# 3. Programme et barre de progression
frame_prog = etree.SubElement(main_box_object, "child")
frame_prog_obj = etree.SubElement(frame_prog, "object", {"class": "GtkFrame", "id": "frame_program"})
etree.SubElement(frame_prog_obj, "property", name="label").text = "Programme en cours"
prog_box = etree.SubElement(frame_prog_obj, "child")
prog_box_obj = etree.SubElement(prog_box, "object", {"class": "GtkBox", "id": "program_box"})
etree.SubElement(prog_box_obj, "property", name="orientation").text = "vertical"
etree.SubElement(prog_box_obj, "property", name="spacing").text = "10"

for text, lbl_id in [("Puissance cible :", "label_power_target"), ("Temps écoulé :", "label_time_elapsed"), ("Temps restant :", "label_time_remaining")]:
    hbox = etree.SubElement(etree.SubElement(prog_box_obj, "child"), "object", {"class": "GtkBox"})
    etree.SubElement(hbox, "property", name="orientation").text = "horizontal"
    lbl_title = etree.SubElement(etree.SubElement(hbox, "child"), "object", {"class": "GtkLabel"})
    etree.SubElement(lbl_title, "property", name="label").text = text
    val = etree.SubElement(etree.SubElement(hbox, "child"), "object", {"class": "GtkLabel", "id": lbl_id})
    etree.SubElement(val, "property", name="label").text = "0"

# Barre de progression
progress = etree.SubElement(etree.SubElement(prog_box_obj, "child"), "object", {"class": "GtkProgressBar", "id": "progress_bar"})
etree.SubElement(progress, "property", name="show_text").text = "True"

# Écriture du fichier
file_path = "home_trainer_interface.glade"
with open(file_path, "wb") as f:
    f.write(etree.tostring(glade_xml, pretty_print=True, xml_declaration=True, encoding="UTF-8"))
