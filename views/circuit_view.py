import tkinter as tk
from tkinter import ttk, messagebox
import threading # Importar o módulo threading

from api_client import ApiClient
from ui_elements import LabeledEntry, ImagePreview, show_info, show_error, show_warning, ask_yes_no, \
    COLOR_PRIMARY_ACCENT, COLOR_SUCCESS_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_BUTTON_TEXT, COLOR_BACKGROUND_MEDIUM, COLOR_FOREGROUND_DARK, COLOR_BACKGROUND_LIGHT, AppHeaderFrame # Importar AppHeaderFrame

class CircuitListView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.circuits = []

        self.create_widgets()
        # REMOVIDO: A chamada inicial da API foi movida para on_show() e será assíncrona
        # self.load_circuits()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Lista de Circuitos")
        header.pack(fill="x", pady=(0, 10))

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Adicionar Novo Circuito", command=self.add_circuit, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        # O botão "Atualizar Lista" agora chamará o método que inicia o carregamento assíncrono
        ttk.Button(button_frame, text="Atualizar Lista", command=self.load_circuits, style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

        # Container para o indicador de carregamento e o Treeview
        self.content_container = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.content_container.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Indicador de Carregamento
        self.loading_label = ttk.Label(self.content_container, text="Carregando circuitos...", 
                                       background=COLOR_BACKGROUND_DARK, foreground=COLOR_FOREGROUND_LIGHT,
                                       font=("Arial", 12, "bold"))
        # O loading_label será empacotado/desempacotado dinamicamente

        # Configuração de Estilos (pode ser movida para o main.py se for global)
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=COLOR_BACKGROUND_LIGHT, foreground=COLOR_FOREGROUND_LIGHT)
        style.configure("Treeview", font=("Arial", 10), rowheight=28, background=COLOR_BACKGROUND_MEDIUM, foreground=COLOR_FOREGROUND_LIGHT, fieldbackground=COLOR_BACKGROUND_MEDIUM)
        style.map('Treeview', background=[('selected', COLOR_PRIMARY_ACCENT)], foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(self.content_container, columns=("ID", "Nome", "País", "Comprimento (km)", "URL Imagem", "URL Mapa"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("País", text="País")
        self.tree.heading("Comprimento (km)", text="Comprimento (km)")
        self.tree.heading("URL Imagem", text="URL Imagem")
        self.tree.heading("URL Mapa", text="URL Mapa")

        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Nome", width=150)
        self.tree.column("País", width=80, anchor=tk.CENTER)
        self.tree.column("Comprimento (km)", width=100, anchor=tk.CENTER)
        self.tree.column("URL Imagem", width=120)
        self.tree.column("URL Mapa", width=120)

        # O tree será empacotado/desempacotado dinamicamente
        self.tree.bind("<Double-1>", self.on_double_click)

        action_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Editar Selecionado", command=self.edit_circuit, style="Accent.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Excluir Selecionado", command=self.delete_circuit, style="Delete.TButton").pack(side=tk.LEFT, padx=10)
        
        ttk.Button(self, text="Voltar à Tela Inicial", command=lambda: self.controller.show_frame("WelcomeView"), 
                   style="Monochromatic.TButton").pack(pady=20)

    # NOVO: Método chamado pelo Controller quando esta tela é exibida
    def on_show(self, **kwargs):
        """Carrega os dados dos circuitos quando a CircuitListView é exibida."""
        self.load_circuits() # load_circuits() agora inicia uma thread

    # ATUALIZADO: Este método agora inicia o carregamento em uma thread separada
    def load_circuits(self):
        # 1. Esconde o treeview e mostra o indicador de carregamento
        self.tree.pack_forget()
        self.loading_label.pack(pady=10)
        
        # 2. Inicia a operação da API em uma nova thread
        threading.Thread(target=self._fetch_circuits_async, daemon=True).start()

    def _fetch_circuits_async(self):
        """Método para buscar os circuitos da API em uma thread separada."""
        response = self.api_client.get_circuits()
        # 3. Usa self.after para agendar a atualização da UI na thread principal do Tkinter
        self.after(0, lambda: self._handle_circuits_response(response))

    def _handle_circuits_response(self, response):
        """Método para processar a resposta da API e atualizar a UI na thread principal."""
        # 4. Esconde o indicador de carregamento
        self.loading_label.pack_forget()

        # 5. Limpa o treeview antes de popular com novos dados
        for item in self.tree.get_children():
            self.tree.delete(item)

        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar circuitos."))
        elif response is not None:
            self.circuits = response
            for circuit in self.circuits:
                self.tree.insert("", tk.END, values=(
                    circuit.get("id"),
                    circuit.get("name"),
                    circuit.get("country"),
                    circuit.get("length_km"),
                    circuit.get("image_url"),
                    circuit.get("map_url")
                ))
            # 6. Empacota o treeview de volta após carregar os dados
            self.tree.pack(fill=tk.BOTH, expand=True)
        else:
            show_error("Erro", "Resposta inesperada da API.")

    def add_circuit(self):
        self.controller.show_frame("AddCircuitView")

    def edit_circuit(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione um circuito para editar.")
            return

        circuit_id = self.tree.item(selected_item, "values")[0]
        self.controller.show_frame("EditCircuitView", circuit_id=circuit_id)

    def delete_circuit(self):
        selected_item = self.tree.focus()
        if not selected_item:
            show_warning("Nenhuma Seleção", "Por favor, selecione um circuito para excluir.")
            return

        circuit_id = self.tree.item(selected_item, "values")[0]
        if ask_yes_no("Confirmar Exclusão", f"Tem certeza que deseja excluir o circuito ID {circuit_id}?"):
            # A exclusão também pode ser feita em uma thread separada se a API for lenta
            # Mas para um DELETE simples, pode ser aceitável na thread principal por enquanto.
            response = self.api_client.delete_circuit(circuit_id)
            if response is True:
                show_info("Sucesso", "Circuito excluído com sucesso!")
                self.load_circuits() # Recarrega a lista após exclusão
            else:
                show_error("Erro", response.get("error", "Falha ao excluir circuito."))

    def on_double_click(self, event):
        self.edit_circuit()

class AddCircuitView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Adicionar Novo Circuito")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.name_entry = LabeledEntry(form_frame, "Nome:")
        self.name_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.country_entry = LabeledEntry(form_frame, "País (3 letras):")
        self.country_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.image_url_entry = LabeledEntry(form_frame, "URL da Imagem (opcional):")
        self.image_url_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.length_km_entry = LabeledEntry(form_frame, "Comprimento (km, opcional):")
        self.length_km_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.map_url_entry = LabeledEntry(form_frame, "URL do Mapa (opcional):")
        self.map_url_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar", command=self.save_circuit, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("CircuitListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    # NOVO: Método on_show para limpar campos ao exibir
    def on_show(self, **kwargs):
        """Limpa os campos do formulário quando a AddCircuitView é exibida."""
        self.name_entry.set("")
        self.country_entry.set("")
        self.image_url_entry.set("")
        self.length_km_entry.set("")
        self.map_url_entry.set("")

    def save_circuit(self):
        data = {
            "name": self.name_entry.get(),
            "country": self.country_entry.get(),
            "image_url": self.image_url_entry.get() or None,
            "length_km": self.length_km_entry.get() or None,
            "map_url": self.map_url_entry.get() or None,
        }

        if not data["name"]:
            show_warning("Erro de Entrada", "O Nome é obrigatório.")
            return
        if not data["country"]:
            show_warning("Erro de Entrada", "O País é obrigatório.")
            return
        if len(data["country"]) != 3:
            show_warning("Erro de Entrada", "O País deve ter 3 letras (ex: BRA).")
            return
        if data["length_km"]:
            try:
                data["length_km"] = float(data["length_km"])
                if data["length_km"] <= 0:
                    show_warning("Erro de Entrada", "O Comprimento (km) deve ser positivo.")
                    return
            except ValueError:
                show_warning("Erro de Entrada", "O Comprimento (km) deve ser um número.")
                return

        response = self.api_client.add_circuit(data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao adicionar circuito."))
        else:
            show_info("Sucesso", "Circuito adicionado com sucesso!")
            self.controller.show_frame("CircuitListView")

class EditCircuitView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.circuit_id = None
        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Editar Circuito")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.name_entry = LabeledEntry(form_frame, "Nome:")
        self.name_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.country_entry = LabeledEntry(form_frame, "País (3 letras):")
        self.country_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.image_url_entry = LabeledEntry(form_frame, "URL da Imagem (opcional):")
        self.image_url_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.image_url_entry.entry.bind("<FocusOut>", self.update_image_preview)

        self.image_preview = ImagePreview(form_frame, label_text="Mapa do Circuito:")
        self.image_preview.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=10)

        self.length_km_entry = LabeledEntry(form_frame, "Comprimento (km, opcional):")
        self.length_km_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        self.map_url_entry = LabeledEntry(form_frame, "URL do Mapa (opcional):")
        self.map_url_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar Alterações", command=self.save_changes, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("CircuitListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    # NOVO: Método on_show para carregar dados de edição
    def on_show(self, circuit_id=None, **kwargs):
        """Carrega os dados do circuito para edição quando a EditCircuitView é exibida."""
        if circuit_id:
            self.load_circuit_data(circuit_id)
        else:
            show_error("Erro", "ID do circuito não fornecido para edição.")
            self.controller.show_frame("CircuitListView") # Volta para a lista se não houver ID

    def load_circuit_data(self, circuit_id):
        self.circuit_id = circuit_id
        response = self.api_client.get_circuit(circuit_id)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar dados do circuito."))
            self.controller.show_frame("CircuitListView")
        elif response is not None:
            self.name_entry.set(response.get("name", ""))
            self.country_entry.set(response.get("country", "") or "")
            image_url = response.get("image_url", "") or ""
            self.image_url_entry.set(image_url)
            self.update_image_preview()

            self.length_km_entry.set(str(response.get("length_km", "") or "")) # Garante que seja string
            self.map_url_entry.set(response.get("map_url", "") or "")
        else:
            show_error("Erro", "Resposta inesperada ao carregar dados do circuito.")
            self.controller.show_frame("CircuitListView")

    def update_image_preview(self, event=None):
        url = self.image_url_entry.get()
        self.image_preview.load_image_from_url(url)

    def save_changes(self):
        data = {
            "name": self.name_entry.get(),
            "country": self.country_entry.get(),
            "image_url": self.image_url_entry.get() or None,
            "length_km": self.length_km_entry.get() or None,
            "map_url": self.map_url_entry.get() or None,
        }

        if not data["name"]:
            show_warning("Erro de Entrada", "O Nome é obrigatório.")
            return
        if not data["country"]:
            show_warning("Erro de Entrada", "O País é obrigatório.")
            return
        if len(data["country"]) != 3:
            show_warning("Erro de Entrada", "O País deve ter 3 letras (ex: BRA).")
            return
        if data["length_km"]:
            try:
                data["length_km"] = float(data["length_km"])
                if data["length_km"] <= 0:
                    show_warning("Erro de Entrada", "O Comprimento (km) deve ser positivo.")
                    return
            except ValueError:
                show_warning("Erro de Entrada", "O Comprimento (km) deve ser um número.")
                return

        response = self.api_client.update_circuit(self.circuit_id, data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao atualizar circuito."))
        else:
            show_info("Sucesso", "Circuito atualizado com sucesso!")
            self.controller.show_frame("CircuitListView")