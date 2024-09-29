from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk
import os
from util.settings_manager import SettingsManager
from business.source_image import SourceImage

# TODO : Simple app which allows to :
#   - open an image file (DONE)
#   - add image metadata like resolution (DONE)
#   - place 4 points on the image (DONE)
#   - display points in a list (DONE)
#   - Remove individual points (DONE)
#   - visually link points via lines (DONE)
#   - update color of vertex and edge of selected point in listbox (DONE)
#   - add a clear selection for zone points (DONE)
#   - allow to define a default directory for images (DONE)
#   - persist opened image between sessions (DONE)
#   - persist active area coordinates for said image - possible to set image file metadata? (DONE)
#   - update zone points listbox and canvas when opening image if there is metadata (DONE)
#   - add a convert jpeg to png button (+save to directory)
#   - define max point count as a constant
#   - prohibit intersecting active area edges
#
#   - Replace tuples with arrays or objects (cannot edit tuples)
#   - Cleanup
#   - Migrate to a bigger app using an actual conception pattern (BBCVPY manual client)

# constants
ROOT_WIDTH = 1420
ROOT_HEIGHT = 800
ZONE_POINT_RADIUS = 4
ZONE_OBJ_COLOR = "green2"
ZONE_OBJ_COLOR_SEL = "red"
SETTINGS_FILE_PATH = "./resources/settings.ini"

# initialize app
root = Tk()
root.title("BBCVPY - Active area delimiter")
root.columnconfigure(index=0, weight=4)
root.columnconfigure(index=1, weight=1)
root.rowconfigure(index=0, weight=1)
root.geometry([f"{ROOT_WIDTH}x{ROOT_HEIGHT}"])
root.state("zoomed")

# initialize global vars
canvas = None
zone_points_listbox = None
opened_im_filename = StringVar()
current_im_adjusted_size = ()
current_im_size_var = StringVar()
zone_points = [None, None, None, None]
zone_points_f = []
placed_points = 0
selected_point_index = None
zone_points_var = StringVar(value=zone_points_f)
opened_source_im = None

# retrieve settings
settings_manager = SettingsManager(SETTINGS_FILE_PATH)
default_input_file_path = settings_manager.get_value("MAIN", "default_input_file_path") or "/"
opened_image_path = settings_manager.get_value("MAIN", "opened_image_path")

def on_canvas_configure(event):
    # display previously opened image
    if opened_image_path is not None:
        open_image(opened_image_path)
    canvas.unbind("<Configure>")

# open an image file, resize it to the canvas and display
def open_image(im_path=None):
    global opened_source_im
    global current_im_size
    global placed_points
    global current_im_adjusted_size

    if im_path is None:
        im_path = filedialog.askopenfilename(
            initialdir=default_input_file_path,
            title="Select an Image file",
            filetypes=(("PNG files", "*.png*"), ("JPEG files", "*.jpeg*")),
        )

    if im_path == "":
        return

    clear_image()

    opened_source_im = SourceImage(im_path)
        
    # save path to settings
    if opened_image_path != im_path:
        settings_manager.set_value("MAIN", "opened_image_path", im_path)

    opened_im_filename.set(os.path.basename(opened_source_im.im.filename))
    current_im_size_var.set(str(opened_source_im.im.size))
    canvas_size = (canvas.winfo_width(), canvas.winfo_height())
    new_width = None
    new_height = None
    im_aspect_ratio = opened_source_im.im.size[0] / opened_source_im.im.size[1]
    canvas_aspect_ratio = canvas_size[0] / canvas_size[1]
    # resize image to conserve its aspect ratio but fit the canvas dimensions
    if im_aspect_ratio > canvas_aspect_ratio:
        new_width = canvas_size[0]
        resize_coeff = opened_source_im.im.size[0] / new_width
        new_height = opened_source_im.im.size[1] / resize_coeff
    elif im_aspect_ratio < canvas_aspect_ratio:
        new_height = canvas_size[1]
        resize_coeff = opened_source_im.im.size[1] / new_height
        new_width = opened_source_im.im.size[0] / resize_coeff

    current_im_adjusted_size = (int(new_width), int(new_height))

    opened_source_im.im = opened_source_im.im.resize(current_im_adjusted_size)
    im_ttk = ImageTk.PhotoImage(opened_source_im.im)

    canvas.delete("all")
    canvas.image = im_ttk
    origin_coords = (
        (canvas_size[0] - new_width) // 2,
        (canvas_size[1] - new_height) // 2,
    )
    canvas.create_image(origin_coords[0], origin_coords[1], image=im_ttk, anchor="nw")

    # load image metadata
    saved_active_points = opened_source_im.get_metadata_value("active_area_points")
    if saved_active_points is not None:
        for i in range(len(saved_active_points)):
            coords = saved_active_points[i]
            if coords == None:
                continue
            place_zone_point(None, coords[0], coords[1])


