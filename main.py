"""
Script de Conversão de PDF/Imagem para DICOM

Este aplicativo converte arquivos PDF ou imagens (PNG, JPG, BMP, TIFF) em arquivos DICOM,
preservando os metadados de um DICOM de origem selecionado pelo usuário. Permite uso em clínicas,
hospitais e ambientes de diagnóstico para arquivamento e interoperabilidade de imagens médicas.

Autor: Julio Cesar Nather Junior
Ano: 2025
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import generate_uid, ExplicitVRLittleEndian, PYDICOM_IMPLEMENTATION_UID
from PIL import Image # Pillow is imported as PIL
from pdf2image import convert_from_path
import os
import datetime
import traceback # For detailed error logging if needed

class DicomConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Conversor DICOM de PDF/Imagem")
        master.geometry("700x650")

        self.source_dicom_path = tk.StringVar()
        self.source_file_path = tk.StringVar() # PDF or Image
        # We'll use source file directory as output directory
        self.output_folder_path = tk.StringVar()

        self.study_instance_uid = tk.StringVar(value="N/A")
        self.patient_name = tk.StringVar(value="N/A")
        self.patient_id = tk.StringVar(value="N/A")
        self.study_date = tk.StringVar(value="N/A")
        self.study_description = tk.StringVar(value="N/A")

        # --- Configure Styles ---
        self._setup_styles()

        # --- UI Elements ---
        main_frame = ttk.Frame(master, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # App Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 15), sticky='ew')
        ttk.Label(header_frame, text="Conversor DICOM", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Separator(main_frame, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 15), padx=5)

        # Source DICOM Selection
        ttk.Label(main_frame, text="1. Selecione o DICOM de origem (para modelo de metadados):", style="Step.TLabel").grid(row=2, column=0, padx=5, pady=(0,5), sticky='w')
        source_dicom_frame = ttk.Frame(main_frame)
        source_dicom_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=(0,15), sticky='ew')
        ttk.Entry(source_dicom_frame, textvariable=self.source_dicom_path, width=60, style="App.TEntry").pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(source_dicom_frame, text="Procurar...", command=self.browse_source_dicom, style="Browse.TButton").pack(side=tk.LEFT, padx=(8,0))

        # Extracted DICOM Info Display
        info_frame = ttk.LabelFrame(main_frame, text="Informações do DICOM de Origem", padding=(10, 8), style="Info.TLabelframe")
        info_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=10, sticky='ew')

        ttk.Label(info_frame, text="StudyInstanceUID:", style="InfoLabel.TLabel").grid(row=0, column=0, sticky='w', pady=3)
        ttk.Label(info_frame, textvariable=self.study_instance_uid, wraplength=450, justify=tk.LEFT, style="InfoValue.TLabel").grid(row=0, column=1, sticky='w', padx=5, pady=3)
        ttk.Label(info_frame, text="Nome do Paciente:", style="InfoLabel.TLabel").grid(row=1, column=0, sticky='w', pady=3)
        ttk.Label(info_frame, textvariable=self.patient_name, style="InfoValue.TLabel").grid(row=1, column=1, sticky='w', padx=5, pady=3)
        ttk.Label(info_frame, text="ID do Paciente:", style="InfoLabel.TLabel").grid(row=2, column=0, sticky='w', pady=3)
        ttk.Label(info_frame, textvariable=self.patient_id, style="InfoValue.TLabel").grid(row=2, column=1, sticky='w', padx=5, pady=3)
        ttk.Label(info_frame, text="Data do Estudo:", style="InfoLabel.TLabel").grid(row=3, column=0, sticky='w', pady=3)
        ttk.Label(info_frame, textvariable=self.study_date, style="InfoValue.TLabel").grid(row=3, column=1, sticky='w', padx=5, pady=3)
        ttk.Label(info_frame, text="Descrição do Estudo:", style="InfoLabel.TLabel").grid(row=4, column=0, sticky='w', pady=3)
        ttk.Label(info_frame, textvariable=self.study_description, style="InfoValue.TLabel").grid(row=4, column=1, sticky='w', padx=5, pady=3)
        info_frame.columnconfigure(1, weight=1)
        
        # Apply a styled separator between sections
        ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky='ew', pady=15, padx=5)

        # PDF/Image Selection
        self.source_file_types = (
            ("Arquivos Suportados", "*.pdf *.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
            ("Arquivos PDF", "*.pdf"),
            ("Arquivos de Imagem (PNG, JPG, BMP, TIFF)", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
            ("Todos os arquivos", "*.*")
        )
        ttk.Label(main_frame, text="2. Selecione o PDF ou Arquivo de Imagem para Converter:", style="Step.TLabel").grid(row=6, column=0, padx=5, pady=(0,5), sticky='w')
        source_file_frame = ttk.Frame(main_frame)
        source_file_frame.grid(row=7, column=0, columnspan=2, padx=5, pady=(0,15), sticky='ew')
        ttk.Entry(source_file_frame, textvariable=self.source_file_path, width=60, style="App.TEntry").pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(source_file_frame, text="Procurar...", command=self.browse_source_file, style="Browse.TButton").pack(side=tk.LEFT, padx=(8,0))

        # Add an information note about saving location
        ttk.Label(main_frame, text="Nota: Os arquivos DICOM serão salvos na mesma pasta do arquivo de origem", 
                 style="Note.TLabel").grid(row=8, column=0, columnspan=2, padx=5, pady=(0,15), sticky='w')

        # Convert Button - Usando tk.Button em vez de ttk.Button para melhor controle de cores
        self.convert_button = tk.Button(main_frame, text="Converter e Salvar Nova Série DICOM", 
                                    command=self.convert_and_save_dicom,
                                    bg="#FF5722", fg="white", font=('Arial', 11, 'bold'),
                                    activebackground="#E64A19", activeforeground="white",
                                    relief=tk.RAISED, padx=15, pady=8, bd=2)
        self.convert_button.grid(row=9, column=0, columnspan=2, pady=15)

        # Progress Bar
        self.progress_label = ttk.Label(main_frame, text="", style="Progress.TLabel")
        self.progress_label.grid(row=10, column=0, columnspan=2, pady=(10,0), padx=5, sticky='ew')
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=300, mode="determinate", style="App.Horizontal.TProgressbar")
        self.progress_bar.grid(row=11, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
        
        # Attribution text at the bottom
        ttk.Separator(main_frame, orient='horizontal').grid(row=12, column=0, columnspan=2, sticky='ew', pady=(15, 10), padx=5)
        ttk.Label(main_frame, text="Desenvolvido por Julio Cesar Nather Junior", style="Attribution.TLabel").grid(row=13, column=0, columnspan=2, padx=5, pady=(0, 5), sticky='e')
        
        main_frame.columnconfigure(0, weight=1)
        
    def _setup_styles(self):
        """Set up the ttk styles for a more modern UI"""
        style = ttk.Style()
        
        # Define colors
        primary_color = "#1976D2"  # Medium blue
        secondary_color = "#64B5F6"  # Light blue
        text_color = "#212121"  # Almost black
        bg_color = "#F5F5F5"  # Light gray
        accent_color = "#FF5722"  # Orange - mais brilhante para o botão de converter
        hover_color = "#E64A19"  # Dark orange
        info_bg = "#E3F2FD"  # Very light blue
        
        # Configure the window background
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=text_color)
        style.configure("TLabelframe", background=bg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=text_color, font=('Arial', 10, 'bold'))
        
        # Header style
        style.configure("Header.TLabel", font=('Arial', 16, 'bold'), foreground=primary_color, background=bg_color)
        
        # Step headers
        style.configure("Step.TLabel", font=('Arial', 11, 'bold'), foreground=primary_color, background=bg_color)
        
        # Info frame
        style.configure("Info.TLabelframe", background=info_bg)
        style.configure("Info.TLabelframe.Label", background=bg_color, foreground=primary_color, font=('Arial', 10, 'bold'))
        style.configure("InfoLabel.TLabel", background=info_bg, foreground=text_color, font=('Arial', 9, 'bold'))
        style.configure("InfoValue.TLabel", background=info_bg, foreground=text_color)
        
        # Note style
        style.configure("Note.TLabel", foreground="#757575", font=('Arial', 9, 'italic'), background=bg_color)
        
        # Entry styling
        style.configure("App.TEntry", borderwidth=1)
        
        # Button styling
        style.configure("Browse.TButton", font=('Arial', 9))
        style.configure("Convert.TButton", font=('Arial', 11, 'bold'), background=accent_color, foreground="white")
        style.map("Convert.TButton",
                 background=[('active', hover_color), ('pressed', accent_color)],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        # Progress indicators
        style.configure("Progress.TLabel", font=('Arial', 10), background=bg_color)
        style.configure("App.Horizontal.TProgressbar", background=accent_color, troughcolor=bg_color)
        
        # Attribution
        style.configure("Attribution.TLabel", font=('Arial', 8), foreground="#757575", background=bg_color)

    def browse_source_dicom(self):
        filepath = filedialog.askopenfilename(
            title="Selecione o Arquivo DICOM de Origem (modelo de metadados)",
            filetypes=(("Arquivos DICOM", "*.dcm"), ("Todos os arquivos", "*.*"))
        )
        if filepath:
            self.source_dicom_path.set(filepath)
            self.load_dicom_info()

    def load_dicom_info(self):
        try:
            ds = pydicom.dcmread(self.source_dicom_path.get(), force=True)
            self.study_instance_uid.set(ds.get("StudyInstanceUID", "N/A"))
            self.patient_name.set(str(ds.get("PatientName", "N/A")))
            self.patient_id.set(ds.get("PatientID", "N/A"))
            self.study_date.set(ds.get("StudyDate", "N/A"))
            self.study_description.set(ds.get("StudyDescription", "N/A"))
        except Exception as e:
            messagebox.showerror("Erro ao Carregar DICOM de Origem", f"Não foi possível ler ou analisar o arquivo DICOM: {e}\nVerifique se é um arquivo DICOM válido.")
            self.study_instance_uid.set("N/A"); self.patient_name.set("N/A"); self.patient_id.set("N/A")
            self.study_date.set("N/A"); self.study_description.set("N/A")

    def browse_source_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecione o PDF ou Arquivo de Imagem para Converter",
            filetypes=self.source_file_types
        )
        if filepath:
            self.source_file_path.set(filepath)

    def _get_dicom_tag_or_default(self, ds, tag_name, default_value=""):
        return ds.get(tag_name, default_value)

    def convert_and_save_dicom(self):
        source_dcm_path = self.source_dicom_path.get()
        source_file_to_convert = self.source_file_path.get()
        
        # Get the directory of the source file as output directory
        output_dir = os.path.dirname(source_file_to_convert)
        self.output_folder_path.set(output_dir)

        if not all([source_dcm_path, source_file_to_convert]):
            messagebox.showerror("Informações Faltando", "Por favor, selecione o DICOM de origem e o arquivo a ser convertido.")
            return

        self.progress_label.config(text="Starting conversion...")
        self.progress_bar["value"] = 0
        self.master.update_idletasks()

        try:
            self.progress_label.config(text="Lendo modelo de DICOM de origem..."); self.progress_bar["value"] = 5; self.master.update_idletasks()
            source_ds_template = pydicom.dcmread(source_dcm_path, force=True)

            self.progress_label.config(text=f"Carregando {os.path.basename(source_file_to_convert)}..."); self.progress_bar["value"] = 15; self.master.update_idletasks()
            images_to_convert = []
            file_ext = os.path.splitext(source_file_to_convert)[1].lower()

            if file_ext == ".pdf":
                try:
                    images_to_convert = convert_from_path(source_file_to_convert, dpi=300)
                except Exception as e:
                    messagebox.showerror("Erro na Conversão do PDF", f"Não foi possível converter o PDF: {e}\nVerifique se o Poppler está instalado e no PATH do sistema.")
                    self.progress_label.config(text="Falha na conversão do PDF."); self.progress_bar["value"] = 0; return
            elif file_ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]:
                images_to_convert.append(Image.open(source_file_to_convert))
            else:
                messagebox.showerror("Tipo de Arquivo não Suportado", f"O tipo de arquivo '{file_ext}' não é suportado para conversão.")
                self.progress_label.config(text="Arquivo não suportado."); self.progress_bar["value"] = 0; return

            if not images_to_convert:
                messagebox.showerror("Nenhuma Imagem Encontrada", "Nenhuma imagem foi encontrada no arquivo de origem selecionado.")
                self.progress_label.config(text="Nenhuma imagem encontrada."); self.progress_bar["value"] = 0; return

            total_images = len(images_to_convert)
            self.progress_bar["maximum"] = 100

            new_study_instance_uid = source_ds_template.StudyInstanceUID
            new_series_instance_uid = generate_uid()
            new_series_instance_uid_short = new_series_instance_uid.split('.')[-1][:8]
            sop_class_uid_sc = "1.2.840.10008.5.1.4.1.1.7" # Secondary Capture

            current_date = datetime.date.today().strftime("%Y%m%d")
            current_time = datetime.datetime.now().strftime("%H%M%S.%f")[:13]

            for i, pil_image in enumerate(images_to_convert):
                self.progress_label.config(text=f"Processando imagem {i+1} de {total_images}...")
                current_progress = 20 + int(((i + 1) / total_images) * 75); self.progress_bar["value"] = current_progress; self.master.update_idletasks()

                ds = Dataset()
                ds.is_little_endian = True
                ds.is_implicit_VR = False

                # --- File Meta Information (Group 0002 Tags ONLY) ---
                ds.file_meta = FileMetaDataset()
                ds.file_meta.MediaStorageSOPClassUID = sop_class_uid_sc
                ds.file_meta.MediaStorageSOPInstanceUID = generate_uid() # Unique SOP Instance UID for this image
                ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
                ds.file_meta.ImplementationClassUID = PYDICOM_IMPLEMENTATION_UID
                ds.file_meta.ImplementationVersionName = "PYDICOM " + pydicom.__version__

                # --- Main Dataset Tags ---
                ds.SpecificCharacterSet = "ISO_IR 100" # For the main dataset

                # Patient Module
                ds.PatientName = self._get_dicom_tag_or_default(source_ds_template, "PatientName", "UNKNOWN")
                ds.PatientID = self._get_dicom_tag_or_default(source_ds_template, "PatientID", "UNKNOWN")
                ds.PatientBirthDate = self._get_dicom_tag_or_default(source_ds_template, "PatientBirthDate", "")
                ds.PatientSex = self._get_dicom_tag_or_default(source_ds_template, "PatientSex", "")

                # General Study Module
                ds.StudyInstanceUID = new_study_instance_uid
                ds.StudyDate = self._get_dicom_tag_or_default(source_ds_template, "StudyDate", current_date)
                ds.StudyTime = self._get_dicom_tag_or_default(source_ds_template, "StudyTime", current_time)
                ds.ReferringPhysicianName = self._get_dicom_tag_or_default(source_ds_template, "ReferringPhysicianName", "")
                ds.StudyID = self._get_dicom_tag_or_default(source_ds_template, "StudyID", "1")
                ds.AccessionNumber = self._get_dicom_tag_or_default(source_ds_template, "AccessionNumber", "")
                original_study_desc = self._get_dicom_tag_or_default(source_ds_template, "StudyDescription", "SecondaryCapture")
                ds.StudyDescription = (original_study_desc + f" - Converted {os.path.basename(source_file_to_convert)}")[:64]

                # General Series Module
                ds.SeriesInstanceUID = new_series_instance_uid
                ds.SeriesNumber = str(self._get_dicom_tag_or_default(source_ds_template, "SeriesNumber", "999"))
                ds.Modality = "OT" # Other
                ds.SeriesDate = current_date
                ds.SeriesTime = current_time
                series_desc = f"Converted {os.path.basename(source_file_to_convert)}"
                if file_ext == ".pdf" and total_images > 1: series_desc += f" - Page {i+1}"
                ds.SeriesDescription = series_desc[:64]
                ds.Laterality = self._get_dicom_tag_or_default(source_ds_template, "Laterality", "")

                # SOP Common Module
                ds.SOPClassUID = sop_class_uid_sc
                ds.SOPInstanceUID = ds.file_meta.MediaStorageSOPInstanceUID # Match File Meta
                ds.InstanceNumber = str(i + 1) # This is where InstanceNumber is set as a string
                ds.ContentDate = current_date
                ds.ContentTime = current_time
                ds.AcquisitionDateTime = current_date + current_time # SC usually current datetime

                # Image Pixel Module & Image Processing
                if pil_image.mode == 'L':
                    ds.SamplesPerPixel = 1; ds.PhotometricInterpretation = "MONOCHROME2"
                elif pil_image.mode == 'LA': # Grayscale with Alpha
                    pil_image = pil_image.convert('L'); ds.SamplesPerPixel = 1; ds.PhotometricInterpretation = "MONOCHROME2"
                elif pil_image.mode == 'RGBA':
                    pil_image = pil_image.convert('RGB'); ds.SamplesPerPixel = 3; ds.PhotometricInterpretation = "RGB"
                elif pil_image.mode == 'P': # Palette
                    pil_image = pil_image.convert('RGB'); ds.SamplesPerPixel = 3; ds.PhotometricInterpretation = "RGB"
                elif pil_image.mode != 'RGB': # Other (CMYK, etc.)
                    pil_image = pil_image.convert('RGB'); ds.SamplesPerPixel = 3; ds.PhotometricInterpretation = "RGB"
                else: # Already RGB
                    ds.SamplesPerPixel = 3; ds.PhotometricInterpretation = "RGB"

                ds.Rows = pil_image.height
                ds.Columns = pil_image.width
                ds.BitsAllocated = 8
                ds.BitsStored = 8
                ds.HighBit = 7
                ds.PixelRepresentation = 0 # Unsigned

                if ds.SamplesPerPixel == 3: ds.PlanarConfiguration = 0 # Pixel-interleaved

                ds.PixelData = pil_image.tobytes()

                # Secondary Capture Image Module
                ds.ConversionType = "WSD" # Workstation
                ds.DateOfSecondaryCapture = current_date
                ds.TimeOfSecondaryCapture = current_time
                if ds.PhotometricInterpretation == "MONOCHROME2": ds.PresentationLUTShape = "IDENTITY"

                # --- CORRECTED FILENAME GENERATION ---
                instance_number_str = str(ds.InstanceNumber) # Explicitly convert InstanceNumber to string
                output_filename = os.path.join(output_dir, f"SC_{new_series_instance_uid_short}_{instance_number_str.zfill(3)}.dcm")
                
                pydicom.dcmwrite(output_filename, ds, write_like_original=False)

            # Get the filename of the first DICOM saved (or only one if there's just one image)
            first_dicom_filename = f"SC_{new_series_instance_uid_short}_001.dcm"
            self.progress_label.config(text=f"Conversão bem-sucedida! {total_images} arquivo(s) DICOM salvo(s) em {output_dir}.")
            self.progress_bar["value"] = 100
            messagebox.showinfo("Sucesso", f"{total_images} arquivo(s) DICOM criado(s) com sucesso em '{output_dir}'.\nArquivo: {first_dicom_filename}")

        except FileNotFoundError as e:
            messagebox.showerror("Erro: Arquivo Não Encontrado", str(e)); self.progress_label.config(text="Conversão falhou: Arquivo não encontrado.")
        except pydicom.errors.InvalidDicomError as e:
            messagebox.showerror("DICOM de Origem Inválido", f"O DICOM de origem não pôde ser lido: {e}\nPode estar corrompido ou inválido."); self.progress_label.config(text="Conversão falhou: DICOM de origem inválido.")
        except Exception as e:
            messagebox.showerror("Erro de Conversão", f"Ocorreu um erro inesperado durante a conversão: {e}")
            self.progress_label.config(text="Conversão falhou: Erro inesperado.")
            print(traceback.format_exc()) # Log detailed error to console
        finally:
            if not self.progress_label.cget("text").startswith("Conversão bem-sucedida"): self.progress_bar["value"] = 0
            self.master.update_idletasks()

if __name__ == '__main__':
    root = tk.Tk()
    app = DicomConverterApp(root)
    root.mainloop()