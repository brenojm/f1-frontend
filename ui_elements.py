import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
from datetime import datetime
import os

# Paleta de Cores
COLOR_BACKGROUND_DARK = "#1A1A1A"
COLOR_BACKGROUND_MEDIUM = "#2B2B2B"
COLOR_BACKGROUND_LIGHT = "#3A3A3A"

COLOR_FOREGROUND_LIGHT = "#F0F0F0"
COLOR_FOREGROUND_DARK = "#C0C0C0"

COLOR_PRIMARY_ACCENT = "#E10600"
COLOR_SUCCESS_ACCENT = "#00B050"
COLOR_DANGER_ACCENT = "#FF4500"

COLOR_BUTTON_TEXT = "white"
COLOR_BORDER_FOCUS = "#FF8C00"

ICONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

def load_icon(icon_name, size=(24, 24)):
    """Carrega um ícone da pasta 'icons'."""
    icon_path = os.path.join(ICONS_PATH, f"{icon_name}.png")
    if os.path.exists(icon_path):
        try:
            img = Image.open(icon_path)
            img.thumbnail(size, Image.LANCZOS)
            photo_image = ImageTk.PhotoImage(img)
            return photo_image
        except Exception as e:
            print(f"ERRO: Falha ao carregar ícone {icon_path}. Motivo: {e}")
            return None
    return None

def format_date_display(date_str):
    if not date_str:
        return ""
    try:
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return dt_obj.strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def format_date_api(date_str):
    if not date_str:
        return ""
    try:
        dt_obj = datetime.strptime(date_str, "%d/%m/%Y")
        return dt_obj.strftime("%Y-%m-%d")
    except ValueError:
        return date_str

