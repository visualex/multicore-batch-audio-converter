import sys
import os
import platform
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog, QSpinBox,
    QProgressBar, QCheckBox, QGroupBox, QListWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import multiprocessing
from convert import convert_file, get_all_audio_files, valid_exts
from functools import partial

class ConversionWorker(QThread):
    """Worker thread to handle conversion process without blocking GUI"""
    progress_updated = pyqtSignal(int)
    file_completed = pyqtSignal(bool, str)
    conversion_finished = pyqtSignal()
    
    def __init__(self, files, input_dir, output_dir, output_format, sample_rate, bit_depth, workers):
        super().__init__()
        self.files = files
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.output_format = output_format
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth
        self.workers = workers
        
    def run(self):
        from multiprocessing import Pool
        from functools import partial
        
        convert_fn = partial(
            convert_file,
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            output_format=self.output_format,
            sample_rate=self.sample_rate,
            bit_depth=self.bit_depth
        )
        
        completed = 0
        total = len(self.files)
        
        with Pool(processes=self.workers) as pool:
            for success, result in pool.imap_unordered(convert_fn, self.files):
                completed += 1
                self.progress_updated.emit(int(completed / total * 100))
                self.file_completed.emit(success, result)
        
        self.conversion_finished.emit()

class AudioConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.available_formats = ["wav", "flac", "mp3", "aiff", "ogg", "m4a"]
        self.available_sample_rates = ["44100", "48000", "96000", "192000"]
        self.available_bit_depths = ["16", "24", "32"]
        self.core_count = multiprocessing.cpu_count()
        
    def init_ui(self):
        self.setWindowTitle("Multicore Audio Batch Converter")
        self.setMinimumSize(700, 500)
        
        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        # Input directory selection
        input_group = QGroupBox("Input Settings")
        input_layout = QVBoxLayout(input_group)
        
        input_dir_layout = QHBoxLayout()
        self.input_dir_label = QLabel("No input directory selected")
        self.input_dir_button = QPushButton("Select Input Directory")
        self.input_dir_button.clicked.connect(self.select_input_dir)
        input_dir_layout.addWidget(self.input_dir_label, 1)
        input_dir_layout.addWidget(self.input_dir_button)
        input_layout.addLayout(input_dir_layout)
        
        # File extension selection
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("File extensions to process:"))
        self.ext_input = QComboBox()
        self.ext_input.addItems(["All files (*)", "Common audio (wav|mp3|flac|aiff|ogg)", "Custom..."])
        self.ext_input.currentIndexChanged.connect(self.handle_extension_change)
        ext_layout.addWidget(self.ext_input, 1)
        input_layout.addLayout(ext_layout)
        
        # Custom extensions
        self.custom_ext_widget = QWidget()
        self.custom_ext_layout = QHBoxLayout(self.custom_ext_widget)
        self.custom_ext_layout.addWidget(QLabel("Custom extensions (e.g., wav|mp3|flac):"))
        self.custom_ext_input = QComboBox()
        self.custom_ext_input.setEditable(True)
        self.custom_ext_layout.addWidget(self.custom_ext_input, 1)
        self.custom_ext_widget.setVisible(False)
        input_layout.addWidget(self.custom_ext_widget)
        
        main_layout.addWidget(input_group)
        
        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout(output_group)
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        self.output_dir_label = QLabel("No output directory selected")
        self.output_dir_button = QPushButton("Select Output Directory")
        self.output_dir_button.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(self.output_dir_label, 1)
        output_dir_layout.addWidget(self.output_dir_button)
        output_layout.addLayout(output_dir_layout)
        
        # Format settings
        format_layout = QHBoxLayout()
        
        # Output format
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["wav", "flac", "mp3", "aiff", "ogg", "m4a"])
        format_layout.addWidget(self.format_combo)
        
        # Sample rate
        format_layout.addWidget(QLabel("Sample Rate:"))
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["44100", "48000", "96000", "192000"])
        format_layout.addWidget(self.sample_rate_combo)
        
        # Bit depth
        format_layout.addWidget(QLabel("Bit Depth:"))
        self.bit_depth_combo = QComboBox()
        self.bit_depth_combo.addItems(["16", "24", "32"])
        format_layout.addWidget(self.bit_depth_combo)
        
        output_layout.addLayout(format_layout)
        
        main_layout.addWidget(output_group)
        
        # Processing settings
        processing_group = QGroupBox("Processing Settings")
        processing_layout = QHBoxLayout(processing_group)
        
        processing_layout.addWidget(QLabel("CPU Cores to use:"))
        self.cores_spinbox = QSpinBox()
        self.cores_spinbox.setMinimum(1)
        self.cores_spinbox.setMaximum(multiprocessing.cpu_count())
        self.cores_spinbox.setValue(multiprocessing.cpu_count())
        processing_layout.addWidget(self.cores_spinbox)
        
        processing_layout.addStretch(1)
        
        main_layout.addWidget(processing_group)
        
        # Log area
        log_group = QGroupBox("Conversion Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_list = QListWidget()
        log_layout.addWidget(self.log_list)
        
        main_layout.addWidget(log_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Conversion")
        self.start_button.clicked.connect(self.start_conversion)
        self.start_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_conversion)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def handle_extension_change(self, index):
        # Show custom extension input if "Custom..." is selected
        if index == 2:  # Custom option
            self.custom_ext_widget.setVisible(True)
        else:
            self.custom_ext_widget.setVisible(False)
    
    def select_input_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if dir_path:
            self.input_dir_label.setText(dir_path)
            self.update_start_button_state()
    
    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir_label.setText(dir_path)
            self.update_start_button_state()
    
    def update_start_button_state(self):
        # Enable start button only when both input and output dirs are selected
        has_input = self.input_dir_label.text() != "No input directory selected"
        has_output = self.output_dir_label.text() != "No output directory selected"
        self.start_button.setEnabled(has_input and has_output)
    
    def get_file_extensions(self):
        if self.ext_input.currentIndex() == 0:  # All files
            return "*"
        elif self.ext_input.currentIndex() == 1:  # Common audio
            return "wav|mp3|flac|aiff|ogg"
        else:  # Custom
            return self.custom_ext_input.currentText()
    
    def start_conversion(self):
        input_dir = Path(self.input_dir_label.text()).resolve()
        output_dir = Path(self.output_dir_label.text()).resolve()
        
        # Create output dir if it doesn't exist
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        
        exts = valid_exts(self.get_file_extensions())
        files = get_all_audio_files(input_dir, exts)
        
        if not files:
            QMessageBox.warning(self, "No Files Found", "No matching audio files were found in the selected directory.")
            return
        
        # Clear log and reset progress
        self.log_list.clear()
        self.progress_bar.setValue(0)
        
        # Update UI state
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        
        # Add initial log entry
        self.log_list.addItem(f"Found {len(files)} files to convert")
        
        # Start conversion worker
        self.worker = ConversionWorker(
            files=files,
            input_dir=input_dir,
            output_dir=output_dir,
            output_format=self.format_combo.currentText(),
            sample_rate=self.sample_rate_combo.currentText(),
            bit_depth=self.bit_depth_combo.currentText(),
            workers=self.cores_spinbox.value()
        )
        
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_completed.connect(self.log_file_completion)
        self.worker.conversion_finished.connect(self.handle_conversion_finished)
        
        self.worker.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def log_file_completion(self, success, result):
        if success:
            # Use the basename of the file for cleaner display
            filename = os.path.basename(result)
            self.log_list.addItem(f"✓ Converted: {filename}")
        else:
            self.log_list.addItem(f"✗ Error: {result}")
        # Auto-scroll to bottom
        self.log_list.scrollToBottom()
    
    def handle_conversion_finished(self):
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        QMessageBox.information(self, "Conversion Complete", "Audio conversion has been completed.")
    
    def cancel_conversion(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.log_list.addItem("Conversion canceled by user")
            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(False)

def main():
    app = QApplication(sys.argv)
    
    # Set application name and organization for settings
    app.setApplicationName("AudioBatchConverter")
    app.setOrganizationName("AudioBatchConverter")
    
    # Adjust style based on platform
    if platform.system() == "Windows":
        app.setStyle("Fusion")  # More consistent look on Windows
    
    window = AudioConverterGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()