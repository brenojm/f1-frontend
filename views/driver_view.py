import tkinter as tk
from tkinter import ttk, messagebox, Canvas
import threading # Importar o módulo threading

from api_client import ApiClient
from ui_elements import LabeledEntry, ImagePreview, show_info, show_error, show_warning, ask_yes_no, \
    COLOR_PRIMARY_ACCENT, COLOR_SUCCESS_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_BUTTON_TEXT, COLOR_BACKGROUND_MEDIUM, COLOR_FOREGROUND_DARK, COLOR_DANGER_ACCENT, \
    format_date_display, format_date_api, AppHeaderFrame, BaseEntityCard

class DriverCard(BaseEntityCard):
    def __init__(self, parent, driver_data, controller):
        detail_lines = [
            ("Nacionalidade: ", "nationality", None),
            ("Nascimento: ", "date_of_birth", format_date_display)
        ]
        
        super().__init__(parent, item_data=driver_data, controller=controller,
                         item_id_key="id",
                         image_url_key="image_url",
                         title_key="full_name",
                         detail_lines_info=detail_lines,
                         edit_view_name="EditDriverView",
                         delete_api_call=lambda id: ApiClient().delete_driver(id),
                         # Garante que a lista seja recarregada após exclusão
                         refresh_list_view_callback=lambda: controller.show_frame("DriverListView") 
                        )

class DriverListView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.drivers = []

        self.create_widgets()
        # A chamada inicial da API foi movida para on_show() e será assíncrona
        # self.load_drivers() 

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Pilotos de Fórmula 1")
        header.pack(fill="x", pady=(0, 10))

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Adicionar Novo Piloto", command=self.add_driver, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Atualizar Cards", command=self.load_drivers, style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)
        
        ttk.Button(self, text="Voltar à Tela Inicial", command=lambda: self.controller.show_frame("WelcomeView"), 
                   style="Monochromatic.TButton").pack(pady=20)
        
        # O frame que contém o canvas e o indicador de carregamento
        self.content_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Indicador de Carregamento
        self.loading_label = ttk.Label(self.content_frame, text="Carregando pilotos...", 
                                       background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT,
                                       font=("Arial", 12, "bold"))
        # Ele será empacotado/desempacotado dinamicamente

        # Estrutura do Canvas e Scrollbar
        self.canvas = tk.Canvas(self.content_frame, bg=COLOR_BACKGROUND_DARK, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # self.canvas e self.scrollbar serão empacotados/desempacotados dinamicamente

        self.cards_container = tk.Frame(self.canvas, bg=COLOR_BACKGROUND_DARK)
        self.canvas.create_window((0, 0), window=self.cards_container, anchor="nw", tags="self.cards_container")

        self.cards_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Bindings do mousewheel permanecem no canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel) # Windows e macOS
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)   # Linux (scroll up)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)   # Linux (scroll down)

    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0: # Scroll para cima
            self.canvas.yview_scroll(-1, "unit")
        elif event.num == 5 or event.delta < 0: # Scroll para baixo
            self.canvas.yview_scroll(1, "unit")

    def on_show(self, **kwargs):
        """Carrega os dados dos pilotos quando a DriverListView é exibida."""
        self.load_drivers() # Agora, load_drivers() inicia uma thread

    def load_drivers(self):
        # 1. Esconde o conteúdo atual (canvas + scrollbar) e mostra o indicador
        self.canvas.pack_forget()
        self.scrollbar.pack_forget()
        self.loading_label.pack(pady=10)
        
        # 2. Inicia a operação da API em uma nova thread
        threading.Thread(target=self._fetch_drivers_async, daemon=True).start()

    def _fetch_drivers_async(self):
        """Método para buscar os pilotos da API em uma thread separada."""
        response = self.api_client.get_drivers()
        # 3. Usa self.after para agendar a atualização da UI na thread principal do Tkinter
        self.after(0, lambda: self._handle_drivers_response(response))

    def _handle_drivers_response(self, response):
        """Método para processar a resposta da API e atualizar a UI na thread principal."""
        # 4. Esconde o indicador de carregamento
        self.loading_label.pack_forget()

        # 5. Limpa os cards existentes antes de criar novos
        for widget in self.cards_container.winfo_children():
            widget.destroy()

        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar pilotos."))
        elif response is not None:
            self.drivers = response
            
            current_row_frame = None
            cards_in_current_row = 0
            max_cols = 4 

            card_width = 280 
            card_height = 220 
            padding_x = 15 
            padding_y = 15 
            
            for driver in self.drivers:
                if cards_in_current_row == 0: 
                    current_row_frame = tk.Frame(self.cards_container, bg=COLOR_BACKGROUND_DARK)
                    current_row_frame.pack(pady=padding_y, anchor="center") 

                card = DriverCard(current_row_frame, driver, self.controller) 
                card.grid_propagate(False)
                card.config(width=card_width, height=card_height)

                card.pack(side=tk.LEFT, padx=padding_x, pady=0) 
                
                cards_in_current_row += 1
                if cards_in_current_row >= max_cols:
                    cards_in_current_row = 0 
            
            # 6. Atualiza o canvas e mostra o scrollbar se necessário
            self.canvas.update_idletasks() # Força a atualização do layout para obter dimensões corretas
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            # Empacota o canvas de volta
            self.canvas.pack(side="left", fill="both", expand=True) 

            # Verifica se a altura do conteúdo excede a altura do canvas para mostrar/esconder a scrollbar
            if self.canvas.bbox("all") and self.canvas.bbox("all")[3] > self.canvas.winfo_height():
                self.scrollbar.pack(side="right", fill="y")
                self.canvas.yview_moveto(0) # Volta para o topo ao recarregar a lista
            else:
                self.scrollbar.pack_forget()
            
        else:
            show_error("Erro", "Resposta inesperada da API.")

    def add_driver(self):
        self.controller.show_frame("AddDriverView")


