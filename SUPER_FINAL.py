import os
import shutil
import cv2

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout, QCheckBox, QPushButton, QFileDialog, QComboBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QSize


class ImageBrowser(QWidget):
    def __init__(self, folder_path, fname):
        super().__init__()

        self.setWindowTitle("Image Annotator")

        # Set background color
        self.setStyleSheet("background-color: lightblue;")

        self.folder_path = folder_path
        self.fname = fname

        # Create the main layout
        main_layout = QHBoxLayout()

        # Create a QLabel for displaying the selected image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.image_label)

        image_file = [file for file in os.listdir(fname) if file.endswith(".png") or file.endswith(".jpg")]
        #parent image
        self.parent_image_path = os.path.join(fname, image_file[0])
        self.parent_image = cv2.imread(self.parent_image_path)
        pixmap = self.convert_cv_image_to_pixmap(self.parent_image)
        self.image_label.setPixmap(pixmap)  # Update the displayed image

        # Create a scrollable area for displaying the images and checkboxes
        scroll_area = QScrollArea()
        scroll_widget = QWidget()

        # Create a layout for the scrollable area
        scroll_layout = QVBoxLayout(scroll_widget)

        # Get the list of image files in the folder
        image_files = [file for file in os.listdir(folder_path) if file.endswith(".png") or file.endswith(".jpg")]

        self.selected_files = []
        self.dropdowns = {}  # Dictionary to store dropdowns for each image

        # Create QLabel, QCheckBox, and QComboBox for each image file
        for image_file in image_files:
            image_path = os.path.join(folder_path, image_file)
            image_label = QLabel()
            pixmap = QPixmap(image_path).scaledToWidth(200)  # Scale the image width to 200 pixels
            image_label.setPixmap(pixmap)

            checkbox = QCheckBox()
            checkbox.setText(image_file)
            checkbox.stateChanged.connect(lambda state, file=image_file: self.checkbox_state_changed(state, file, pixmap))

            # Add hover event handlers to the image label
            image_label.enterEvent = lambda event, label=image_label, path=image_path: self.image_label_hover_enter(event, label, path)
            image_label.leaveEvent = lambda event: self.image_label_hover_leave(event)

            #add dropdown menu with three options pet, human , prop 
            dropdown = QComboBox()
            dropdown.addItem("Pet")
            dropdown.addItem("Human")
            dropdown.addItem("Prop")

            # Add the dropdown to the dictionary with the image file as the key
            self.dropdowns[image_file] = dropdown

            # Add the image, checkbox, and dropdown to the scroll layout
            image_layout = QHBoxLayout()
            image_layout.addWidget(image_label)
            image_layout.addWidget(checkbox)
            image_layout.addWidget(dropdown)
            scroll_layout.addLayout(image_layout)

        # Set the scrollable area widget and layout
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        # Add the scrollable area to the main layout
        main_layout.addWidget(scroll_area)

        # Add a save button
        save_button = QPushButton("SAVE")
        save_button.clicked.connect(self.save_files)
        main_layout.addWidget(save_button)
        
        # Add another save2 button
        save2_button = QPushButton("COMBINE")
        save2_button.clicked.connect(self.save_combined_images)
        main_layout.addWidget(save2_button)


        self.setLayout(main_layout)


    def checkbox_state_changed(self, state, file, pixmap):

        if state == 2:
            self.selected_files.append(file)

        elif state == 0:
            self.selected_files.remove(file)


    def save_files(self):

        if not self.selected_files:

            print("No files selected.")
            return
        
        # Ask for the final destination folder
        save_folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if save_folder:

            mask_folder = os.path.join(save_folder, os.path.basename(self.folder_path) + "_mask")
            os.makedirs(mask_folder, exist_ok=True)

            for file in self.selected_files:

                selected_option = self.dropdowns[file].currentText()
                subfolder = os.path.join(mask_folder, selected_option.lower())
                os.makedirs(subfolder, exist_ok=True)

                source_path = os.path.join(self.folder_path, file)
                destination_path = os.path.join(subfolder, file)
                try:
                    shutil.copy(source_path, destination_path)
                except Exception as e:
                    print(f"An error occurred while saving {file}: {str(e)}")
            print("Files saved successfully.")



    def save_combined_images(self):
        if not self.selected_files:
            print("No files selected.")
            return
        
        # Ask for the final destination folder
        save_folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")

        if save_folder:

            combined_folder = os.path.join(save_folder, os.path.basename(self.folder_path) + "_combined")
            os.makedirs(combined_folder, exist_ok=True)
            
            combined_image = None

            for file in self.selected_files:
                image_path = os.path.join(self.folder_path, file)
                try:
                    image = cv2.imread(image_path)
                    if combined_image is None:
                        combined_image = image
                    else:
                        combined_image = cv2.addWeighted(combined_image, 0.5, image, 0.5, 0)
                except Exception as e:
                    print(f"An error occurred while processing {file}: {str(e)}")

            if combined_image is not None:
                save_path = os.path.join(combined_folder, "combined_image.jpg")
                cv2.imwrite(save_path, combined_image)
                print("Combined image saved successfully.")
            else:
                print("No images found for combining.")



    def image_label_hover_enter(self, event, label, path):

        try:
            image = cv2.imread(path)
            combined_image = cv2.addWeighted(self.parent_image, 0.5, image, 0.5, 0)
            pixmap = self.convert_cv_image_to_pixmap(combined_image)
            self.image_label.setPixmap(pixmap)

        except Exception as e:
            print(f"An error occurred while processing {path}: {str(e)}")



    def image_label_hover_leave(self, event):

        pixmap = self.convert_cv_image_to_pixmap(self.parent_image)
        self.image_label.setPixmap(pixmap)


    def convert_cv_image_to_pixmap(self, image):

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        return pixmap.scaledToWidth(400)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Take image path input
    folder_path = QFileDialog.getExistingDirectory(None, "Select Folder", "")
    fname = QFileDialog.getExistingDirectory(None, "Select Folder", "")

    # Call image browser function with folder path as argument
    image_browser = ImageBrowser(folder_path, fname)
    image_browser.show()

    sys.exit(app.exec_())
