import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import time
import json
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(__file__))
import script  # Importar o script principal

# Variável de controle para encerrar a importação
stop_flag = False
cache = set()  # Sistema de cache para evitar duplicados

class LoadingAnimation:
    def __init__(self, status_label):
        self.status_label = status_label
        self.running = False
        self.dots = 0
        
    def start(self):
        self.running = True
        self.animate()
        
    def stop(self):
        self.running = False
        
    def animate(self):
        if not self.running:
            return
            
        self.dots = (self.dots + 1) % 4
        current_text = self.status_label.cget("text").split('.')[0]
        self.status_label.config(text=f"{current_text}{'.' * self.dots}")
        self.status_label.after(500, self.animate)

# Função para carregar tweets
def load_tweets(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read().replace("window.YTD.tweets.part0 = ", "")
            tweets = json.loads(content)
        return tweets
    except Exception as e:
        return []

# Função para salvar progresso
def save_progress(file_path, completed_tweets):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(completed_tweets, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar progresso: {e}")

# Função para simular o processo de importação
def import_tweets(handle, password, file_path, status_label, progress_bar, completed_file):
    global stop_flag, cache
    stop_flag = False

    # Criar e iniciar animação de loading
    loading = LoadingAnimation(status_label)
    loading.start()

    if not handle or not password or not file_path:
        messagebox.showerror("Erro", "Preencha todos os campos corretamente!")
        return

    if not os.path.exists(file_path):
        messagebox.showerror("Erro", "O arquivo especificado não foi encontrado!")
        return

    tweets = load_tweets(file_path)
    if not tweets:
        messagebox.showerror("Erro", "Nenhum tweet encontrado no arquivo!")
        return

    # Carregar progresso salvo, se existir
    if os.path.exists(completed_file):
        with open(completed_file, encoding="utf-8") as f:
            completed_tweets = json.load(f)
    else:
        completed_tweets = []

    # Atualizar cache com tweets já completados
    cache.update([json.dumps(tweet) for tweet in completed_tweets])

    # Filtrar tweets já importados
    tweets_to_import = [tweet for tweet in tweets if json.dumps(tweet) not in cache]

    if not tweets_to_import:
        messagebox.showinfo("Info", "Todos os tweets já foram importados anteriormente!")
        return

    try:
        progress_bar["maximum"] = len(tweets_to_import)
        for i, tweet in enumerate(tweets_to_import):
            if stop_flag:  # Interrompe a importação se o botão "Encerrar" for pressionado
                loading.stop()
                save_progress(completed_file, completed_tweets)
                status_label.config(text="Importação encerrada pelo usuário.")
                return

            # Simula o tempo de postagem (substitua por chamada à função real de postagem)
            time.sleep(0.1)

            # Atualizar interface com animação
            progress = (i + 1) / len(tweets_to_import) * 100
            progress_bar["value"] = i + 1
            status_label.config(text=f"Importando... {progress:.1f}%")
            
            # Efeito visual na barra de progresso
            style.configure("Custom.Horizontal.TProgressbar",
                          background=f'#{int(40 + progress/100 * 60):02x}90e2')

            # Marca o tweet como importado
            completed_tweets.append(tweet)
            cache.add(json.dumps(tweet))  # Adicionar ao cache
            save_progress(completed_file, completed_tweets)

            root.update_idletasks()

    finally:
        loading.stop()
        save_progress(completed_file, completed_tweets)
        status_label.config(text="Importação concluída!")
        messagebox.showinfo("Sucesso", "Todos os tweets foram importados com sucesso!")

# Função para abrir o seletor de arquivos
def select_file(entry):
    file_path = filedialog.askopenfilename(
        title="Selecione o arquivo tweets.js",
        filetypes=(("Arquivos JSON", "*.js"), ("Todos os arquivos", "*.*"))
    )
    if file_path:
        entry.delete(0, tk.END)
        entry.insert(0, file_path)

# Função para iniciar a importação em uma thread separada
def start_import(handle_entry, password_entry, file_entry, status_label, progress_bar, stop_button):
    handle = handle_entry.get().strip()
    password = password_entry.get().strip()
    file_path = file_entry.get().strip()
    completed_file = "completed_tweets.json"

    # Habilita o botão de encerrar
    stop_button["state"] = "normal"

    Thread(
        target=import_tweets,
        args=(handle, password, file_path, status_label, progress_bar, completed_file),
        daemon=True
    ).start()

# Função para encerrar a importação
def stop_import(status_label):
    global stop_flag
    stop_flag = True
    status_label.config(text="Encerrando a importação...")

class ModernUI:
    def __init__(self, root):
        self.root = root
        self.handle_entry = None
        self.password_entry = None
        self.file_entry = None
        self.log_text = None
        self.setup_window()
        self.create_styles()
        self.create_widgets()
        self.import_progress = script.ImportProgress()
        self.is_importing = False
        self.current_session = None
        self.total_tweets = 0
        self.current_position = 0
        self.stop_requested = False
        self.progress_callback = None
        self.session = None
        
    def setup_window(self):
        self.root.title("Twitter to Bluesky")
        self.root.geometry("600x700")
        self.root.configure(bg='#ffffff')
        
        # Adicionar ícone da janela se disponível
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
            
        # Centralizar janela
        self.center_window()
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_styles(self):
        self.colors = {
            'primary': '#0EA5E9',     # Azul mais vibrante
            'secondary': '#F1F5F9',   # Cinza mais claro
            'text': '#0F172A',        # Texto mais escuro
            'success': '#22C55E',     # Verde success
            'error': '#EF4444',       # Vermelho error
            'warning': '#F59E0B',     # Laranja warning
            'hover': '#0284C7'        # Hover state
        }
        
        style = ttk.Style(self.root)
        style.theme_use("clam")
        
        # Configurações de estilo modernas
        style.configure("Modern.TFrame", background='#ffffff')
        style.configure("Modern.TLabel",
                       background='#ffffff',
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10))
        style.configure("Header.TLabel",
                       background='#ffffff',
                       foreground=self.colors['text'],
                       font=('Segoe UI', 24, 'bold'))
        
        # Configurar estilos do botão normal e hover
        style.configure("Modern.TButton",
                       background=self.colors['primary'],
                       foreground='white',
                       padding=(30, 15),
                       font=('Segoe UI', 10, 'bold'))
        
        style.configure("Modern.TButton.Hover",
                       background=self.colors['hover'],
                       foreground='white',
                       padding=(30, 15),
                       font=('Segoe UI', 10, 'bold'))
        
        style.map("Modern.TButton",
                 background=[('active', self.colors['hover'])])
        
        # Configurar barra de progresso moderna
        style.configure("Modern.Horizontal.TProgressbar",
                       background=self.colors['primary'],
                       troughcolor=self.colors['secondary'],
                       thickness=8)
                       
        # Adicionar estilo para área de log
        style.configure("Log.TFrame",
                       background='#ffffff',
                       relief='solid',
                       borderwidth=1)
                       
        style.configure("Log.TText",
                       background='#f8fafc',
                       foreground=self.colors['text'],
                       font=('Consolas', 9),
                       relief='flat',
                       borderwidth=0,
                       padx=10,
                       pady=10)

        # Configurar estilo base
        style.configure("Modern.TButton",
                       background=self.colors['primary'],
                       foreground='white',
                       padding=(30, 15),
                       font=('Segoe UI', 10, 'bold'))
        
        # Configurar mapeamento para hover
        style.map("Modern.TButton",
                 background=[('active', self.colors['hover']),
                           ('pressed', self.colors['hover']),
                           ('disabled', self.colors['secondary'])],
                 foreground=[('disabled', '#999999')])

    def create_ripple_effect(self, event):
        widget = event.widget
        x, y = event.x, event.y
        
        # Criar efeito de onda
        ripple = tk.Canvas(widget, width=20, height=20,
                          bg=self.colors['hover'],
                          highlightthickness=0)
        ripple.place(x=x-10, y=y-10)
        
        # Animação de expansão e fade
        for i in range(5):
            ripple.configure(width=i*10, height=i*10)
            self.root.after(50)
            ripple.update()
        
        ripple.destroy()

    def create_widgets(self):
        # Container principal
        self.main_frame = ttk.Frame(self.root, style="Modern.TFrame", padding=30)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header com animação
        self.header = ttk.Label(self.main_frame,
                              text="Twitter → Bluesky",
                              style="Header.TLabel")
        self.header.pack(pady=(0, 30))
        
        # Campos de entrada com validação
        self.input_fields = []
        fields = [
            ("Bluesky Handle", None),
            ("Password", "•"),
            ("Twitter Archive", None, "browse")
        ]
        
        for field_info in fields:
            frame = self.create_input_field(*field_info)
            frame.pack(fill=tk.X, pady=(0, 15))
            
        # Status e Progresso
        self.create_status_section()
        
        # Botões com efeitos
        self.create_action_buttons()
        
        # Adicionar área de log após a barra de progresso
        self.create_log_area()
        
        # Iniciar animações
        self.start_animations()
        
    def create_input_field(self, label, show=None, button=None):
        frame = ttk.Frame(self.main_frame, style="Modern.TFrame")
        
        ttk.Label(frame, text=label, style="Modern.TLabel").pack(anchor="w")
        
        entry = ttk.Entry(frame, font=('Segoe UI', 10), show=show)
        entry.pack(fill=tk.X, pady=(5, 0))
        
        # Atribuir campos de entrada às variáveis da classe
        if label == "Bluesky Handle":
            self.handle_entry = entry
        elif label == "Password":
            self.password_entry = entry
        elif label == "Twitter Archive":
            self.file_entry = entry
        
        if button == "browse":
            browse_btn = ttk.Button(frame, text="Browse",
                                  style="Modern.TButton",
                                  command=lambda: self.browse_file(entry))
            browse_btn.pack(pady=(5, 0))
            
        self.input_fields.append(entry)
        return frame
        
    def create_status_section(self):
        self.status_frame = ttk.Frame(self.main_frame, style="Modern.TFrame")
        self.status_frame.pack(fill=tk.X, pady=20)
        
        # Frame para status e contador
        self.info_frame = ttk.Frame(self.status_frame, style="Modern.TFrame")
        self.info_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.status_label = ttk.Label(self.info_frame,
                                    text="Ready to import",
                                    style="Modern.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        self.counter_label = ttk.Label(self.info_frame,
                                     text="0/0",
                                     font=('Segoe UI', 10, 'bold'))
        self.counter_label.pack(side=tk.RIGHT)
        
        self.progress = ttk.Progressbar(self.status_frame,
                                      style="Modern.Horizontal.TProgressbar",
                                      mode="determinate")
        self.progress.pack(fill=tk.X, pady=(5, 0))

    def update_counter(self, current, total):
        """Atualizar contador de tweets"""
        if not current or not total:
            return
            
        self.current_position = current
        self.total_tweets = total
        self.counter_label.config(text=f"{current}/{total}")
        # Atualizar também a barra de progresso
        self.progress["maximum"] = total
        self.progress["value"] = current
        self.root.update_idletasks()

    def create_action_buttons(self):
        self.button_frame = ttk.Frame(self.main_frame, style="Modern.TFrame")
        self.button_frame.pack(pady=20)
        
        self.start_button = ttk.Button(
            self.button_frame,
            text="Start Import",
            style="Modern.TButton",
            command=self.start_import
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            self.button_frame,
            text="Stop Import",
            style="Modern.TButton",
            state="disabled",
            command=self.stop_import
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

    def create_log_area(self):
        """Criar área de log estilizada"""
        log_frame = ttk.Frame(self.main_frame, style="Log.TFrame")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Área de texto com scrollbar e fonte mono
        self.log_text = tk.Text(log_frame,
                               height=20,  # Aumentar altura
                               wrap=tk.WORD,
                               font=('Consolas', 10),
                               bg='#ffffff',  # Fundo branco
                               fg='#1a1a1a',  # Texto quase preto
                               relief='flat',
                               padx=15,
                               pady=15)
        
        # Configurar tags para formatação
        self.log_text.tag_configure('timestamp', foreground='#666666')
        self.log_text.tag_configure('header', foreground='#1d4ed8', font=('Consolas', 10))
        self.log_text.tag_configure('success', foreground='#15803d')
        self.log_text.tag_configure('error', foreground='#dc2626')
        self.log_text.tag_configure('tweet', foreground='#1a1a1a')
        self.log_text.tag_configure('footer', foreground='#6b21a8')
        self.log_text.tag_configure('warning', foreground='#d97706')
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", 
                                command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.configure(state='disabled')

    def log_message(self, message, level='info'):
        """Adicionar mensagem ao log com formatação"""
        if not self.log_text:
            return
            
        self.log_text.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Ícones para diferentes tipos de mensagem
        icons = {
            'info': 'ℹ️',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️'
        }
        
        # Formatar mensagem com timestamp
        formatted_msg = f"{icons.get(level, 'ℹ️')} [{timestamp}] {message}\n"
        
        # Inserir mensagem com a tag apropriada
        self.log_text.insert(tk.END, formatted_msg, level)
        
        # Auto-scroll para última mensagem
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
        self.root.update_idletasks()

    def log_tweet(self, text, status=""):
        if not self.log_text:
            return
            
        self.log_text.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Linha separadora
        self.log_text.insert(tk.END, "\n" + "─" * 80 + "\n\n", 'separator')
        
        # Sempre mostrar o texto do tweet sendo analisado
        if text:
            self.log_text.insert(tk.END, "Analisando tweet: ", 'header')
            self.log_text.insert(tk.END, f"{text}\n\n", 'tweet')
        
        if isinstance(status, dict):
            # Se estiver apenas analisando, não mostrar mais nada
            if status.get('analyzing'):
                self.log_text.configure(state='disabled')
                return
                
            tweet_text = status.get('text', '')
            status_text = status.get('status', '')
            footer = status.get('footer', '')
            delay = status.get('delay', '')
            
            if "sucesso" in str(status_text).lower():
                self.log_text.insert(tk.END, "✅ Postado com sucesso:\n", 'success')
                self.log_text.insert(tk.END, f"{tweet_text}\n\n", 'tweet')
                if footer:
                    self.log_text.insert(tk.END, f"{footer}\n", 'footer')
                if delay:
                    self.log_text.insert(tk.END, f"⏱️ Delay: {delay:.1f}s\n", 'info')
        else:
            if "retweet" in str(status).lower():
                self.log_text.insert(tk.END, f"❌ [{timestamp}] {status}\n", 'warning')
            elif "resposta" in str(status).lower():
                self.log_text.insert(tk.END, f"❌ [{timestamp}] {status}\n", 'warning')
            elif "ignorado" in str(status).lower():
                self.log_text.insert(tk.END, f"❌ [{timestamp}] {status}\n", 'warning')
            else:
                self.log_text.insert(tk.END, f"❌ [{timestamp}] {status}\n", 'error')
        
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
        self.root.update_idletasks()

    def start_animations(self):
        def animate():
            self.progress['value'] = 0
            for i in range(101):
                if i <= 100:
                    self.progress['value'] = i
                    self.root.after(20)
            self.progress['value'] = 0
            
        self.root.after(1000, animate)
        
    def start_import(self):
        if self.is_importing:
            return
            
        handle = self.handle_entry.get().strip()
        password = self.password_entry.get().strip()
        file_path = self.file_entry.get().strip()
        
        if not all([handle, password, file_path]):
            self.log_message("Preencha todos os campos!", 'error')
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
            
        self.stop_requested = False
        
        def progress_callback(progress, success, data):
            if isinstance(data, dict):
                current = data.get('current', 0)
                total = data.get('total', 0)
                
                # Sempre atualizar contador quando disponível
                if current and total:
                    self.update_counter(current, total)
                
                text = data.get('text', '')
                status = data.get('status', '')
                error = data.get('error')
                
                if error:
                    self.log_message(error, 'error')
                elif "Analisando" in str(status):
                    self.status_label.config(
                        text=f"Analisando tweet {current} de {total}",
                        foreground=self.colors['primary']
                    )
                    self.log_tweet(text, data)
                elif success:
                    self.status_label.config(
                        text=f"Importando... {progress:.1f}%",
                        foreground=self.colors['success']
                    )
                    self.log_tweet(text, data)
                else:
                    self.log_tweet(text, data)
                    
            self.update_progress(progress)
            
        progress_callback.stop_requested = False
        self.progress_callback = progress_callback
        
        def import_thread():
            try:
                self.is_importing = True
                self.log_message("Iniciando importação...", 'info')
                
                success, message = script.resume_import(
                    handle=handle,
                    password=password,
                    tweets_path=file_path,
                    callback=progress_callback
                )
                
                if success:
                    if "pausada" in message.lower():
                        self.log_message("Importação pausada com sucesso!", 'warning')
                        self.log_message(f"Progresso salvo no tweet {self.current_position} de {self.total_tweets}", 'info')
                    else:
                        self.log_message("Importação concluída com sucesso!", 'success')
                else:
                    self.log_message(f"Erro na importação: {message}", 'error')
                    
            except Exception as e:
                self.log_message(f"Erro inesperado: {str(e)}", 'error')
            finally:
                self.is_importing = False
                self.stop_button.config(state="disabled")
                self.start_button.config(state="normal")
        
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        Thread(target=import_thread, daemon=True).start()

    def stop_import(self):
        """Parar importação de forma segura"""
        if not self.is_importing or not self.progress_callback:
            return
            
        self.progress_callback.stop_requested = True
        self.log_message("Solicitação de parada recebida, aguarde...", 'warning')
        self.status_label.config(
            text="Salvando progresso...",
            foreground=self.colors['warning']
        )

    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()

    def browse_file(self, entry):
        """Método para selecionar arquivo"""
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo tweets.js",
            filetypes=(("Arquivos JSON", "*.js"), ("Todos os arquivos", "*.*"))
        )
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernUI(root)
    root.mainloop()
