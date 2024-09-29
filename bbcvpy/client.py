from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk
import os
from util.settings_manager import SettingsManager
from business.source_image import SourceImage

# constants
ROOT_WIDTH = 1420
ROOT_HEIGHT = 800
ZONE_POINT_RADIUS = 4
ZONE_POINT_LIMIT = 4
ZONE_OBJ_COLOR = "green2"
ZONE_OBJ_COLOR_SEL = "red"
SETTINGS_FILE_PATH = "./resources/settings.ini"


class Client:
    def __init__(self):
        self.root = None
        self.zone_points_listbox = None
        self.opened_im_filename = None
        self.current_im_adjusted_size = ()
        self.current_im_size_var = None
        self.zone_points = [None, None, None, None]
        self.zone_points_f = []
        self.placed_points = 0
        self.selected_point_index = None
        self.zone_points_var = None
        self.opened_source_im = None

        # widgets
        self.canvas = None
        self.frame_left = None
        self.frame_right = None
        self.frame_right_lf_1 = None
        self.frame_right_lf_2 = None
        self.opened_im_filename_entry = None
        self.im_res_label = None
        self.im_res_entry = None
        self.open_img_button = None
        self.clear_img_button = None
        self.zone_points_listbox = None
        self.clear_points_button = None
        self.remove_point_button = None
        self.clear_selection_button = None
        self.persist_area_button = None

    # initialize app
    def init(self):
        self.root = Tk()
        self.root.title("BBCVPY UI Client")
        self.root.columnconfigure(index=0, weight=4)
        self.root.columnconfigure(index=1, weight=1)
        self.root.rowconfigure(index=0, weight=1)
        self.root.geometry([f"{ROOT_WIDTH}x{ROOT_HEIGHT}"])
        self.root.state("zoomed")

        # initialize vars requiring default root window
        self.opened_im_filename = StringVar()
        self.current_im_size_var = StringVar()
        self.zone_points_var = StringVar(value=self.zone_points_f)

        # retrieve settings
        self.settings_manager = SettingsManager(SETTINGS_FILE_PATH)
        self.default_input_file_path = (
            self.settings_manager.get_value("MAIN", "default_input_file_path") or "/"
        )
        self.opened_image_path = self.settings_manager.get_value(
            "MAIN", "opened_image_path"
        )

        # initialize left frame
        self.frame_left = ttk.Frame(self.root, padding="3 3 12 12")
        self.frame_left.columnconfigure(index=0, weight=1)
        self.frame_left.rowconfigure(index=0, weight=1)
        self.frame_left.grid(column=0, row=0, columnspan=1, sticky="nsew")

        # initialize right frame
        self.frame_right = ttk.Frame(self.root, padding="3 3 12 12")
        self.frame_right.columnconfigure(index=0, weight=1)
        self.frame_right.columnconfigure(index=1, weight=1)
        self.frame_right.grid(column=1, row=0, columnspan=1, sticky="nsew")

        # initialize right frame label frames
        self.frame_right_lf_1 = ttk.LabelFrame(self.frame_right, text="Source image")
        self.frame_right_lf_1.columnconfigure(index=0, weight=1)
        self.frame_right_lf_1.columnconfigure(index=1, weight=2)
        self.frame_right_lf_1.columnconfigure(index=2, weight=4)
        self.frame_right_lf_1.grid(column=0, row=0, columnspan=2, pady=10, sticky="new")

        self.frame_right_lf_2 = ttk.LabelFrame(self.frame_right, text="Active area")
        self.frame_right_lf_2.columnconfigure(index=0, weight=1)
        self.frame_right_lf_2.columnconfigure(index=1, weight=2)
        self.frame_right_lf_2.columnconfigure(index=2, weight=4)
        self.frame_right_lf_2.grid(column=0, row=1, columnspan=2, pady=5, sticky="new")

        # initialize left frame widgets
        self.canvas = Canvas(self.frame_left, background="gray75")
        self.canvas.grid(column=0, row=0, sticky="nsew")
        self.root.update()

        # activate event binding on mouse button 1 press
        self.canvas.bind("<ButtonPress-1>", self.place_zone_point)

        # initialize right frame widgets
        # label frame 1
        self.opened_im_filename_entry = ttk.Entry(
            self.frame_right_lf_1,
            textvariable=self.opened_im_filename,
            state="readonly",
        )
        self.opened_im_filename_entry.grid(column=1, row=0, columnspan=2, sticky="nsew")

        self.im_res_label = ttk.Label(self.frame_right_lf_1, text="Resolution")
        self.im_res_label.grid(column=1, row=1)

        self.im_res_entry = ttk.Entry(
            self.frame_right_lf_1,
            textvariable=self.current_im_size_var,
            state="readonly",
        )
        self.im_res_entry.grid(column=2, row=1, sticky="nsew")

        opened_im_btn_style = ttk.Style()
        opened_im_btn_style.theme_use("clam")
        opened_im_btn_style.configure("opened_im_btn.TButton", background="PaleGreen1")
        self.open_img_button = ttk.Button(
            self.frame_right_lf_1,
            text="Open image",
            command=self.open_image,
            style="opened_im_btn.TButton",
        )
        self.open_img_button.grid(column=0, row=0, sticky="nsew")

        clear_img_btn_style = ttk.Style()
        clear_img_btn_style.theme_use("clam")
        clear_img_btn_style.configure("clear_img_btn_style.TButton", background="pink1")
        self.clear_img_button = ttk.Button(
            self.frame_right_lf_1,
            text="Clear image",
            command=self.clear_image,
            style="clear_img_btn_style.TButton",
        )
        self.clear_img_button.grid(column=0, row=1, sticky="nsew")

        # label frame 2
        self.zone_points_listbox = Listbox(
            self.frame_right_lf_2, height=4, listvariable=self.zone_points_var
        )
        self.zone_points_listbox.grid(
            column=1, row=0, columnspan=2, rowspan=2, sticky="nsew"
        )
        self.zone_points_listbox.bind(
            "<ButtonRelease-1>", lambda event=None: self.toggle_point_selection()
        )

        self.clear_points_button = ttk.Button(
            self.frame_right_lf_2, text="Clear points", command=self.clear_points
        )
        self.clear_points_button.grid(column=0, row=0, sticky="nsew")

        self.remove_point_button = ttk.Button(
            self.frame_right_lf_2, text="Remove point", command=self.destroy_point
        )
        self.remove_point_button.grid(column=0, row=1, sticky="nsew")

        self.clear_selection_button = ttk.Button(
            self.frame_right_lf_2,
            text="Clear selection",
            command=lambda: self.toggle_point_selection(True),
        )
        self.clear_selection_button.grid(column=0, row=2, sticky="nsew")

        persist_area_btn_style = ttk.Style()
        persist_area_btn_style.theme_use("clam")
        persist_area_btn_style.configure(
            "persist_area_btn_style.TButton", background="khaki1"
        )
        self.persist_area_button = ttk.Button(
            self.frame_right_lf_2,
            text="Persist area",
            command=self.save_active_area_metadata,
            style="persist_area_btn_style.TButton",
        )
        self.persist_area_button.grid(column=0, row=3, sticky="nsew")

        # init list box content
        self.set_zone_points_var(self.zone_points)

        self.canvas.bind("<Configure>", self.on_canvas_configure)

    def run(self):
        self.root.mainloop()

    def on_canvas_configure(self, event):
        # display previously opened image
        if self.opened_image_path is not None:
            self.open_image(self.opened_image_path)
        self.canvas.unbind("<Configure>")

    # resize image to canvas while conserving origin ratio
    def resize_image_to_canvas(self, canvas_size):
        new_width, new_height = None, None

        im_aspect_ratio = (
            self.opened_source_im.im.size[0] / self.opened_source_im.im.size[1]
        )
        canvas_aspect_ratio = canvas_size[0] / canvas_size[1]
        # resize image to conserve its aspect ratio but fit the canvas dimensions
        if im_aspect_ratio > canvas_aspect_ratio:
            new_width = canvas_size[0]
            resize_coeff = self.opened_source_im.im.size[0] / new_width
            new_height = self.opened_source_im.im.size[1] / resize_coeff
        elif im_aspect_ratio < canvas_aspect_ratio:
            new_height = canvas_size[1]
            resize_coeff = self.opened_source_im.im.size[1] / new_height
            new_width = self.opened_source_im.im.size[0] / resize_coeff

        return new_width, new_height

    # open an image file, resize it to the canvas and display
    def open_image(self, im_path=None):
        if im_path is None:
            im_path = filedialog.askopenfilename(
                initialdir=self.default_input_file_path,
                title="Select an Image file",
                filetypes=(("PNG files", "*.png*"), ("JPEG files", "*.jpeg*")),
            )

        if im_path == "":
            return

        self.clear_image()

        self.opened_source_im = SourceImage(im_path)

        # save path to settings
        if self.opened_image_path != im_path:
            self.settings_manager.set_value("MAIN", "opened_image_path", im_path)

        self.opened_im_filename.set(os.path.basename(self.opened_source_im.im.filename))
        self.current_im_size_var.set(str(self.opened_source_im.im.size))
        
        # resize image to canvas and draw it
        canvas_size = (self.canvas.winfo_width(), self.canvas.winfo_height())
        new_width, new_height = self.resize_image_to_canvas(canvas_size)
        self.current_im_adjusted_size = (int(new_width), int(new_height))
        self.opened_source_im.im = self.opened_source_im.im.resize(
            self.current_im_adjusted_size
        )
        self.draw_image_onto_canvas(canvas_size, (new_width, new_height))
        
        self.load_im_points_metadata()
        
    # loads zone points metadata from the image and draws the points on the canvas
    def load_im_points_metadata(self):
        saved_active_points = self.opened_source_im.get_metadata_value(
            "active_area_points"
        )
        if saved_active_points is not None:
            for i in range(len(saved_active_points)):
                coords = saved_active_points[i]
                if coords == None:
                    continue
                self.place_zone_point(None, coords[0], coords[1])
                
    def draw_image_onto_canvas(self, canvas_size, im_resized_size):
        im_ttk = ImageTk.PhotoImage(self.opened_source_im.im)
        # cleanup all objects on the canvas
        self.canvas.delete("all")
        # store reference to image to avoid garbage collection
        self.canvas.image = im_ttk
        origin_coords = (
            (canvas_size[0] - im_resized_size[0]) // 2,
            (canvas_size[1] - im_resized_size[1]) // 2,
        )
        self.canvas.create_image(
            origin_coords[0], origin_coords[1], image=im_ttk, anchor="nw"
        )

    def clear_image(self):
        self.canvas.delete("all")
        self.opened_im_filename.set("")
        self.current_im_adjusted_size = ()
        self.current_im_size_var.set("")
        self.clear_points()
        self.opened_image_path = None
        self.settings_manager.set_value(
            "MAIN", "opened_image_path", self.opened_image_path
        )

    # show a popup, deactivating the parent and adjacent windows
    def popup(self, title, message):
        popup = Toplevel(self.root)
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
    def place_zone_point(self, event, x_i=None, y_i=None):
        x, y = None, None
        if event is not None:
            x = event.x
            y = event.y
        else:
            x = x_i
            y = y_i

        if self.opened_im_filename.get() == "":
            self.popup("Invalid action", "Open an image file to place points.")
            return

        # check if the mouse click is inside the boundaries of the image (which may not take the entire canvas)
        canvas_im_coords_start = (
            (self.canvas.winfo_width() - self.current_im_adjusted_size[0]) // 2,
            (self.canvas.winfo_height() - self.current_im_adjusted_size[1]) // 2,
        )
        canvas_im_coords_end = (
            (self.canvas.winfo_width() + self.current_im_adjusted_size[0]) // 2,
            (self.canvas.winfo_height() + self.current_im_adjusted_size[1]) // 2,
        )

        # the cursor is not in the image, ignore the event
        if (
            x < canvas_im_coords_start[0]
            or x > canvas_im_coords_end[0]
            or y < canvas_im_coords_start[1]
            or y > canvas_im_coords_end[1]
        ):
            return

        if self.placed_points == ZONE_POINT_LIMIT:
            self.popup("Invalid action", f"There are already {ZONE_POINT_LIMIT} points.")
            return

        # search for the first available slot
        i = 0
        free_index = None
        while i < len(self.zone_points) and free_index is None:
            zp = self.zone_points[i]
            if zp is None:
                free_index = i
            i += 1
        # this shouldn't happen
        if free_index == None:
            self.popup("Unhandled error", "no free slot - this shouldn't happen")
            return

        # draw edge between current and previous vertex
        id_line = None
        zp_prev_index = None
        if free_index == 0:
            zp_prev_index = ZONE_POINT_LIMIT - 1
        else:
            zp_prev_index = free_index - 1
        zp_prev = self.zone_points[zp_prev_index]
        if zp_prev is not None:
            edge_fill_color = ZONE_OBJ_COLOR
            if self.selected_point_index is not None:
                if zp_prev_index == self.selected_point_index:
                    edge_fill_color = ZONE_OBJ_COLOR_SEL
            id_line = self.canvas.create_line(
                zp_prev[0][0],
                zp_prev[0][1],
                x,
                y,
                fill=edge_fill_color,
                width=2,
                tags=("zone_edge", f"zone_edge_{free_index}"),
            )
            self.canvas.tag_raise(f"zone_point_{zp_prev_index}")

        # draw edge between current and next vertex
        # this can happen in 2 situations : zone point is the ZONE_POINT_LIMITth (last) one, or zone point is created between before existing point
        if free_index == ZONE_POINT_LIMIT - 1 or self.zone_points[free_index + 1] is not None:
            zp_next = None
            zp_next_index = None
            if free_index == ZONE_POINT_LIMIT - 1:
                zp_next = self.zone_points[0]
                zp_next_index = 0
            else:
                zp_next = self.zone_points[free_index + 1]
                zp_next_index = free_index + 1
            edge_fill_color = ZONE_OBJ_COLOR
            if self.selected_point_index is not None:
                if zp_next_index == self.selected_point_index:
                    edge_fill_color = ZONE_OBJ_COLOR_SEL
            id_line_next = self.canvas.create_line(
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
            self.zone_points[zp_next_index] = zp_mut
            self.canvas.tag_raise(f"zone_point_{zp_next_index}")

        # draw vertex
        id_oval = self.canvas.create_oval(
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
        self.zone_points[free_index] = zp
        self.set_zone_points_var(self.zone_points)
        self.placed_points += 1

    # remove all zone points from image
    def clear_points(self):
        for i in range(len(self.zone_points)):
            zp = self.zone_points[i]
            if zp is None:
                continue
            self.canvas.delete(zp[1][0])
            self.canvas.delete(zp[1][1])
            self.zone_points[i] = None
        self.set_zone_points_var(self.zone_points)
        self.placed_points = 0
        self.selected_point_index = None

    # update zone points listbox content
    def set_zone_points_var(self, zone_points):
        self.zone_points_f.clear()
        for i in range(len(self.zone_points)):
            zp = self.zone_points[i]
            zp_str = f"Point {i + 1} : "
            if zp:
                zp_str += f"(x={zp[0][0]}, y={zp[0][1]})"
            else:
                zp_str += "Empty"
            self.zone_points_f.append(zp_str)
        self.zone_points_var.set(self.zone_points_f)

    def get_points_listbox_first_sel(self):
        selected_index_t = self.zone_points_listbox.curselection()
        if selected_index_t == ():
            return
        selected_index = selected_index_t[0]
        return selected_index

    # remove a point from the zone_points list and from the canvas
    # any new point will be added in ascending order and taking the first available space in the list
    def destroy_point(self):
        selected_index = self.get_points_listbox_first_sel()
        zp = self.zone_points[selected_index]
        next_zp_index = selected_index + 1
        if next_zp_index == ZONE_POINT_LIMIT:
            next_zp_index = 0
        # get the next zone point
        next_zp = self.zone_points[next_zp_index]
        self.canvas.delete(zp[1][0])
        # destroy edge between this point and the previous one
        if zp[1][1]:
            self.canvas.delete(zp[1][1])
        # destroy edge between this point and the next one
        if next_zp and next_zp[1][1]:
            self.canvas.delete(next_zp[1][1])
            zp_next_mut = (next_zp[0], (next_zp[1][0], None))
            self.zone_points[next_zp_index] = zp_next_mut
        # clear slot
        self.zone_points[selected_index] = None
        # refresh listbox
        self.set_zone_points_var(self.zone_points)
        self.placed_points -= 1
        # dereference this index as being activated
        if self.selected_point_index == selected_index:
            self.selected_point_index = None

    def toggle_point_selection(self, clear=False):
        if self.selected_point_index is not None:
            zp_sel = self.zone_points[self.selected_point_index]
            if zp_sel is not None:
                self.canvas.itemconfigure(zp_sel[1][0], fill=ZONE_OBJ_COLOR)
                if zp_sel is not None:
                    self.canvas.itemconfigure(zp_sel[1][1], fill=ZONE_OBJ_COLOR)
                zp_sel_next = None
                if self.selected_point_index != ZONE_POINT_LIMIT - 1:
                    zp_sel_next = self.zone_points[self.selected_point_index + 1]
                else:
                    zp_sel_next = self.zone_points[0]
                if zp_sel_next is not None and zp_sel_next[1][1] is not None:
                    self.canvas.itemconfigure(zp_sel_next[1][1], fill=ZONE_OBJ_COLOR)
        selected_index = self.get_points_listbox_first_sel()
        activate = selected_index != self.selected_point_index
        if activate and not clear:
            zp = self.zone_points[selected_index]
            if zp is None:
                return
            self.canvas.itemconfigure(zp[1][0], fill=ZONE_OBJ_COLOR_SEL)
            if zp[1][1] is not None:
                self.canvas.itemconfigure(zp[1][1], fill=ZONE_OBJ_COLOR_SEL)
            zp_next = None
            if selected_index != ZONE_POINT_LIMIT - 1:
                zp_next = self.zone_points[selected_index + 1]
            else:
                zp_next = self.zone_points[0]
            if zp_next is not None:
                self.canvas.itemconfigure(zp_next[1][1], fill=ZONE_OBJ_COLOR_SEL)
            self.selected_point_index = selected_index
        else:
            self.selected_point_index = None

    # persist active area in image metadata
    def save_active_area_metadata(self):
        self.zone_points_f = []
        for zp in self.zone_points:
            value = None
            if zp is not None:
                value = zp[0]
            self.zone_points_f.append(value)
        self.opened_source_im.set_metadata_value(
            "active_area_points", self.zone_points_f
        )
        self.popup(
            "Action success", "The active area delimitation was successfully updated"
        )