def clear_image():
    global opened_image_path
    global current_im_adjusted_size
    global current_im_size_str
    canvas.delete("all")
    opened_im_filename.set("")
    current_im_adjusted_size = ()
    current_im_size_var.set("")
    clear_points()
    opened_image_path = None
    settings_manager.set_value("MAIN", "opened_image_path", opened_image_path)


# show a popup, deactivating the parent and adjacent windows
def popup(title, message):
    popup = Toplevel(root)
    popup.geometry(["300x200+500+350"])
    popup.title(title)
    popup.columnconfigure(index=0, weight=1)
    popup.rowconfigure(index=0, weight=1)
    popup.rowconfigure(index=1, weight=1)
    popup.grab_set()

    message_label = ttk.Label(popup, text=message)
    message_label.grid(column=0, row=0)

    def close():
        popup.grab_release()
        popup.destroy()

    ack_button = ttk.Button(popup, text="Close", command=close)
    ack_button.grid(column=0, row=1)


# place a zone point on the canvas - links the previous point to the new one with a line
def place_zone_point(event, x_i=None, y_i=None):
    global placed_points
    x, y = None, None
    if event is not None:
        x = event.x
        y = event.y
    else:
        x = x_i
        y = y_i

    if opened_im_filename.get() == "":
        popup("Invalid action", "Open an image file to place points.")
        return

    # check if the mouse click is inside the boundaries of the image (which may not take the entire canvas)
    canvas_im_coords_start = (
        (canvas.winfo_width() - current_im_adjusted_size[0]) // 2,
        (canvas.winfo_height() - current_im_adjusted_size[1]) // 2,
    )
    canvas_im_coords_end = (
        (canvas.winfo_width() + current_im_adjusted_size[0]) // 2,
        (canvas.winfo_height() + current_im_adjusted_size[1]) // 2,
    )

    # the cursor is not in the image, ignore the event
    if (
        x < canvas_im_coords_start[0]
        or x > canvas_im_coords_end[0]
        or y < canvas_im_coords_start[1]
        or y > canvas_im_coords_end[1]
    ):
        return

    if placed_points == 4:
        popup("Invalid action", "There are already 4 points.")
        return

    # search for the first available slot
    i = 0
    free_index = None
    while i < len(zone_points) and free_index is None:
        zp = zone_points[i]
        if zp is None:
            free_index = i
        i += 1
    # this shouldn't happen
    if free_index == None:
        popup("Unhandled error", "no free slot - this shouldn't happen")
        return

    # draw edge between current and previous vertex
    id_line = None
    zp_prev_index = None
    if free_index == 0:
        zp_prev_index = 3
    else:
        zp_prev_index = free_index - 1
    zp_prev = zone_points[zp_prev_index]
    if zp_prev is not None:
        edge_fill_color = ZONE_OBJ_COLOR
        if selected_point_index is not None:
            if zp_prev_index == selected_point_index:
                edge_fill_color = ZONE_OBJ_COLOR_SEL
        id_line = canvas.create_line(
            zp_prev[0][0],
            zp_prev[0][1],
            x,
            y,
            fill=edge_fill_color,
            width=2,
            tags=("zone_edge", f"zone_edge_{free_index}"),
        )
        canvas.tag_raise(f"zone_point_{zp_prev_index}")

    # draw edge between current and next vertex
    # this can happen in 2 situations : zone point is the 4th (last) one, or zone point is created between before existing point
    if free_index == 3 or zone_points[free_index + 1] is not None:
        zp_next = None
        zp_next_index = None
        if free_index == 3:
            zp_next = zone_points[0]
            zp_next_index = 0
        else:
            zp_next = zone_points[free_index + 1]
            zp_next_index = free_index + 1
        edge_fill_color = ZONE_OBJ_COLOR
        if selected_point_index is not None:
            if zp_next_index == selected_point_index:
                edge_fill_color = ZONE_OBJ_COLOR_SEL
        id_line_next = canvas.create_line(
            zp_next[0][0],
            zp_next[0][1],
            x,
            y,
            fill=edge_fill_color,
            width=2,
            tags=("zone_edge", f"zone_edge_{free_index}"),
        )
        # update next point stored line id
        zp_mut = (zp_next[0], (zp_next[1][0], id_line_next))
        zone_points[zp_next_index] = zp_mut
        canvas.tag_raise(f"zone_point_{zp_next_index}")

    # draw vertex
    id_oval = canvas.create_oval(
        x - ZONE_POINT_RADIUS,
        y - ZONE_POINT_RADIUS,
        x + ZONE_POINT_RADIUS,
        y + ZONE_POINT_RADIUS,
        fill=ZONE_OBJ_COLOR,
        width=0,
        tags=("zone_point", f"zone_point_{free_index}"),
    )

    # register new point
    zp = ((x, y), (id_oval, id_line))
    zone_points[free_index] = zp
    set_zone_points_var(zone_points)
    placed_points += 1


