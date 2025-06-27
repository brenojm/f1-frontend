import tkinter as tk
from tkinter import ttk, messagebox, Canvas
import threading # Importar o módulo threading

from api_client import ApiClient
from ui_elements import LabeledEntry, ImagePreview, show_info, show_error, show_warning, ask_yes_no, \
    COLOR_PRIMARY_ACCENT, COLOR_SUCCESS_ACCENT, COLOR_BACKGROUND_DARK, COLOR_FOREGROUND_LIGHT, \
    COLOR_BUTTON_TEXT, COLOR_BACKGROUND_MEDIUM, COLOR_FOREGROUND_DARK, COLOR_DANGER_ACCENT, \
    AppHeaderFrame, BaseEntityCard

class TeamCard(BaseEntityCard):
    def __init__(self, parent, team_data, controller):
        detail_lines = [
            ("País Base: ", "base_country", None),
            ("Diretor: ", "principal", None),
            ("Ano Fundação: ", "founded_year", None)
        ]
        
        super().__init__(parent, item_data=team_data, controller=controller,
                         item_id_key="id",
                         image_url_key="logo_url",
                         title_key="name",
                         detail_lines_info=detail_lines,
                         edit_view_name="EditTeamView",
                         delete_api_call=lambda id: ApiClient().delete_team(id),
                         # ATUALIZADO: Chama on_show para garantir o recarregamento correto da lista após exclusão
                         refresh_list_view_callback=lambda: controller.show_frame("TeamListView") 
                        )


class TeamListView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.teams = []

        self.create_widgets()
        # REMOVIDO: A chamada inicial da API foi movida para on_show() e será assíncrona
        # self.load_teams()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Lista de Equipes")
        header.pack(fill="x", pady=(0, 10))

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Adicionar Nova Equipe", command=self.add_team, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        # O botão "Atualizar Cards" agora chamará o método que inicia o carregamento assíncrono
        ttk.Button(button_frame, text="Atualizar Cards", command=self.load_teams, style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

        ttk.Button(self, text="Voltar à Tela Inicial", command=lambda: self.controller.show_frame("WelcomeView"), 
                   style="Monochromatic.TButton").pack(pady=20)
        
        # O frame que contém o canvas e o indicador de carregamento
        self.content_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Indicador de Carregamento
        self.loading_label = ttk.Label(self.content_frame, text="Carregando equipes...", 
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
        
        # Vincula eventos de roda do mouse para rolagem
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel) # Windows e macOS
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)   # Linux (scroll up)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)   # Linux (scroll down)
        
    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0: # Scroll para cima
            self.canvas.yview_scroll(-1, "unit")
        elif event.num == 5 or event.delta < 0: # Scroll para baixo
            self.canvas.yview_scroll(1, "unit")

    # NOVO: Método chamado pelo Controller quando esta tela é exibida
    def on_show(self, **kwargs):
        """Carrega os dados das equipes quando a TeamListView é exibida."""
        self.load_teams() # load_teams() agora inicia uma thread

    # ATUALIZADO: Este método agora inicia o carregamento em uma thread separada
    def load_teams(self):
        # 1. Esconde o conteúdo atual (canvas + scrollbar) e mostra o indicador
        self.canvas.pack_forget()
        self.scrollbar.pack_forget()
        self.loading_label.pack(pady=10)
        
        # 2. Inicia a operação da API em uma nova thread
        threading.Thread(target=self._fetch_teams_async, daemon=True).start()

    def _fetch_teams_async(self):
        """Método para buscar as equipes da API em uma thread separada."""
        response = self.api_client.get_teams()
        # 3. Usa self.after para agendar a atualização da UI na thread principal do Tkinter
        self.after(0, lambda: self._handle_teams_response(response))

    def _handle_teams_response(self, response):
        """Método para processar a resposta da API e atualizar a UI na thread principal."""
        # 4. Esconde o indicador de carregamento
        self.loading_label.pack_forget()

        # 5. Limpa os cards existentes antes de criar novos
        for widget in self.cards_container.winfo_children():
            widget.destroy()

        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar equipes."))
        elif response is not None:
            self.teams = response
            
            current_row_frame = None
            cards_in_current_row = 0
            max_cols = 4 

            card_width = 280
            card_height = 220
            padding_x = 15
            padding_y = 15
            
            for team in self.teams:
                if cards_in_current_row == 0:
                    current_row_frame = tk.Frame(self.cards_container, bg=COLOR_BACKGROUND_DARK)
                    current_row_frame.pack(pady=padding_y, anchor="center") 

                card = TeamCard(current_row_frame, team, self.controller)
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

    def add_team(self):
        self.controller.show_frame("AddTeamView")

    # Métodos edit_team e delete_team não estão definidos no contexto, mantidos como pass se não forem usados
    def edit_team(self):
        pass

    def delete_team(self):
        pass

    def on_double_click(self, event):
        pass


