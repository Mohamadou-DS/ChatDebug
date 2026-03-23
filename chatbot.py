from tkinter.filedialog import Open
import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image, ImageDraw
import time
from datetime import datetime
import random
import google.generativeai as genai
import json
import os
from tkinter import messagebox
import requests

# Configuration de CustomTkinter
ctk.set_appearance_mode("dark")  # Thème sombre par défaut
ctk.set_default_color_theme("blue")  # Thème de couleur bleu

# Palette de couleurs
COLORS = {
    "blue_light": "#636AF2",
    "blue_dark": "#666CD9",
    "orange_light": "#F25C05",
    "orange_dark": "#F24607",
    "gray_light": "#F2F2F2",
}

# Chemin du fichier de sauvegarde des discussions
SAVE_FILE = "discussions.json"

def make_circular_image(image_path, size):
    """Convertir une image en forme circulaire."""
    image = Image.open(image_path).resize(size, Image.Resampling.LANCZOS)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, *size), fill=255)
    result = Image.new("RGBA", size)
    result.paste(image, (0, 0), mask)
    return result

class ChatbotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatbot de Débogage")
        self.root.geometry("1200x800")
        self.root.configure(fg_color=COLORS["gray_light"])
        self.root.state("zoomed")  # Mode plein écran avec barre de titre

        self.is_dark_theme = False  # False = thème clair, True = thème sombre
        self.discussions = self.load_discussions()
        self.show_startup_animation()

    def show_startup_animation(self):
        """Afficher l'animation de démarrage."""
        self.startup_frame = ctk.CTkFrame(self.root, fg_color=COLORS["gray_light"])
        self.startup_frame.pack(fill="both", expand=True)

        self.logo_image = make_circular_image("logo.jpeg", (90, 90))
        self.logo_photo = CTkImage(self.logo_image, size=(90, 90))
        self.logo_label = ctk.CTkLabel(self.startup_frame, image=self.logo_photo, text="")
        self.logo_label.pack(pady=(100, 20))

        self.welcome_label = ctk.CTkLabel(
            self.startup_frame, text="Bienvenue dans votre chatbot de débogage, un instant...",
            font=("Segoe UI", 18), text_color=COLORS["blue_dark"]
        )
        self.welcome_label.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.startup_frame, orientation="horizontal", width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        self.root.after(200, self.update_progress)

    def update_progress(self):
        """Mettre à jour la barre de progression."""
        current_value = self.progress_bar.get()
        if current_value < 1:
            self.progress_bar.set(current_value + 0.025)
            self.root.after(200, self.update_progress)
        else:
            self.startup_frame.destroy()
            self.setup_main_interface()

    def setup_main_interface(self):
        """Configurer l'interface principale après l'animation de démarrage."""
        self.sidebar = ctk.CTkFrame(self.root, fg_color=COLORS["blue_dark"], width=200)
        self.sidebar.pack(side="left", fill="y")

        self.logo_image = make_circular_image("logo.jpeg", (90, 90))
        self.logo_photo = CTkImage(self.logo_image, size=(90, 90))
        self.logo_label = ctk.CTkLabel(self.sidebar, image=self.logo_photo, text="")
        self.logo_label.pack(pady=(20, 10))

        button_options = {
            "font": ("Segoe UI", 14),
            "fg_color": "transparent",
            "anchor": "w",
            "cursor": "hand2",
        }

        self.home_button = ctk.CTkButton(self.sidebar, text="Home", **button_options, command=lambda: self.update_main_content("home"))
        self.home_button.pack(fill="x", pady=5, padx=20)

        self.discussions_button = ctk.CTkButton(
            self.sidebar, text="Discutions", **button_options, command=lambda: self.update_main_content("discussions")
        )
        self.discussions_button.pack(fill="x", pady=5, padx=20)

        self.theme_button = ctk.CTkButton(self.sidebar, text="Thème Sombre" if not self.is_dark_theme else "Thème Claire", **button_options, command=self.toggle_theme)
        self.theme_button.pack(fill="x", pady=5, padx=20)

        self.poweroff_button = ctk.CTkButton(self.sidebar, text="PowerOff", **button_options, command=self.confirm_shutdown)
        self.poweroff_button.pack(side="bottom", fill="x", pady=(10, 20), padx=20)

        self.main_container = ctk.CTkFrame(self.root, fg_color=COLORS["gray_light"])
        self.main_container.pack(side="right", fill="both", expand=True)

        self.header = ctk.CTkFrame(self.main_container, fg_color=COLORS["gray_light"], height=80)
        self.header.pack(fill="x")

        self.new_chat_button = ctk.CTkButton(
            self.header, text="+ Nouvelle discussion", font=("Segoe UI", 14),
            fg_color=COLORS["blue_light"], hover_color=COLORS["orange_light"],
            command=self.open_new_discussion
        )
        self.new_chat_button.pack(side="right", padx=20, pady=20)

        self.time_date_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS["gray_light"])
        self.time_date_frame.pack(fill="x", pady=10)

        self.time_label = ctk.CTkLabel(self.time_date_frame, text="", font=("Segoe UI", 16), text_color=COLORS["orange_light"])
        self.time_label.pack(side="left", padx=10)

        self.date_label = ctk.CTkLabel(self.time_date_frame, text="", font=("Segoe UI", 12), text_color=COLORS["orange_light"])
        self.date_label.pack(side="left", padx=10)

        self.update_time_date()

        self.main_content = ctk.CTkFrame(self.main_container, fg_color=COLORS["gray_light"])
        self.main_content.pack(fill="both", expand=True, padx=20, pady=20)

        self.update_main_content("home")

    def update_time_date(self):
        """Mettre à jour l'heure et la date."""
        now = datetime.now()
        self.time_label.configure(text=now.strftime("%H:%M:%S"))
        self.date_label.configure(text=now.strftime("%d/%m/%Y"))
        self.root.after(1000, self.update_time_date)

    def toggle_theme(self):
        """Basculer entre les thèmes clair et sombre."""
        if self.is_dark_theme:
            # Passer au thème clair
            self.main_container.configure(fg_color=COLORS["gray_light"])
            self.header.configure(fg_color=COLORS["gray_light"])
            self.time_date_frame.configure(fg_color=COLORS["gray_light"])
            self.main_content.configure(fg_color=COLORS["gray_light"])
            self.theme_button.configure(text="Thème Sombre")
            if hasattr(self, "message_label") and self.message_label.winfo_exists():
                self.message_label.configure(text_color=COLORS["orange_light"])
        else:
            # Passer au thème sombre
            self.main_container.configure(fg_color="#2E2E2E")
            self.header.configure(fg_color="#2E2E2E")
            self.time_date_frame.configure(fg_color="#2E2E2E")
            self.main_content.configure(fg_color="#2E2E2E")
            self.theme_button.configure(text="Thème Claire")
            if hasattr(self, "message_label") and self.message_label.winfo_exists():
                self.message_label.configure(text_color=COLORS["blue_light"])

        # Inverser l'état du thème
        self.is_dark_theme = not self.is_dark_theme

    def update_main_content(self, content):
        """Mettre à jour le contenu du conteneur principal."""
        for widget in self.main_content.winfo_children():
            widget.destroy()

        if content == "home":
            self.show_home_page()
        elif content == "discussions":
            self.show_discussions_list()

    def show_home_page(self):
        """Afficher la page d'accueil."""
        for widget in self.main_content.winfo_children():
            widget.destroy()  # Effacer tous les widgets dans main_content

        # Ajouter le titre "Home" en haut à gauche
        title_label = ctk.CTkLabel(self.main_content, text="Home", font=("Segoe UI", 20), text_color=COLORS["blue_dark"])
        title_label.pack(side="top", anchor="nw", padx=20, pady=10)

        # Afficher le logo
        self.main_logo_image = Image.open("logo.jpeg").resize((300, 300), Image.Resampling.LANCZOS)
        self.main_logo_photo = CTkImage(self.main_logo_image, size=(300, 300))
        self.main_logo_label = ctk.CTkLabel(self.main_content, image=self.main_logo_photo, text="")
        self.main_logo_label.pack(pady=20)

        # Afficher un message aléatoire
        self.message_label = ctk.CTkLabel(self.main_content, text="", font=("Segoe UI", 18), text_color=COLORS["blue_dark"])
        self.message_label.pack(pady=10)
        self.show_random_message()

    def show_random_message(self):
        """Afficher un message aléatoire caractère par caractère."""
        if hasattr(self, "message_label") and self.message_label.winfo_exists():
            messages = [
                "ChatDebug, votre assistant de débogage.",
                "Analyser et déboguer votre code.",
                "Trouver des explications de vos erreurs avec des solutions proposées.",
            ]
            self.current_message = random.choice(messages)
            self.message_index = 0
            self.message_label.configure(text="")
            self.root.after(100, self.display_next_character)

    def display_next_character(self):
        """Afficher le prochain caractère du message."""
        if hasattr(self, "message_label") and self.message_label.winfo_exists():
            if self.message_index < len(self.current_message):
                self.message_label.configure(text=self.message_label.cget("text") + self.current_message[self.message_index])
                self.message_index += 1
                self.root.after(100, self.display_next_character)
            else:
                self.root.after(3000, self.erase_message)

    def erase_message(self):
        """Effacer le message caractère par caractère."""
        if hasattr(self, "message_label") and self.message_label.winfo_exists():
            current_text = self.message_label.cget("text")
            if current_text:
                self.message_label.configure(text=current_text[:-1])
                self.root.after(100, self.erase_message)
            else:
                self.root.after(1000, self.show_random_message)

    def show_discussions_list(self):
        """Afficher la liste des discussions ou un message si aucune discussion n'existe."""
        for widget in self.main_content.winfo_children():
            widget.destroy()  # Effacer tous les widgets dans main_content

        # Ajouter le titre "Discussions" en haut à gauche
        title_label = ctk.CTkLabel(self.main_content, text="Discussions", font=("Segoe UI", 20), text_color=COLORS["blue_dark"])
        title_label.pack(side="top", anchor="nw", padx=20, pady=10)

        if not self.discussions:
            # Afficher une image et un message si aucune discussion n'existe
            no_discussions_image = CTkImage(Image.open("no_discussions.jpeg"), size=(200, 200))
            no_discussions_label = ctk.CTkLabel(self.main_content, image=no_discussions_image, text="")
            no_discussions_label.pack(pady=20)

            no_discussions_text = ctk.CTkLabel(
                self.main_content,
                text="Pas encore de discussions, cliquez sur [+ Nouvelle discussion] pour commencer à discuter.",
                font=("Segoe UI", 16),
                text_color=COLORS["blue_dark"]
            )
            no_discussions_text.pack(pady=10)
        else:
            # Afficher la liste des discussions
            for discussion in self.discussions:
                discussion_frame = ctk.CTkFrame(
                    self.main_content, fg_color=COLORS["gray_light"], border_width=1, border_color=COLORS["blue_light"]
                )
                discussion_frame.pack(fill="x", pady=5, padx=10)

                # Effet de survol
                discussion_frame.bind("<Enter>", lambda e, f=discussion_frame: f.configure(border_color=COLORS["orange_light"]))
                discussion_frame.bind("<Leave>", lambda e, f=discussion_frame: f.configure(border_color=COLORS["blue_light"]))
                discussion_frame.bind("<Button-1>", lambda e, d=discussion: self.read_discussion(d))

                # Titre de la discussion
                title_label = ctk.CTkLabel(discussion_frame, text=discussion["title"], font=("Segoe UI", 14), text_color=COLORS["blue_dark"])
                title_label.pack(side="left", padx=10)

                # Bouton de suppression
                delete_button = ctk.CTkButton(
                    discussion_frame, text="Supprimer", font=("Segoe UI", 12), fg_color=COLORS["orange_light"],
                    hover_color=COLORS["orange_dark"], command=lambda d=discussion: self.delete_discussion(d)
                )
                delete_button.pack(side="right", padx=5)

    def read_discussion(self, discussion):
        """Afficher le contenu d'une discussion."""
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # Titre de la discussion
        title_label = ctk.CTkLabel(self.main_content, text=discussion["title"], font=("Segoe UI", 18), text_color=COLORS["blue_dark"])
        title_label.pack(pady=10)

        # Zone de messages scrollable
        self.chat_frame = ctk.CTkScrollableFrame(self.main_content, fg_color=COLORS["gray_light"])
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Afficher les messages existants sans animation
        for message in discussion["messages"]:
            self.display_message(message["role"], message["content"], animate=False)

        # Zone d'entrée et bouton d'envoi
        self.input_frame = ctk.CTkFrame(self.main_content, fg_color=COLORS["gray_light"])
        self.input_frame.pack(fill="x", pady=10)

        self.user_input = ctk.CTkEntry(self.input_frame, font=("Segoe UI", 14), placeholder_text="Entrez votre message...")
        self.user_input.pack(side="left", fill="x", expand=True, padx=10)

        self.send_button = ctk.CTkButton(
            self.input_frame, text="Envoyer", font=("Segoe UI", 14), fg_color=COLORS["blue_light"], hover_color=COLORS["orange_light"],
            command=lambda: self.send_message(discussion)
        )
        self.send_button.pack(side="right", padx=10)

    def display_message(self, role, content, animate=False):
        """Afficher un message avec une bordure adaptée et des symboles."""
        frame = ctk.CTkFrame(
            self.chat_frame, fg_color=COLORS["gray_light"], border_width=1,
            border_color=COLORS["blue_light" if role == "user" else "orange_light"], width=400
        )
        frame.pack(fill="x", pady=5)

        # Ajouter un symbole > ou < selon le rôle
        symbol = ">" if role == "user" else "<"
        symbol_label = ctk.CTkLabel(
            frame, text=symbol, font=("Segoe UI", 14), text_color=COLORS["blue_light" if role == "user" else "orange_light"]
        )
        symbol_label.pack(side="right" if role == "user" else "left", padx=5)

        # Afficher le message
        message_label = ctk.CTkLabel(
            frame, text="", font=("Segoe UI", 14), text_color=COLORS["blue_dark" if role == "user" else "orange_dark"],
            justify="left", wraplength=800
        )
        message_label.pack(side="right" if role == "user" else "left", fill="x", padx=5, pady=5)

        # Appliquer l'animation uniquement si c'est une nouvelle réponse du chatbot
        if role == "assistant" and animate:
            self.display_message_character_by_character(message_label, content)
            # Bouton de copie
            copy_button = ctk.CTkButton(
                frame, text="📋", font=("Segoe UI", 15), fg_color="transparent", hover_color=COLORS["orange_light"],
                width=50, command=lambda: self.copy_to_clipboard(content)
            )
            copy_button.pack(side="right", padx=5)
        else:
            # Afficher le message directement sans animation
            message_label.configure(text=content)

    def display_message_character_by_character(self, label, content):
        """Afficher un message caractère par caractère."""
        if not hasattr(self, "message_char_index"):
            self.message_char_index = 0

        # Check if the label widget still exists
        if not label.winfo_exists():
            return  # Stop if the widget is destroyed

        if self.message_char_index < len(content):
            label.configure(text=label.cget("text") + content[self.message_char_index])
            self.message_char_index += 1
            self.root.after(25, lambda: self.display_message_character_by_character(label, content))
        else:
            self.message_char_index = 0  # Réinitialiser pour le prochain message

    def copy_to_clipboard(self, text):
        """Copier le texte dans le presse-papiers."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.show_notification("Réponse copiée dans le presse-papiers !")

    def show_notification(self, message):
        """Afficher une notification en haut de l'interface."""
        # Créer un cadre pour la notification
        self.notification_frame = ctk.CTkFrame(
            self.header, fg_color=COLORS["orange_light"], border_width=2, border_color=COLORS["orange_dark"], width=200, height=150
        )
        self.notification_frame.pack(side="right", fill="x", pady=10, padx=10)  # Position en haut

        # Ajouter un label pour le message
        notification_label = ctk.CTkLabel(
            self.notification_frame, text=message, font=("Segoe UI", 14), text_color=COLORS["gray_light"]
        )
        notification_label.pack(pady=10, padx=10)

        # Fermer la notification après 3 secondes
        self.root.after(3000, self.close_notification)

    def close_notification(self):
        """Fermer la notification."""
        if hasattr(self, "notification_frame") and self.notification_frame.winfo_exists():
            self.notification_frame.destroy()

    def send_message(self, discussion=None):
        """Envoyer un message et mettre à jour la discussion."""
        message = self.user_input.get()
        if message.strip():
            if discussion is None:
                # Créer une nouvelle discussion
                new_discussion = {
                    "id": len(self.discussions) + 1,
                    "title": f"Discussion {len(self.discussions) + 1}",
                    "messages": []
                }
                self.discussions.append(new_discussion)
                discussion = new_discussion

            # Ajouter le message de l'utilisateur
            discussion["messages"].append({"role": "user", "content": message})
            self.display_message("user", message, animate=False)  # Pas d'animation pour l'utilisateur

            # Obtenir la réponse du chatbot
            response = self.get_chatbot_response(message)
            discussion["messages"].append({"role": "assistant", "content": response})
            self.display_message("assistant", response, animate=True)  # Animation pour le chatbot

            # Sauvegarder les discussions
            self.save_discussions()

            # Effacer l'entrée utilisateur
            self.user_input.delete(0, "end")

    def get_chatbot_response(self, message):
        """Obtenir une réponse du chatbot avec Gemini API"""
        try:
            # Configuration de l'API Gemini
            genai.configure(api_key="#####")
            
            # Création du modèle
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Préparation du prompt
            prompt = f"""Tu es un expert en débogage de code. Analyse les erreurs et propose des solutions claires en français.
            
            Message de l'utilisateur : {message}"""
            
            # Génération de la réponse
            response = model.generate_content(prompt)
            
            # Récupération de la réponse
            if response.text:
                return response.text.strip()
            else:
                return "Aucune réponse générée"

        except Exception as e:
            # Gestion générique avec encodage forcé UTF-8
            error_msg = f"Erreur inattendue : {str(e)}"
            return error_msg.encode('utf-8', errors='replace').decode('utf-8')

    def show_confirmation(self, title, message, callback):
        """Afficher une boîte de dialogue de confirmation au milieu du conteneur."""
        # Créer un cadre pour la confirmation
        self.confirmation_frame = ctk.CTkFrame(
            self.main_content, fg_color=COLORS["gray_light"], border_width=2, border_color=COLORS["blue_light"], width=210
        )
        # Centrer le cadre dans le conteneur
        self.confirmation_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Afficher le message de confirmation
        confirmation_label = ctk.CTkLabel(
            self.confirmation_frame, text=message, font=("Segoe UI", 14), text_color=COLORS["blue_dark"]
        )
        confirmation_label.pack(pady=10, padx=10)

        # Boutons Oui/Non
        buttons_frame = ctk.CTkFrame(self.confirmation_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)

        yes_button = ctk.CTkButton(
            buttons_frame,
            text="Oui",
            font=("Segoe UI", 14),
            fg_color=COLORS["blue_light"],
            hover_color=COLORS["orange_light"],
            command=lambda: self.on_confirmation(True, callback)
        )
        yes_button.pack(side="left", padx=10)

        no_button = ctk.CTkButton(
            buttons_frame,
            text="Non",
            font=("Segoe UI", 14),
            fg_color=COLORS["blue_light"],
            hover_color=COLORS["orange_light"],
            command=lambda: self.on_confirmation(False, callback)
        )
        no_button.pack(side="right", padx=10)

    def on_confirmation(self, result, callback):
        """Gérer la réponse de l'utilisateur."""
        if hasattr(self, "confirmation_frame") and self.confirmation_frame.winfo_exists():
            self.confirmation_frame.destroy()
        callback(result)  # Appeler le callback avec le résultat

    def delete_discussion(self, discussion):
        """Supprimer une discussion après confirmation."""
        def on_confirm(result):
            if result:
                # Supprimer la discussion de la liste
                self.discussions = [d for d in self.discussions if d["id"] != discussion["id"]]
                self.save_discussions()  # Sauvegarder les discussions mises à jour

                # Réinitialiser main_content et afficher à nouveau la liste des discussions
                for widget in self.main_content.winfo_children():
                    widget.destroy()  # Effacer tous les widgets dans main_content
                self.show_discussions_list()  # Afficher la liste des discussions

                # Afficher une notification de confirmation
                self.show_notification("La discussion a été supprimée.")

        # Afficher la boîte de dialogue de confirmation
        self.show_confirmation("Confirmation", "Êtes-vous sûr de vouloir supprimer cette discussion ?", on_confirm)

    def confirm_shutdown(self):
        """Confirmer la fermeture de l'application."""
        def on_confirm(result):
            if result:
                self.shutdown_animation()

        self.show_confirmation("Confirmation", "Êtes-vous sûr de vouloir quitter ?", on_confirm)

    def shutdown_animation(self):
        """Afficher l'animation de fermeture."""
        for widget in self.main_content.winfo_children():
            widget.destroy()

        self.main_logo_image = Image.open("logo.jpeg").resize((300, 300), Image.Resampling.LANCZOS)
        self.main_logo_photo = CTkImage(self.main_logo_image, size=(300, 300))
        self.main_logo_label = ctk.CTkLabel(self.main_content, image=self.main_logo_photo, text="")
        self.main_logo_label.pack(pady=20)

        shutdown_label = ctk.CTkLabel(
            self.main_content, text="Fermeture en cours, à bientot...", font=("Segoe UI", 18), text_color=COLORS["orange_light"]
        )
        shutdown_label.pack(pady=20)

        self.progress_bar = ctk.CTkProgressBar(self.main_content, orientation="horizontal", width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        self.root.after(100, self.update_shutdown_progress)

    def update_shutdown_progress(self):
        """Mettre à jour la barre de progression de fermeture."""
        current_value = self.progress_bar.get()
        if current_value < 1:
            self.progress_bar.set(current_value + 0.05)
            self.root.after(100, self.update_shutdown_progress)
        else:
            self.root.destroy()

    def load_discussions(self):
        """Charger les discussions depuis le fichier."""
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        return []

    def save_discussions(self):
        """Sauvegarder les discussions dans le fichier."""
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(self.discussions, file, ensure_ascii=False, indent=4)

    def open_new_discussion(self):
        """Ouvrir une nouvelle discussion."""
        for widget in self.main_content.winfo_children():
            widget.destroy()

        welcome_label = ctk.CTkLabel(
            self.main_content,
            text="Salut, je suis votre assistant de débogage. Comment puis-je vous aider aujourd'hui ?",
            font=("Segoe UI", 18),
            text_color=COLORS["blue_dark"]
        )
        welcome_label.pack(pady=20)

        self.chat_frame = ctk.CTkScrollableFrame(self.main_content, fg_color=COLORS["gray_light"])
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.input_frame = ctk.CTkFrame(self.main_content, fg_color=COLORS["gray_light"])
        self.input_frame.pack(fill="x", pady=10)

        self.user_input = ctk.CTkEntry(
            self.input_frame,
            font=("Segoe UI", 14),
            placeholder_text="Entrez votre erreur ou code..."
        )
        self.user_input.pack(side="left", fill="x", expand=True, padx=10)

        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Envoyer",
            font=("Segoe UI", 14),
            fg_color=COLORS["blue_light"],
            hover_color=COLORS["orange_light"],
            command=lambda: self.send_message()
        )
        self.send_button.pack(side="right", padx=10)

if __name__ == "__main__":
    root = ctk.CTk()
    chatbot_ui = ChatbotUI(root)
    root.mainloop()
