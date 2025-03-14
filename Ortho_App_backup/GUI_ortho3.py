import os
import pydicom
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk

class DicomViewerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DICOM Viewer")
        self.geometry("800x600")

        # Button to select folder
        self.select_button = ctk.CTkButton(
            self, text="Select DICOM Folder", command=self.select_folder
        )
        self.select_button.pack(pady=20)

        # Label to display the DICOM slice
        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.pack()

    def select_folder(self):
        folder_path = ctk.filedialog.askdirectory(title="Select DICOM Folder")
        if folder_path:
            self.display_middle_slice(folder_path)

    def display_middle_slice(self, folder_path):
        try:
            # Load DICOM files from the folder
            dicom_files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.endswith(".dcm")
            ]
            if not dicom_files:
                raise ValueError("No DICOM files found in the selected folder.")

            # Read and sort the DICOM files by InstanceNumber
            slices = [pydicom.dcmread(f) for f in dicom_files]
            slices.sort(key=lambda x: int(x.InstanceNumber))

            # Get the middle slice
            middle_slice = slices[len(slices) // 2]
            pixel_array = middle_slice.pixel_array

            # Normalize pixel values for better visualization
            pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array))
            pixel_array = (pixel_array * 255).astype(np.uint8)

            # Convert to a PIL Image for display
            image = Image.fromarray(pixel_array)
            image = image.resize((400, 400))  # Resize for display
            image_tk = ImageTk.PhotoImage(image)

            # Display the image in the label
            self.image_label.configure(image=image_tk)
            self.image_label.image = image_tk  # Keep a reference to avoid garbage collection

        except Exception as e:
            ctk.messagebox.showerror("Error", f"Failed to load DICOM files: {e}")

if __name__ == "__main__":
    app = DicomViewerApp()
    app.mainloop()