class AddTeamView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Adicionar Nova Equipe")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.name_entry = LabeledEntry(form_frame, "Nome:")
        self.name_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        self.logo_url_entry = LabeledEntry(form_frame, "URL do Logo (opcional):")
        self.logo_url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.logo_url_entry.entry.bind("<FocusOut>", self.update_image_preview)

        self.image_preview = ImagePreview(form_frame, label_text="Pré-visualização do Logo:")
        self.image_preview.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=10)


        self.base_country_entry = LabeledEntry(form_frame, "País Base (3 letras):")
        self.base_country_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

        self.principal_entry = LabeledEntry(form_frame, "Diretor (opcional):")
        self.principal_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)

        self.founded_year_entry = LabeledEntry(form_frame, "Ano de Fundação (opcional):")
        self.founded_year_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar", command=self.save_team, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("TeamListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    # NOVO: Método on_show para limpar campos ao exibir
    def on_show(self, **kwargs):
        """Limpa os campos do formulário quando a AddTeamView é exibida."""
        self.name_entry.set("")
        self.logo_url_entry.set("")
        self.image_preview.load_image_from_url("") # Limpa a pré-visualização da imagem
        self.base_country_entry.set("")
        self.principal_entry.set("")
        self.founded_year_entry.set("")

    def update_image_preview(self, event=None):
        url = self.logo_url_entry.get()
        self.image_preview.load_image_from_url(url)

    def save_team(self):
        data = {
            "name": self.name_entry.get(),
            "logo_url": self.logo_url_entry.get() or None,
            "base_country": self.base_country_entry.get() or None,
            "principal": self.principal_entry.get() or None,
            "founded_year": self.founded_year_entry.get() or None,
        }

        if not data["name"]:
            show_warning("Erro de Entrada", "O Nome é obrigatório.")
            return
        if data["base_country"] and len(data["base_country"]) != 3:
            show_warning("Erro de Entrada", "O País Base deve ter 3 letras (ex: BRA).")
            return
        if data["founded_year"]:
            try:
                data["founded_year"] = int(data["founded_year"])
                # ATUALIZADO: Usar o ano atual dinamicamente
                current_year = 2025 # Ou importar datetime e usar datetime.now().year
                if not (1950 <= data["founded_year"] <= current_year):
                    show_warning("Erro de Entrada", f"O Ano de Fundação deve estar entre 1950 e o ano atual ({current_year}).")
                    return
            except ValueError:
                show_warning("Erro de Entrada", "O Ano de Fundação deve ser um número inteiro.")
                return

        response = self.api_client.add_team(data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao adicionar equipe."))
        else:
            show_info("Sucesso", "Equipe adicionada com sucesso!")
            self.controller.show_frame("TeamListView")

class EditTeamView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BACKGROUND_DARK)
        self.controller = controller
        self.api_client = ApiClient()
        self.team_id = None
        self.create_widgets()

    def create_widgets(self):
        header = AppHeaderFrame(self, title_text="Editar Equipe")
        header.pack(fill="x", pady=(0, 10))

        form_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        form_frame.pack(pady=10, padx=20, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        self.name_entry = LabeledEntry(form_frame, "Nome:")
        self.name_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        self.logo_url_entry = LabeledEntry(form_frame, "URL do Logo (opcional):")
        self.logo_url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.logo_url_entry.entry.bind("<FocusOut>", self.update_image_preview)

        self.image_preview = ImagePreview(form_frame, label_text="Pré-visualização do Logo:")
        self.image_preview.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=10)

        self.base_country_entry = LabeledEntry(form_frame, "País Base (3 letras):")
        self.base_country_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

        self.principal_entry = LabeledEntry(form_frame, "Diretor (opcional):")
        self.principal_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)

        self.founded_year_entry = LabeledEntry(form_frame, "Ano de Fundação (opcional):")
        self.founded_year_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND_DARK)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Salvar Alterações", command=self.save_changes, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=lambda: self.controller.show_frame("TeamListView"), style="Monochromatic.TButton").pack(side=tk.LEFT, padx=10)

    # NOVO: Método on_show para carregar dados de edição
    def on_show(self, team_id=None, **kwargs):
        """Carrega os dados da equipe para edição quando a EditTeamView é exibida."""
        if team_id:
            self.load_team_data(team_id)
        else:
            show_error("Erro", "ID da equipe não fornecido para edição.")
            self.controller.show_frame("TeamListView") # Volta para a lista se não houver ID

    def load_team_data(self, team_id):
        self.team_id = team_id
        response = self.api_client.get_team(team_id)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao carregar dados da equipe."))
            self.controller.show_frame("TeamListView")
        elif response is not None:
            self.name_entry.set(response.get("name", ""))
            logo_url = response.get("logo_url", "") or ""
            self.logo_url_entry.set(logo_url)
            self.update_image_preview()

            self.base_country_entry.set(response.get("base_country", "") or "")
            self.principal_entry.set(response.get("principal", "") or "")
            self.founded_year_entry.set(str(response.get("founded_year", "")) or "") # Converte para string
        else:
            show_error("Erro", "Resposta inesperada ao carregar dados da equipe.")
            self.controller.show_frame("TeamListView")

    def update_image_preview(self, event=None):
        url = self.logo_url_entry.get()
        self.image_preview.load_image_from_url(url)

    def save_changes(self):
        data = {
            "name": self.name_entry.get(),
            "logo_url": self.logo_url_entry.get() or None,
            "base_country": self.base_country_entry.get() or None,
            "principal": self.principal_entry.get() or None,
            "founded_year": self.founded_year_entry.get() or None,
        }

        if not data["name"]:
            show_warning("Erro de Entrada", "O Nome é obrigatório.")
            return
        if data["base_country"] and len(data["base_country"]) != 3:
            show_warning("Erro de Entrada", "O País Base deve ter 3 letras (ex: BRA).")
            return
        if data["founded_year"]:
            try:
                data["founded_year"] = int(data["founded_year"])
                # ATUALIZADO: Usar o ano atual dinamicamente
                current_year = 2025 # Ou importar datetime e usar datetime.now().year
                if not (1950 <= data["founded_year"] <= current_year):
                    show_warning("Erro de Entrada", f"O Ano de Fundação deve estar entre 1950 e o ano atual ({current_year}).")
                    return
            except ValueError:
                show_warning("Erro de Entrada", "O Ano de Fundação deve ser um número inteiro.")
                return

        response = self.api_client.update_team(self.team_id, data)
        if isinstance(response, dict) and "error" in response:
            show_error("Erro", response.get("error", "Falha ao atualizar equipe."))
        else:
            show_info("Sucesso", "Equipe atualizada com sucesso!")
            self.controller.show_frame("TeamListView")