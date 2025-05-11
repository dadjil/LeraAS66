import tkinter as tk
from interface_manager import ApplicationInterface

if __name__ == "__main__":
    root = tk.Tk()
    app = ApplicationInterface(root)
    root.mainloop()