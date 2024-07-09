import tkinter as tk
from PIL import Image, ImageTk
import random
import string
import pygame
import os

# Initialize Pygame for music
pygame.mixer.init()
pygame.mixer.music.load("background_music.mp3")  # Make sure you have a music file named "background_music.mp3" in the same directory
pygame.mixer.music.play(-1)  # Loop the music indefinitely

# Function to generate a random key with a specific format
def generate_key():
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) for _ in range(5)]
    key = '-'.join(parts)
    key_entry.config(state=tk.NORMAL)
    key_entry.delete(0, tk.END)
    key_entry.insert(0, key)
    key_entry.config(state=tk.DISABLED)

# Function to create a pulsating effect
def pulsate():
    color = random.choice(['#00FF00', '#FF0000', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'])
    title_label.config(fg=color)
    root.after(500, pulsate)

# Function to close the application
def close_app():
    root.destroy()

# Functions to make the window draggable
def start_move(event):
    root.x = event.x
    root.y = event.y

def do_move(event):
    deltax = event.x - root.x
    deltay = event.y - root.y
    new_pos = f"+{root.winfo_x() + deltax}+{root.winfo_y() + deltay}"
    root.geometry(new_pos)

# Setting up the main window
root = tk.Tk()
root.title("Keygen 2000s Style")
root.geometry("600x400")
root.overrideredirect(True)  # Remove the window border

# Check if background image file exists
background_image_path = "background.jpg"
if not os.path.exists(background_image_path):
    raise FileNotFoundError(f"Background image file '{background_image_path}' not found. Please make sure it exists in the same directory as the script.")

# Load and set background image
bg_image = Image.open(background_image_path)
bg_image = bg_image.resize((600, 400), Image.LANCZOS)
bg_photo = ImageTk.PhotoImage(bg_image)
background_label = tk.Label(root, image=bg_photo)
background_label.place(relwidth=1, relheight=1)

# Adding a close button
close_button = tk.Button(root, text="X", command=close_app, font=("Courier", 12, "bold"), bg="red", fg="white")
close_button.place(x=570, y=10)

# Adding a title label
title_label = tk.Label(root, text="PeoneerDJ wav Correcor", font=("Courier", 24, "bold"), bg="black", fg="lime")
title_label.pack(pady=20)

# Adding the key entry
key_entry = tk.Entry(root, font=("Courier", 16), width=30, justify='center', state=tk.DISABLED)
key_entry.pack(pady=20)

# Adding a generate button
generate_button = tk.Button(root, text="Generate Key", command=generate_key, font=("Courier", 16), bg="lime", fg="black")
generate_button.pack(pady=20)

# Adding a footer label
footer_label = tk.Label(root, text="© Podval tvoyu mamku ebal", font=("Courier", 12), bg="black", fg="lime")
footer_label.pack(side="bottom", pady=10)

# Bind the draggable functions
root.bind("<Button-1>", start_move)
root.bind("<B1-Motion>", do_move)

# Start the pulsating effect
pulsate()

# Running the GUI loop
root.mainloop()
