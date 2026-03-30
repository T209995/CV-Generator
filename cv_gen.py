import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
import webbrowser

class ResumeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Générateur de CV")
        self.root.geometry("850x900")
        
        # Style
        self.style = ttk.Style()
        self.style.configure("TNotebook.Tab", padding=[15, 5], font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#2980b9")
        
        # Stockage des données
        self.experiences = []
        self.projets = []

        self.setup_ui()

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=15, pady=10)

        # Onglet 1: Coordonnées
        self.tab_info = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_info, text="1. Coordonnées")
        self.setup_info_tab()

        # Onglet 2: Expériences
        self.tab_exp = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_exp, text="2. Expériences")
        self.setup_exp_tab()

        # Onglet 3: Compétences & Autres
        self.tab_misc = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_misc, text="3. Compétences & Divers")
        self.setup_misc_tab()

        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill="x")
        
        ttk.Separator(bottom_frame, orient="horizontal").pack(fill="x", pady=5)
        self.btn_gen = ttk.Button(bottom_frame, text="🚀 GÉNÉRER MON CV (HTML)", command=self.generate)
        self.btn_gen.pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="Quitter", command=self.root.quit).pack(side="right")

    def setup_info_tab(self):
        container = ttk.Frame(self.tab_info, padding="25")
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Informations Générales", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        fields = [
            ("Nom Complet *", "nom"), ("Email *", "email"), ("Téléphone *", "phone"),
            ("Adresse ", "adresse"), ("Lien LinkedIn", "linkedin"), ("Lien GitHub", "github"),
            ("Diplôme Principal *", "edu")
        ]

        self.info_vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(container, text=label).grid(row=i+1, column=0, sticky="w", pady=5)
            var = tk.StringVar()
            ttk.Entry(container, textvariable=var, width=55).grid(row=i+1, column=1, sticky="w", padx=15)
            self.info_vars[key] = var

        ttk.Label(container, text="Résumé / Accroche").grid(row=9, column=0, sticky="nw", pady=15)
        self.resume_text = tk.Text(container, height=8, width=41, font=("Segoe UI", 10), padx=5, pady=5)
        self.resume_text.grid(row=9, column=1, sticky="w", padx=15, pady=15)

    def setup_exp_tab(self):
        container = ttk.Frame(self.tab_exp, padding="20")
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Parcours Professionnel", style="Header.TLabel").pack(anchor="w", pady=(0, 10))
        
        list_container = ttk.LabelFrame(container, text=" Vos Expériences ", padding=10)
        list_container.pack(fill="both", expand=True)

        self.canvas_exp = tk.Canvas(list_container, highlightthickness=0)
        self.scrollbar_exp = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas_exp.yview)
        self.exp_list_frame = ttk.Frame(self.canvas_exp)

        self.exp_list_frame.bind("<Configure>", lambda e: self.canvas_exp.configure(scrollregion=self.canvas_exp.bbox("all")))
        self.canvas_exp.create_window((0, 0), window=self.exp_list_frame, anchor="nw")
        self.canvas_exp.configure(yscrollcommand=self.scrollbar_exp.set)
        self.canvas_exp.pack(side="left", fill="both", expand=True)
        self.scrollbar_exp.pack(side="right", fill="y")

        ttk.Button(container, text="+ Ajouter une expérience", command=self.add_exp_dialog).pack(pady=15)

    def add_exp_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Détails de l'expérience")
        dialog.geometry("500x650")
        dialog.grab_set()
        
        main_f = ttk.Frame(dialog, padding=25)
        main_f.pack(fill="both", expand=True)

        ttk.Label(main_f, text="Poste occupé * :").pack(anchor="w")
        titre = ttk.Entry(main_f, width=50); titre.pack(fill="x", pady=5)
        ttk.Label(main_f, text="Entreprise * :").pack(anchor="w")
        ent = ttk.Entry(main_f, width=50); ent.pack(fill="x", pady=5)
        ttk.Label(main_f, text="Dates :").pack(anchor="w")
        dates = ttk.Entry(main_f, width=50); dates.pack(fill="x", pady=5)
        ttk.Label(main_f, text="Missions (une par ligne) :").pack(anchor="w", pady=(10, 0))
        miss = tk.Text(main_f, height=12, width=45, font=("Segoe UI", 10)); miss.pack(fill="both", expand=True, pady=5)

        def save():
            m_list = [l.strip() for l in miss.get("1.0", "end").split("\n") if l.strip()]
            if titre.get().strip() and ent.get().strip():
                self.experiences.append({'titre': titre.get().strip(), 'entreprise': ent.get().strip(), 'dates': dates.get().strip(), 'missions': m_list})
                self.refresh_exp_list(); dialog.destroy()
            else: messagebox.showwarning("Incomplet", "Poste et entreprise requis.")

        ttk.Button(main_f, text="Valider", command=save).pack(pady=15)

    def refresh_exp_list(self):
        for widget in self.exp_list_frame.winfo_children(): widget.destroy()
        if not self.experiences:
            ttk.Label(self.exp_list_frame, text="Aucune expérience ajoutée.", font=("Arial", 9, "italic")).pack(pady=20)
            return
        for i, exp in enumerate(self.experiences):
            f = ttk.Frame(self.exp_list_frame, padding=5); f.pack(fill="x", expand=True)
            ttk.Label(f, text=f"• {exp['titre']} @ {exp['entreprise']}", font=("Segoe UI", 10)).pack(side="left", padx=5)
            ttk.Button(f, text="Supprimer", width=12, command=lambda idx=i: self.remove_exp(idx)).pack(side="right")
            ttk.Separator(self.exp_list_frame, orient="horizontal").pack(fill="x", pady=2)

    def remove_exp(self, idx):
        if messagebox.askyesno("Confirmation", "Supprimer cette expérience ?"):
            self.experiences.pop(idx); self.refresh_exp_list()

    def setup_misc_tab(self):
        container = ttk.Frame(self.tab_misc, padding="25")
        container.pack(fill="both", expand=True)

        # Compétences Techniques (Hard Skills)
        ttk.Label(container, text="Compétences Techniques (Hard Skills)", style="Header.TLabel").pack(anchor="w")
        ttk.Label(container, text="Logiciels, langages, outils (ex: Python, Excel, SQL)", font=("Arial", 8)).pack(anchor="w")
        self.hard_skills_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.hard_skills_var, width=85).pack(pady=(5, 15))

        # Compétences Générales (Soft Skills)
        ttk.Label(container, text="Compétences Générales (Soft Skills)", style="Header.TLabel").pack(anchor="w")
        ttk.Label(container, text="Qualités humaines (ex: Autonomie, Travail d'équipe, Rigueur)", font=("Arial", 8)).pack(anchor="w")
        self.soft_skills_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.soft_skills_var, width=85).pack(pady=(5, 15))

        # Langues & Intérêts
        grid_f = ttk.Frame(container); grid_f.pack(fill="x", pady=10)
        ttk.Label(grid_f, text="Langues :", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.lang_var = tk.StringVar(); ttk.Entry(grid_f, textvariable=self.lang_var, width=40).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        ttk.Label(grid_f, text="Intérêts :", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w")
        self.interest_var = tk.StringVar(); ttk.Entry(grid_f, textvariable=self.interest_var, width=40).grid(row=1, column=1, sticky="w", padx=10, pady=5)

        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=20)
        ttk.Label(container, text="Projets & Portfolios", style="Header.TLabel").pack(anchor="w")
        self.proj_list_frame = ttk.Frame(container); self.proj_list_frame.pack(fill="both", expand=True, pady=5)
        ttk.Button(container, text="+ Ajouter un projet", command=self.add_proj_dialog).pack(pady=5)

    def add_proj_dialog(self):
        dialog = tk.Toplevel(self.root); dialog.title("Détails du projet"); dialog.geometry("400x250"); dialog.grab_set()
        f = ttk.Frame(dialog, padding=20); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Nom du projet :").pack(anchor="w")
        name = ttk.Entry(f, width=40); name.pack(pady=5)
        ttk.Label(f, text="Description courte :").pack(anchor="w")
        desc = ttk.Entry(f, width=40); desc.pack(pady=5)
        def save():
            if name.get().strip():
                self.projets.append({'titre': name.get().strip(), 'desc': desc.get().strip()})
                self.refresh_proj_list(); dialog.destroy()
        ttk.Button(f, text="Ajouter", command=save).pack(pady=15)

    def refresh_proj_list(self):
        for widget in self.proj_list_frame.winfo_children(): widget.destroy()
        for i, p in enumerate(self.projets):
            f = ttk.Frame(self.proj_list_frame); f.pack(fill="x", pady=2)
            ttk.Label(f, text=f"📂 {p['titre']} - {p['desc']}", font=("Arial", 9)).pack(side="left")
            ttk.Button(f, text="X", width=3, command=lambda idx=i: self.remove_proj(idx)).pack(side="right")

    def remove_proj(self, idx):
        self.projets.pop(idx); self.refresh_proj_list()

    def generate(self):
        nom = self.info_vars['nom'].get().strip()
        email = self.info_vars['email'].get().strip()
        if not nom or "@" not in email:
            messagebox.showerror("Champs requis", "Nom et Email valide requis."); return

        data = {
            'nom': nom, 'email': email, 'phone': self.info_vars['phone'].get().strip(),
            'adresse': self.info_vars['adresse'].get().strip(), 'linkedin': self.info_vars['linkedin'].get().strip(),
            'github': self.info_vars['github'].get().strip(), 'education': self.info_vars['edu'].get().strip(),
            'resume': self.resume_text.get("1.0", "end-1c").strip(), 'experiences': self.experiences,
            'projets': self.projets, 'hard_skills': self.hard_skills_var.get().split(','),
            'soft_skills': self.soft_skills_var.get().split(','), 'langues': self.lang_var.get().split(','),
            'interets': self.interest_var.get().split(',')
        }

        html_content = self.create_html_template(data)
        file_path = filedialog.asksaveasfilename(initialfile=f"CV_{nom.replace(' ', '_')}.html", defaultextension=".html", filetypes=[("HTML", "*.html")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f: f.write(html_content)
            if messagebox.askyesno("Succès", "CV généré ! Ouvrir le fichier ?"): webbrowser.open(f"file://{file_path}")

    def create_html_template(self, data):
        links = []
        if data['linkedin']: links.append(f'<a href="{data["linkedin"]}" target="_blank">LinkedIn</a>')
        if data['github']: links.append(f'<a href="{data["github"]}" target="_blank">GitHub</a>')
        links_str = (" | " + " | ".join(links)) if links else ""

        exp_html = ""
        for exp in data['experiences']:
            m_li = "".join([f"<li>{m}</li>" for m in exp['missions']])
            exp_html += f"<div class='item'><div class='upper-row'><h3 class='job-title'>{exp['titre']}</h3><span class='time'>{exp['dates']}</span></div><div class='company'>{exp['entreprise']}</div><ul>{m_li}</ul></div>"

        def get_badges(items, color_class="tag"):
            return "".join([f'<span class="{color_class}">{i.strip()}</span>' for i in items if i.strip()])

        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <style>
                :root {{ --main-blue: #2c3e50; --accent-blue: #3498db; --soft-gray: #7f8c8d; }}
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.5; color: #333; max-width: 850px; margin: 40px auto; padding: 0 20px; background: #f4f7f6; }}
                .cv-container {{ background: #fff; padding: 50px; border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1); border-top: 12px solid var(--main-blue); }}
                header {{ border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 25px; }}
                h1 {{ margin: 0; color: var(--main-blue); font-size: 2.8em; }}
                .contacts {{ color: var(--soft-gray); font-size: 0.9em; margin-top: 8px; }}
                .contacts a {{ color: var(--accent-blue); text-decoration: none; font-weight: 500; }}
                h2 {{ color: var(--accent-blue); border-bottom: 1px solid #d6eaf8; padding-bottom: 5px; margin-top: 35px; text-transform: uppercase; font-size: 1em; letter-spacing: 1px; }}
                .item {{ margin-bottom: 20px; }}
                .upper-row {{ display: flex; justify-content: space-between; align-items: baseline; }}
                .job-title {{ margin: 0; color: #333; font-size: 1.2em; }}
                .time {{ color: #95a5a6; font-size: 0.85em; font-weight: 600; }}
                .company {{ color: var(--accent-blue); font-weight: 700; }}
                ul {{ margin-top: 8px; padding-left: 20px; color: #444; }}
                .tag {{ display: inline-block; background: #ebf5fb; color: #2c3e50; padding: 5px 12px; border-radius: 4px; margin: 3px; font-size: 0.85em; font-weight: 600; border: 1px solid #d6eaf8; }}
                .tag-soft {{ display: inline-block; background: #f4f7f6; color: #7f8c8d; padding: 5px 12px; border-radius: 4px; margin: 3px; font-size: 0.85em; font-weight: 600; border: 1px solid #eee; }}
                .profile {{ background: #fdfdfd; padding: 15px; border-left: 5px solid var(--accent-blue); font-style: italic; color: #555; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="cv-container">
                <header>
                    <h1>{data['nom']}</h1>
                    <div class="contacts">{data['email']} | {data['phone']} | {data['adresse']}{links_str}</div>
                </header>
                {f'<div class="profile">{data["resume"].replace(chr(10), "<br>")}</div>' if data['resume'] else ''}
                <h2>Formation</h2><div class="item"><strong>{data['education']}</strong></div>
                {f'<h2>Parcours Professionnel</h2>{exp_html}' if data['experiences'] else ''}
                {f'<h2>Projets</h2><div>{get_badges([p["titre"] for p in data["projets"]])}</div>' if data['projets'] else ''}
                <h2>Compétences Techniques</h2><div>{get_badges(data['hard_skills'])}</div>
                {f'<h2>Compétences Générales</h2><div>{get_badges(data["soft_skills"], "tag-soft")}</div>' if data['soft_skills'][0].strip() else ''}
                {f'<h2>Langues</h2><div>{get_badges(data["langues"])}</div>' if data['langues'][0].strip() else ''}
                {f'<h2>Centres d intérêt</h2><div>{get_badges(data["interets"], "tag-soft")}</div>' if data['interets'][0].strip() else ''}
            </div>
        </body>
        </html>"""

if __name__ == "__main__":
    root = tk.Tk()
    app = ResumeApp(root)
    root.mainloop()
