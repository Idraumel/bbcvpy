from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
from PIL import ExifTags

# TODO : Simple app which allows to :
#   - open an image file (DONE)
#   - add image metadata like resolution (DONE)
#   - place 4 points on the image (DONE)
#   - display points in a list (DONE)
#   - Remove individual points (DONE)
#   - visually link points via lines (DONE)
#   - update color of vertex and edge of selected point in listbox (DONE)
#   - add a clear selection for zone points
#   - persist active area coordinates for said image - possible to set image file metadata?
#
#   - Replace tuples with arrays or objects (cannot edit tuples)
#   - Cleanup
#   - Migrate to a bigger app using an actual conception pattern (BBCVPY manual client)

# Constants
ROOT_WIDTH = 1420
ROOT_HEIGHT = 800
ZONE_POINT_RADIUS = 4
ZONE_OBJ_COLOR = "green2"
ZONE_OBJ_COLOR_SEL = "red"

# Initialize app
root = Tk()
root.title("BBCVPY - Active area delimiter")
root.columnconfigure(index=0, weight=4)
root.columnconfigure(index=1, weight=1)
root.rowconfigure(index=0, weight=1)
root.geometry([f"{ROOT_WIDTH}x{ROOT_HEIGHT}"])
root.state("zoomed")

canvas = None
zone_points_listbox = None
opened_im_filename = StringVar()
current_im_adjusted_size = ()
current_im_size_var = StringVar()
zone_points = [None, None, None, None]
zone_points_f = []
zone_points_var = StringVar(value=zone_points_f)
placed_points = 0
selected_point_index = None


# open an image file, resize it to the canvas and display
def open_image():
    im_path = filedialog.askopenfilename(
        initialdir="/",
        title="Select an Image file",
        filetypes=(("PNG files", "*.png*"), ("JPEG files", "*.jpeg*")),
    )

    if im_path == "":
        return

    clear_image()

    im = Image.open(im_path)
    global current_im_size
    current_im_size_var.set(str(im.size))

    opened_im_filename.set(os.path.basename(im.filename))
    canvas_size = (canvas.winfo_width(), canvas.winfo_height())
    new_width = None
    new_height = None
    im_aspect_ratio = im.size[0] / im.size[1]
    canvas_aspect_ratio = canvas_size[0] / canvas_size[1]
    # resize image to conserve its aspect ratio but fit the canvas dimensions
    if im_aspect_ratio > canvas_aspect_ratio:
        new_width = canvas_size[0]
        resize_coeff = im.size[0] / new_width
        new_height = im.size[1] / resize_coeff
    elif im_aspect_ratio < canvas_aspect_ratio:
        new_height = canvas_size[1]
        resize_coeff = im.size[1] / new_height
        new_width = im.size[0] / resize_coeff

    global current_im_adjusted_size
    current_im_adjusted_size = (int(new_width), int(new_height))

    im = im.resize(current_im_adjusted_size)
    im_ttk = ImageTk.PhotoImage(im)

    canvas.delete("all")
    canvas.image = im_ttk
    origin_coords = (
        (canvas_size[0] - new_width) // 2,
        (canvas_size[1] - new_height) // 2,
    )
    canvas.create_image(origin_coords[0], origin_coords[1], image=im_ttk, anchor="nw")


def clear_image():
    canvas.delete("all")
    opened_im_filename.set("")
    global current_im_adjusted_size
    current_im_adjusted_size = ()
    global current_im_size_str
    current_im_size_var.set("")
    clear_points()