class LabeledEntry(tk.Frame):
    def __init__(self, parent, label_text, entry_width=30, readonly=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.config(bg=parent.cget('bg'))

        self.label = ttk.Label(self, text=label_text, style="Monochromatic.TLabel")
        self.label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry = ttk.Entry(self, width=entry_width, style="Monochromatic.TEntry")
        self.entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        if readonly:
            self.entry.config(state='readonly')

    def get(self):
        return self.entry.get()

    def set(self, value):
        self.entry.config(state='normal')
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        if self.entry.cget('state') == 'readonly':
             self.entry.config(state=self.entry.cget('state'))


class LabeledSpinbox(tk.Frame):
    def __init__(self, parent, label_text, from_=0, to=100, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.config(bg=parent.cget('bg'))

        self.label = ttk.Label(self, text=label_text, style="Monochromatic.TLabel")
        self.label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.spinbox_var = tk.IntVar()
        self.spinbox = ttk.Spinbox(self, from_=from_, to=to, textvariable=self.spinbox_var,
                                 style="Monochromatic.TEntry")
        self.spinbox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

    def get(self):
        return self.spinbox_var.get()

    def set(self, value):
        self.spinbox_var.set(value)

class LabeledCombobox(tk.Frame):
    def __init__(self, parent, label_text, values_map, default_id=None, **kwargs):
        """
        values_map should be a dictionary like {id: name, ...} for ID-Name mapping.
        If just a list of strings, pass it directly.
        """
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.config(bg=parent.cget('bg'))

        self.label = ttk.Label(self, text=label_text, style="Monochromatic.TLabel")
        self.label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self._id_to_name = values_map if isinstance(values_map, dict) else {}
        self._name_to_id = {str(v): k for k, v in values_map.items()} if isinstance(values_map, dict) else {}
        
        display_values = list(values_map.values()) if isinstance(values_map, dict) else list(values_map)
        self._display_values = [str(v) for v in display_values]

        self.combobox_var = tk.StringVar()
        self.combobox = ttk.Combobox(self, textvariable=self.combobox_var, values=self._display_values,
                                     state="readonly", style="Monochromatic.TCombobox")
        self.combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        if default_id is not None:
            self.set_by_id(default_id)
        elif self._display_values:
            self.combobox.set(self._display_values[0])

    def get_id(self):
        selected_name = self.combobox_var.get()
        return self._name_to_id.get(selected_name)

    def get_name(self):
        return self.combobox_var.get()

    def set_by_id(self, item_id):
        name = self._id_to_name.get(item_id, "")
        self.combobox_var.set(str(name))
    
    def set_by_name(self, name):
        self.combobox_var.set(str(name))

class LabeledCheckbutton(tk.Frame):
    def __init__(self, parent, label_text, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=parent.cget('bg'))

        self.var = tk.BooleanVar()
        self.checkbutton = ttk.Checkbutton(self, text=label_text, variable=self.var,
                                          style="Monochromatic.TCheckbutton")
        self.checkbutton.pack(padx=5, pady=5, anchor="w")

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

class ImagePreview(tk.Frame):
    def __init__(self, parent, label_text="Pré-visualização da Imagem:", max_size=(200, 200), **kwargs):
        super().__init__(parent, **kwargs)
        self.max_size = max_size
        
        self.columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.config(bg=parent.cget('bg'))

        self.image_label = tk.Label(self, bg=COLOR_BACKGROUND_MEDIUM, relief="flat", bd=0, highlightthickness=0) 
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.default_photo_image = load_icon("default_image", size=self.max_size) 
        if self.default_photo_image:
            self.image_label.config(image=self.default_photo_image)
        else:
            self.image_label.config(text="Sem Imagem", fg=COLOR_FOREGROUND_DARK)
        self.image = None


    def load_image_from_url(self, url):
        self.image_label.config(image='')
        self.image = None

        if not url:
            if self.default_photo_image:
                self.image_label.config(image=self.default_photo_image, text="")
            else:
                self.image_label.config(text="Sem Imagem", fg=COLOR_FOREGROUND_DARK)
            return

        self.image_label.config(text="Carregando...", fg=COLOR_FOREGROUND_DARK)
        try:
            response = requests.get(url, stream=True, timeout=5)
            response.raise_for_status()
            image_data = response.content
            img = Image.open(BytesIO(image_data))
            img.thumbnail(self.max_size, Image.LANCZOS)
            self.image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.image, text="")
        except requests.exceptions.RequestException as e:
            if self.default_photo_image:
                self.image_label.config(image=self.default_photo_image, text="")
            else:
                self.image_label.config(text="Erro ao carregar", fg=COLOR_DANGER_ACCENT)
            print(f"ERRO: Falha ao carregar imagem: {e.args[0] if e.args else e}. URL: {url}")
        except Exception as e:
            if self.default_photo_image:
                self.image_label.config(image=self.default_photo_image, text="")
            else:
                self.image_label.config(text="Erro processamento", fg=COLOR_DANGER_ACCENT)
            print(f"ERRO: Falha ao processar imagem: {e}. URL: {url}")


def show_info(title, message):
    messagebox.showinfo(title, message)

def show_error(title, message):
    messagebox.showerror(title, message)

def show_warning(title, message):
    messagebox.showwarning(title, message)

def ask_yes_no(title, message):
    return messagebox.askyesno(title, message)

class AppHeaderFrame(tk.Frame):
    def __init__(self, parent, title_text, bg_color=COLOR_BACKGROUND_DARK, fg_color=COLOR_PRIMARY_ACCENT, **kwargs):
        super().__init__(parent, bg=bg_color, **kwargs)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.f1_logo_image = load_icon("f1_logo", size=(192, 48))
        if self.f1_logo_image:
            self.logo_label = tk.Label(self, image=self.f1_logo_image, bg=bg_color)
            self.logo_label.image = self.f1_logo_image
            self.logo_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        else:
            self.logo_label = tk.Label(self, text="F1", font=("Arial", 16, "bold"), bg=bg_color, fg=fg_color)
            self.logo_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.title_label = tk.Label(self, text=title_text, font=("Arial", 20, "bold"), bg=bg_color, fg=fg_color)
        self.title_label.grid(row=0, column=1, padx=15, pady=10, sticky="w")

class BaseEntityCard(tk.Frame):
    def __init__(self, parent, item_data, controller, 
                 item_id_key="id", image_url_key=None, title_key=None, detail_lines_info=None,
                 edit_view_name=None, delete_api_call=None, refresh_list_view_callback=None, 
                 # Parâmetros específicos para BaseEntityCard
                 bg_color=COLOR_BACKGROUND_MEDIUM, fg_color=COLOR_FOREGROUND_LIGHT, **kwargs_for_tk_frame): # Captura apenas kwargs para tk.Frame
        
        # Passa apenas os kwargs que tk.Frame reconhece para o construtor pai
        super().__init__(parent, bg=bg_color, relief="flat", bd=0, highlightthickness=0, **kwargs_for_tk_frame)

        self.controller = controller
        self.item_data = item_data
        self.item_id = item_data.get(item_id_key)

        # Armazenar os argumentos como atributos da instância
        self.item_id_key = item_id_key
        self.image_url_key = image_url_key
        self.title_key = title_key
        self.detail_lines_info = detail_lines_info if detail_lines_info is not None else []
        self.edit_view_name = edit_view_name
        self.delete_api_call = delete_api_call
        self.refresh_list_view_callback = refresh_list_view_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        if self.image_url_key:
            self.image_preview = ImagePreview(self, label_text="", max_size=(100, 100), bg=bg_color)
            self.image_preview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            self.image_preview.load_image_from_url(self.item_data.get(self.image_url_key, ""))

        self.details_frame = tk.Frame(self, bg=bg_color)
        self.details_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nw")

        if self.title_key:
            ttk.Label(self.details_frame, text=self.item_data.get(self.title_key, ""),
                      font=("Arial", 12, "bold"), style="CardTitle.TLabel").pack(anchor="w", pady=2)
        
        for prefix, data_key, formatter in self.detail_lines_info:
            value = self.item_data.get(data_key, 'N/A')
            display_value = formatter(value) if formatter else str(value)
            ttk.Label(self.details_frame, text=f"{prefix}{display_value}",
                      font=("Arial", 10), style="CardDetail.TLabel").pack(anchor="w")

        action_frame = tk.Frame(self, bg=bg_color)
        action_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        edit_btn = ttk.Button(action_frame, text="Editar", command=self._edit_item, style="Accent.TButton")
        edit_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        delete_btn = ttk.Button(action_frame, text="Excluir", command=self._delete_item, style="Delete.TButton")
        delete_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    def _edit_item(self):
        if self.edit_view_name:
            param_name = f"{self.edit_view_name.replace('Edit', '').replace('View', '').lower()}_id"
            self.controller.show_frame(self.edit_view_name, **{param_name: self.item_id})

    def _delete_item(self):
        if ask_yes_no("Confirmar Exclusão", f"Tem certeza que deseja excluir '{self.item_data.get(self.title_key, self.item_id)}' (ID: {self.item_id})?"):
            if self.delete_api_call:
                response = self.delete_api_call(self.item_id)
                if response is True:
                    show_info("Sucesso", "Item excluído com sucesso!")
                    if self.refresh_list_view_callback:
                        self.refresh_list_view_callback() # Chama a função de callback fornecida
                else:
                    show_error("Erro", response.get("error", "Falha ao excluir item. (Verifique o console para detalhes)"))