# remove all zone points from image
def clear_points():
    global placed_points
    global zone_points
    global selected_point_index
    for i in range(len(zone_points)):
        zp = zone_points[i]
        if zp is None:
            continue
        canvas.delete(zp[1][0])
        canvas.delete(zp[1][1])
        zone_points[i] = None
    set_zone_points_var(zone_points)
    placed_points = 0
    selected_point_index = None


# update zone points listbox content
def set_zone_points_var(zone_points):
    zone_points_f.clear()
    for i in range(len(zone_points)):
        zp = zone_points[i]
        zp_str = f"Point {i + 1} : "
        if zp:
            zp_str += f"(x={zp[0][0]}, y={zp[0][1]})"
        else:
            zp_str += "Empty"
        zone_points_f.append(zp_str)
    zone_points_var.set(zone_points_f)


def get_points_listbox_first_sel():
    selected_index_t = zone_points_listbox.curselection()
    if selected_index_t == ():
        return
    selected_index = selected_index_t[0]
    return selected_index


# remove a point from the zone_points list and from the canvas
# any new point will be added in ascending order and taking the first available space in the list
def destroy_point():
    global placed_points
    global selected_point_index
    selected_index = get_points_listbox_first_sel()
    zp = zone_points[selected_index]
    next_zp_index = selected_index + 1
    if next_zp_index == 4:
        next_zp_index = 0
    # get the next zone point
    next_zp = zone_points[next_zp_index]
    canvas.delete(zp[1][0])
    # destroy edge between this point and the previous one
    if zp[1][1]:
        canvas.delete(zp[1][1])
    # destroy edge between this point and the next one
    if next_zp and next_zp[1][1]:
        canvas.delete(next_zp[1][1])
        zp_next_mut = (next_zp[0], (next_zp[1][0], None))
        zone_points[next_zp_index] = zp_next_mut
    # clear slot
    zone_points[selected_index] = None
    # refresh listbox
    set_zone_points_var(zone_points)
    placed_points -= 1
    # dereference this index as being activated
    if selected_point_index == selected_index:
        selected_point_index = None


def toggle_point_selection(clear=False):
    global selected_point_index
    if selected_point_index is not None:
        zp_sel = zone_points[selected_point_index]
        if zp_sel is not None:
            canvas.itemconfigure(zp_sel[1][0], fill=ZONE_OBJ_COLOR)
            if zp_sel is not None:
                canvas.itemconfigure(zp_sel[1][1], fill=ZONE_OBJ_COLOR)
            zp_sel_next = None
            if selected_point_index != 3:
                zp_sel_next = zone_points[selected_point_index + 1]
            else:
                zp_sel_next = zone_points[0]
            if zp_sel_next is not None and zp_sel_next[1][1] is not None:
                canvas.itemconfigure(zp_sel_next[1][1], fill=ZONE_OBJ_COLOR)
    selected_index = get_points_listbox_first_sel()
    activate = selected_index != selected_point_index
    if activate and not clear:
        zp = zone_points[selected_index]
        if zp is None:
            return
        canvas.itemconfigure(zp[1][0], fill=ZONE_OBJ_COLOR_SEL)
        if zp[1][1] is not None:
            canvas.itemconfigure(zp[1][1], fill=ZONE_OBJ_COLOR_SEL)
        zp_next = None
        if selected_index != 3:
            zp_next = zone_points[selected_index + 1]
        else:
            zp_next = zone_points[0]
        if zp_next is not None:
            canvas.itemconfigure(zp_next[1][1], fill=ZONE_OBJ_COLOR_SEL)
        selected_point_index = selected_index
    else:
        selected_point_index = None


# persist active area in image metadata
def persist_area():
    zone_points_f = []
    for zp in zone_points:
        value = None
        if zp is not None:
            value = zp[0]
        zone_points_f.append(value)
    opened_source_im.set_metadata_value("active_area_points", zone_points_f)
    popup("Action success", "The active area delimitation was successfully updated")