# show a popup, deactivating the parent and adjacent windows
def popup(title, message):
    popup = Toplevel(root)
    popup.geometry(["250x175+500+350"])
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
def place_zone_point(event):
    global placed_points

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
        event.x < canvas_im_coords_start[0]
        or event.x > canvas_im_coords_end[0]
        or event.y < canvas_im_coords_start[1]
        or event.y > canvas_im_coords_end[1]
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
        print("no free slot - this shouldn't happen")
        return

    # draw edge with previous vertex if existent
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
            event.x,
            event.y,
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
            event.x,
            event.y,
            fill=edge_fill_color,
            width=2,
            tags=("zone_edge", f"zone_edge_{free_index}"),
        )
        # update next point stored line id
        next_point_mut = (zp_next[0], (zp_next[1][0], id_line_next))
        zone_points[zp_next_index] = next_point_mut
        canvas.tag_raise(f"zone_point_{zp_next_index}")

    # draw vertex
    id_oval = canvas.create_oval(
        event.x - ZONE_POINT_RADIUS,
        event.y - ZONE_POINT_RADIUS,
        event.x + ZONE_POINT_RADIUS,
        event.y + ZONE_POINT_RADIUS,
        fill=ZONE_OBJ_COLOR,
        width=0,
        tags=("zone_point", f"zone_point_{free_index}"),
    )

    # register new point
    zp = ((event.x, event.y), (id_oval, id_line))
    zone_points[free_index] = zp
    set_zone_points_var(zone_points)
    placed_points += 1


# remove zone points from image
def clear_points():
    global placed_points
    global zone_points
    for i in range(len(zone_points)):
        zp = zone_points[i]
        if zp is None:
            continue
        canvas.delete(zp[1][0])
        canvas.delete(zp[1][1])
        zone_points[i] = None
    set_zone_points_var(zone_points)
    placed_points = 0


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
        next_zp_mut = (next_zp[0], (next_zp[1][0], None))
        zone_points[next_zp_index] = next_zp_mut
    # clear slot
    zone_points[selected_index] = None
    # refresh listbox
    set_zone_points_var(zone_points)
    placed_points -= 1
    # dereference this index as being activated
    if selected_point_index == selected_index:
        selected_point_index = None


def select_point(event):
    global selected_point_index
    if selected_point_index is not None:
        zp_sel = zone_points[selected_point_index]
        if zp_sel is not None:
            # TODO declare each color as constant for modularity
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
    zp = zone_points[selected_index]
    if zp is None: return
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
frame_right.columnconfigure(index=1, weight=2)
frame_right.columnconfigure(index=2, weight=4)
frame_right.grid(column=1, row=0, columnspan=1, sticky="nsew")

# initialize left frame widgets
canvas = Canvas(frame_left, background="gray75")
canvas.grid(column=0, row=0, sticky="nsew")
root.update()

# activate event binding on mouse button 1 press
canvas.bind("<ButtonPress-1>", place_zone_point)

# initialize right frame widgets
opened_im_filename_entry = ttk.Entry(
    frame_right, textvariable=opened_im_filename, state="readonly"
)
opened_im_filename_entry.grid(column=1, row=0, columnspan=2, sticky="nsew")

im_res_label = ttk.Label(frame_right, text="Resolution")
im_res_label.grid(column=1, row=1)

im_res_entry = ttk.Entry(
    frame_right, textvariable=current_im_size_var, state="readonly"
)
im_res_entry.grid(column=2, row=1, sticky="nsew")

open_img_button = ttk.Button(frame_right, text="Open image", command=open_image)
open_img_button.grid(column=0, row=0, sticky="nsew")

clear_img_button = ttk.Button(frame_right, text="Clear image", command=clear_image)
clear_img_button.grid(column=0, row=1, sticky="nsew")

clear_points_button = ttk.Button(frame_right, text="Clear points", command=clear_points)
clear_points_button.grid(column=0, row=2, sticky="nsew")

zone_points_listbox = Listbox(frame_right, height=4, listvariable=zone_points_var)
zone_points_listbox.grid(column=0, row=3, columnspan=2, sticky="nsew")

zone_points_listbox.bind("<<ListboxSelect>>", select_point)

remove_point_button = ttk.Button(
    frame_right, text="Remove point", command=destroy_point
)
remove_point_button.grid(column=1, row=2, sticky="nsew")
set_zone_points_var(zone_points)

root.mainloop()
