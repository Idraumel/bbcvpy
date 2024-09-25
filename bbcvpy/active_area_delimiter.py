from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import os

# TODO : Simple app which allows to :
#   - open an image file (DONE)
#   - add image metadata like resolution
#   - place 4 points on the image
#   - view list and remove points

ROOT_WIDTH = 1920
ROOT_HEIGHT = 1080

# initialize app
root = Tk()
root.title("BBCVPY - Active area delimiter")
root.columnconfigure(index=0, weight=4)
root.columnconfigure(index=1, weight=1)
root.rowconfigure(index=0, weight=1)
root.geometry([f"{ROOT_WIDTH}x{ROOT_HEIGHT}"])

canvas = None
opened_im_filename = StringVar()
zone_points = []

def open_image():
    im_path = filedialog.askopenfilename(
        initialdir="/",
        title="Select an Image file",
        filetypes=(("PNG files", "*.png*"), ("JPEG files", "*.jpeg*")),
    )

    if im_path == "":
        return

    im = Image.open(im_path)

    opened_im_filename.set(os.path.basename(im.filename))
    canvas_size = (canvas.winfo_width(), canvas.winfo_height())
    new_width = None
    new_height = None
    im_aspect_ratio = im.size[0] / im.size[1]
    canvas_aspect_ratio = canvas_size[0] / canvas_size[1]
    if im_aspect_ratio > canvas_aspect_ratio:
        new_width = canvas_size[0]
        resize_coeff = im.size[0] / new_width
        new_height = im.size[1] / resize_coeff
    elif im_aspect_ratio < canvas_aspect_ratio:
        new_height = canvas_size[1]
        resize_coeff = im.size[1] / new_height
        new_width = im.size[0] / resize_coeff

    im = im.resize((int(new_width), int(new_height)))
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
    zone_points.clear()


def popup(title, message):
    popup = Toplevel(root)
    popup.geometry(
        [
            "250x175+500+350"
        ]
    )
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


def place_zone_point(event):
    if opened_im_filename.get() == "":
        popup("Invalid action", "Open an image file to place points.")
        return
    
    # TODO : check if the mouse click is inside the boundaries of the image (which may not take the entire canvas)

    if len(zone_points) == 4:
        popup("Invalid action", "There are already 4 points.")
        return

    zone_points.append((event.x, event.y))


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
frame_right.columnconfigure(index=1, weight=5)
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
opened_im_filename_entry.grid(column=1, row=0, sticky="nsew")

open_img_button = ttk.Button(frame_right, text="Open image", command=open_image)
open_img_button.grid(column=0, row=0, sticky="nsew")

clear_img_button = ttk.Button(frame_right, text="Clear image", command=clear_image)
clear_img_button.grid(column=0, row=1, sticky="nsew")

root.mainloop()