# initialize left frame
# style_frame_left = ttk.Style()
# style_frame_left.theme_use("clam")
# style_frame_left.configure("frame_left.TFrame", background="sky blue")
frame_left = ttk.Frame(root, padding="3 3 12 12")
frame_left.columnconfigure(index=0, weight=1)
frame_left.rowconfigure(index=0, weight=1)
frame_left.grid(column=0, row=0, columnspan=1, sticky="nsew")

# initialize right frame
frame_right = ttk.Frame(root, padding="3 3 12 12")
frame_right.columnconfigure(index=0, weight=1)
frame_right.columnconfigure(index=1, weight=1)
frame_right.grid(column=1, row=0, columnspan=1, sticky="nsew")

# initialize right frame label frames
frame_right_lf_1 = ttk.LabelFrame(frame_right, text="Source image")
frame_right_lf_1.columnconfigure(index=0, weight=1)
frame_right_lf_1.columnconfigure(index=1, weight=2)
frame_right_lf_1.columnconfigure(index=2, weight=4)
frame_right_lf_1.grid(column=0, row=0, columnspan=2, pady=10, sticky="new")

frame_right_lf_2 = ttk.LabelFrame(frame_right, text="Active area")
frame_right_lf_2.columnconfigure(index=0, weight=1)
frame_right_lf_2.columnconfigure(index=1, weight=2)
frame_right_lf_2.columnconfigure(index=2, weight=4)
frame_right_lf_2.grid(column=0, row=1, columnspan=2, pady=5, sticky="new")

# initialize left frame widgets
canvas = Canvas(frame_left, background="gray75")
canvas.grid(column=0, row=0, sticky="nsew")
root.update()

# activate event binding on mouse button 1 press
canvas.bind("<ButtonPress-1>", place_zone_point)

# initialize right frame widgets
# label frame 1
opened_im_filename_entry = ttk.Entry(
    frame_right_lf_1,
    textvariable=opened_im_filename,
    state="readonly",
)
opened_im_filename_entry.grid(column=1, row=0, columnspan=2, sticky="nsew")

im_res_label = ttk.Label(frame_right_lf_1, text="Resolution")
im_res_label.grid(column=1, row=1)

im_res_entry = ttk.Entry(
    frame_right_lf_1, textvariable=current_im_size_var, state="readonly"
)
im_res_entry.grid(column=2, row=1, sticky="nsew")

opened_im_btn_style = ttk.Style()
opened_im_btn_style.theme_use("clam")
opened_im_btn_style.configure("opened_im_btn.TButton", background="PaleGreen1")
open_img_button = ttk.Button(
    frame_right_lf_1,
    text="Open image",
    command=open_image,
    style="opened_im_btn.TButton",
)
open_img_button.grid(column=0, row=0, sticky="nsew")

clear_img_btn_style = ttk.Style()
clear_img_btn_style.theme_use("clam")
clear_img_btn_style.configure("clear_img_btn_style.TButton", background="pink1")
clear_img_button = ttk.Button(
    frame_right_lf_1,
    text="Clear image",
    command=clear_image,
    style="clear_img_btn_style.TButton",
)
clear_img_button.grid(column=0, row=1, sticky="nsew")

# label frame 2
zone_points_listbox = Listbox(frame_right_lf_2, height=4, listvariable=zone_points_var)
zone_points_listbox.grid(column=1, row=0, columnspan=2, rowspan=2, sticky="nsew")
zone_points_listbox.bind(
    "<ButtonRelease-1>", lambda event=None: toggle_point_selection()
)

clear_points_button = ttk.Button(
    frame_right_lf_2, text="Clear points", command=clear_points
)
clear_points_button.grid(column=0, row=0, sticky="nsew")

remove_point_button = ttk.Button(
    frame_right_lf_2, text="Remove point", command=destroy_point
)
remove_point_button.grid(column=0, row=1, sticky="nsew")

clear_selection_button = ttk.Button(
    frame_right_lf_2,
    text="Clear selection",
    command=lambda: toggle_point_selection(True),
)
clear_selection_button.grid(column=0, row=2, sticky="nsew")

persist_area_btn_style = ttk.Style()
persist_area_btn_style.theme_use("clam")
persist_area_btn_style.configure("persist_area_btn_style.TButton", background="khaki1")
persist_area_button = ttk.Button(
    frame_right_lf_2,
    text="Persist area",
    command=persist_area,
    style="persist_area_btn_style.TButton",
)
persist_area_button.grid(column=0, row=3, sticky="nsew")

# init list box content
set_zone_points_var(zone_points)

canvas.bind("<Configure>", on_canvas_configure)

root.mainloop()