# As classes AddDriverView e EditDriverView permanecem as mesmas que na última atualização.
# Elas não exigem mudanças relacionadas ao scroll ou threading direto para a API de lista.

class AddDriverView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Adicionar Novo Piloto")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.full_name_entry = LabeledEntry(form_frame, "Nome Completo:")
        self.full_name_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.nationality_entry = LabeledEntry(form_frame, "Nacionalidade (3 letras):")
        self.nationality_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.dob_entry = LabeledEntry(form_frame, "Data de Nascimento (DD/MM/AAAA):")
        self.dob_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.image_url_entry = LabeledEntry(form_frame, "URL da Imagem (opcional):")
        self.image_url_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar", command=self.save_driver, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("DriverListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    def on_show(self, **kwargs):
        self.full_name_entry.set("")
        self.nationality_entry.set("")
        self.dob_entry.set("")
        self.image_url_entry.set("")

    def save_driver(self):
        dob_input = self.dob_entry.get()
        dob_api_format = format_date_api(dob_input)

        data = {
            "full_name": self.full_name_entry.get(),
            "nationality": self.nationality_entry.get() or None,
            "date_of_birth": dob_api_format,
            "image_url": self.image_url_entry.get() or None,
        }

        if not data["full_name"]:
            show_warning("Erro de Entrada", "O Nome Completo é obrigatório.")
            return
        if data["nationality"] and len(data["nationality"]) != 3:
            show_warning("Erro de Entrada", "A Nacionalidade deve ter 3 letras (ex: BRA).")
            return
        if dob_input and dob_api_format is None: 
            show_warning("Erro de Entrada", "A Data de Nascimento deve estar no formato DD/MM/AAAA.")
            return

        response = self.api_client.add_driver(data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao adicionar piloto."))
        else:
            show_info("Sucesso", "Piloto adicionado com sucesso!")
            self.controller.show_frame("DriverListView")


class EditDriverView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.driver_id = None
        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Editar Piloto")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.full_name_entry = LabeledEntry(form_frame, "Nome Completo:")
        self.full_name_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.nationality_entry = LabeledEntry(form_frame, "Nacionalidade (3 letras):")
        self.nationality_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.dob_entry = LabeledEntry(form_frame, "Data de Nascimento (DD/MM/AAAA):")
        self.dob_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.image_url_entry = LabeledEntry(form_frame, "URL da Imagem (opcional):")
        self.image_url_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.image_url_entry.entry.bind("<FocusOut>", self.update_image_preview)

        self.image_preview = ImagePreview(form_frame, label_text="Foto do Piloto:")
        self.image_preview.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=10)


        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar Alterações", command=self.save_changes, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("DriverListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    def on_show(self, driver_id=None, **kwargs):
        if driver_id:
            self.load_driver_data(driver_id)
        else:
            show_error("Erro", "ID do piloto não fornecido para edição.")
            self.controller.show_frame("DriverListView")

    def load_driver_data(self, driver_id):
        self.driver_id = driver_id
        driver = self.api_client.get_driver(driver_id)
        if isinstance(driver, dict) and "error" in driver:
            show_error("Erro", driver.get("error", "Falha ao carregar dados do piloto."))
            self.controller.show_frame("DriverListView")
        elif driver:
            self.full_name_entry.set(driver.get("full_name", ""))
            self.nationality_entry.set(driver.get("nationality", "") or "")
            
            dob_display_format = format_date_display(driver.get("date_of_birth", ""))
            self.dob_entry.set(dob_display_format)
            
            image_url = driver.get("image_url", "") or ""
            self.image_url_entry.set(image_url)
            self.update_image_preview()
        else:
            show_error("Erro", "Resposta inesperada ao carregar dados do piloto.")
            self.controller.show_frame("DriverListView")

    def update_image_preview(self, event=None):
        url = self.image_url_entry.get()
        self.image_preview.load_image_from_url(url)

    def save_changes(self):
        dob_input = self.dob_entry.get()
        dob_api_format = format_date_api(dob_input)

        data = {
            "full_name": self.full_name_entry.get(),
            "nationality": self.nationality_entry.get() or None,
            "date_of_birth": dob_api_format,
            "image_url": self.image_url_entry.get() or None,
        }

        if not data["full_name"]:
            show_warning("Erro de Entrada", "O Nome Completo é obrigatório.")
            return
        if data["nationality"] and len(data["nationality"]) != 3:
            show_warning("Erro de Entrada", "A Nacionalidade deve ter 3 letras (ex: BRA).")
            return
        if dob_input and dob_api_format is None: 
            show_warning("Erro de Entrada", "A Data de Nascimento deve estar no formato DD/MM/AAAA.")
            return

        response = self.api_client.update_driver(self.driver_id, data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao atualizar piloto."))
        else:
            show_info("Sucesso", "Piloto atualizado com sucesso!")
            self.controller.show_frame("DriverListView")