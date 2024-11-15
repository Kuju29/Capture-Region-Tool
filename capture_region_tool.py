import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk, ImageGrab
import json

class ReadOnlyText(tk.Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bind('<Key>', lambda e: 'break')
        self.bind('<Button-1>', lambda e: self.focus_set())

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Copy All", command=self.copy_all_text)

        self.bind("<Button-3>", self.show_context_menu)

    def copy_all_text(self):
        try:
            text = self.get('1.0', tk.END)
            self.clipboard_clear()
            self.clipboard_append(text)
        except tk.TclError:
            pass

    def show_context_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

class ScreenCaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Capture Region Tool")

        self.root.geometry("800x600")

        self.capture_button = ttk.Button(
            root, text="Select Screen Region", command=self.capture_region)
        self.capture_button.pack(pady=10)

        self.region_info = ReadOnlyText(root, width=50, height=1, wrap='none')
        self.region_info.pack(pady=10, fill=tk.X, expand=False)

        self.region_info.bind('<Configure>', self._on_text_change)

        self.image_canvas = tk.Canvas(root, borderwidth=1, relief='solid')
        self.image_canvas.pack(pady=10, fill=tk.BOTH, expand=True)

        self.save_button = ttk.Button(
            root, text="Save Image", command=self.save_image)
        self.save_button.pack(pady=10)

        self.screenshot = None
        self.coordinates = {}
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.image_id = None

    def _on_text_change(self, event):
        num_lines = int(self.region_info.index('end-1c').split('.')[0])
        self.region_info.config(height=num_lines)

    def capture_region(self):
        self.root.withdraw()

        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        x1, y1, x2, y2 = self.get_mouse_selection()

        self.root.deiconify()

        if x1 is None or y1 is None or x2 is None or y2 is None:
            return

        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        if width == 0 or height == 0:
            messagebox.showwarning("Warning", "No region selected.")
            return

        self.coordinates = {
            "top": int(top),
            "left": int(left),
            "width": int(width),
            "height": int(height)
        }

        self.region_info.config(state='normal')
        self.region_info.delete('1.0', tk.END)
        screen_size = f"({self.screen_width}, {self.screen_height}) "
        coords_json = json.dumps(self.coordinates)
        self.region_info.insert(tk.END, screen_size + coords_json)
        self._on_text_change(None)
        self.region_info.config(state='disabled')

        self.screenshot = ImageGrab.grab(
            bbox=(left, top, left + width, top + height))

        self.photo = ImageTk.PhotoImage(self.screenshot)
        self.image_canvas.delete("all")
        self.image_canvas.config(scrollregion=(
            0, 0, self.screenshot.width, self.screenshot.height))

        self.image_id = self.image_canvas.create_image(
            0, 0, anchor='nw', image=self.photo)
        self.center_image()

        self.add_scrollbars()

    def center_image(self):
        self.image_canvas.update_idletasks()
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        image_width = self.photo.width()
        image_height = self.photo.height()

        x = (canvas_width - image_width) / 2
        y = (canvas_height - image_height) / 2

        self.image_canvas.coords(self.image_id, x, y)

    def add_scrollbars(self):
        for widget in self.image_canvas.winfo_children():
            widget.destroy()

        x_scrollbar = tk.Scrollbar(
            self.image_canvas, orient=tk.HORIZONTAL, command=self.image_canvas.xview)
        y_scrollbar = tk.Scrollbar(
            self.image_canvas, orient=tk.VERTICAL, command=self.image_canvas.yview)
        self.image_canvas.config(
            xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)

        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def get_mouse_selection(self):
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes("-fullscreen", True)
        self.selection_window.attributes("-alpha", 0.3)
        self.selection_window.config(bg='black')

        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect = None

        self.canvas = tk.Canvas(self.selection_window, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=1)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.selection_window.bind("<Escape>", self.cancel_selection)

        self.root.wait_window(self.selection_window)

        return self.start_x, self.start_y, self.end_x, self.end_y

    def on_button_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root

        self.rect = self.canvas.create_rectangle(
            0, 0, 0, 0, outline='red', width=2)

    def on_move_press(self, event):
        curX = event.x_root
        curY = event.y_root

        self.canvas.delete("all")

        screen_width = self.selection_window.winfo_screenwidth()
        screen_height = self.selection_window.winfo_screenheight()
        self.canvas.create_rectangle(
            0, 0, screen_width, screen_height, fill='black', stipple='gray50')

        self.canvas.create_rectangle(self.start_x, self.start_y, curX,
                                     curY, outline='red', width=2, fill='white', stipple='gray75')

    def on_button_release(self, event):
        self.end_x = event.x_root
        self.end_y = event.y_root

        self.selection_window.destroy()

    def cancel_selection(self, event):
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.selection_window.destroy()

    def save_image(self):
        if self.screenshot:

            image_file_path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[
                                                           ("PNG files", "*.png"), ("All files", "*.*")], title="Save Image As")
            if image_file_path:

                self.screenshot.save(image_file_path)
                messagebox.showinfo("Success", "Image saved successfully.")
            else:
                messagebox.showwarning("Warning", "Image not saved.")
        else:
            messagebox.showwarning(
                "Error", "Please select a screen region first.")


if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenCaptureApp(root)
    root.mainloop()
