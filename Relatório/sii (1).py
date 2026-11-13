"""
SISTEMA INTEGRADO DE INFORMACAO (SII) - PROJETO ACADEMICO
Aplicacao demonstrativa em Python, Tkinter e SQLite.
Use apenas dados ficticios. Nao utilizar para atendimento clinico real.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, hashlib, secrets
from datetime import datetime

DB_NAME = "sii_provincial.db"

def conectar():
    con = sqlite3.connect(DB_NAME)
    con.execute("PRAGMA foreign_keys = ON")
    return con

def hash_senha(senha, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 120000).hex()
    return salt, digest

def verificar_senha(senha, salt, digest):
    return hash_senha(senha, salt)[1] == digest

def inicializar_bd():
    with conectar() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS unidades(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, tipo TEXT NOT NULL, municipio TEXT NOT NULL,
            contacto TEXT
        );
        CREATE TABLE IF NOT EXISTS utilizadores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, username TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL, senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL, unidade_id INTEGER,
            ativo INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(unidade_id) REFERENCES unidades(id)
        );
        CREATE TABLE IF NOT EXISTS pacientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL, nome TEXT NOT NULL,
            nascimento TEXT, sexo TEXT, telefone TEXT,
            municipio TEXT, unidade_origem INTEGER,
            criado_em TEXT NOT NULL,
            FOREIGN KEY(unidade_origem) REFERENCES unidades(id)
        );
        CREATE TABLE IF NOT EXISTS registos_clinicos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL, unidade_id INTEGER NOT NULL,
            data TEXT NOT NULL, tipo TEXT NOT NULL,
            descricao TEXT NOT NULL, profissional TEXT,
            FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
            FOREIGN KEY(unidade_id) REFERENCES unidades(id)
        );
        CREATE TABLE IF NOT EXISTS encaminhamentos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL, origem_id INTEGER NOT NULL,
            destino_id INTEGER NOT NULL, data TEXT NOT NULL,
            motivo TEXT NOT NULL, estado TEXT NOT NULL DEFAULT 'Pendente',
            FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
            FOREIGN KEY(origem_id) REFERENCES unidades(id),
            FOREIGN KEY(destino_id) REFERENCES unidades(id)
        );
        CREATE TABLE IF NOT EXISTS auditoria(
            id INTEGER PRIMARY KEY AUTOINCREMENT, utilizador TEXT,
            acao TEXT, data TEXT
        );
        """)
        if con.execute("SELECT COUNT(*) FROM unidades").fetchone()[0] == 0:
            con.executemany("INSERT INTO unidades(nome,tipo,municipio,contacto) VALUES(?,?,?,?)", [
                ("Hospital Provincial do Uíge","Hospital","Uíge","000 000 000"),
                ("Centro de Saúde do Negage","Centro de Saúde","Negage","000 000 001"),
                ("Posto de Saúde do Songo","Posto de Saúde","Songo","000 000 002")])
        if con.execute("SELECT COUNT(*) FROM utilizadores").fetchone()[0] == 0:
            unidade = con.execute("SELECT id FROM unidades ORDER BY id LIMIT 1").fetchone()[0]
            salt, digest = hash_senha("Admin@123")
            con.execute("""INSERT INTO utilizadores(nome,username,salt,senha_hash,perfil,unidade_id)
                           VALUES(?,?,?,?,?,?)""",
                        ("Administrador do Sistema","admin",salt,digest,"Administrador",unidade))

class SIIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SII - Sistema Integrado de Informação | Saúde do Uíge")
        self.root.geometry("1120x720")
        self.root.minsize(960, 620)
        self.user = None
        self.style = ttk.Style()
        try: self.style.theme_use("clam")
        except tk.TclError: pass
        self.style.configure("Title.TLabel", font=("Segoe UI", 19, "bold"), foreground="#123b5d")
        self.style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.login()

    def registar_acao(self, acao):
        with conectar() as con:
            con.execute("INSERT INTO auditoria(utilizador,acao,data) VALUES(?,?,?)",
                        (self.user["username"], acao, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    def limpar(self):
        for w in self.root.winfo_children(): w.destroy()

    def login(self):
        self.limpar()
        frame = ttk.Frame(self.root, padding=35)
        frame.place(relx=.5, rely=.5, anchor="center")
        ttk.Label(frame, text="SISTEMA INTEGRADO DE INFORMAÇÃO", style="Title.TLabel").pack(pady=(0,8))
        ttk.Label(frame, text="Direção Provincial da Saúde do Uíge").pack(pady=(0,25))
        ttk.Label(frame, text="Utilizador").pack(anchor="w")
        username = ttk.Entry(frame, width=38); username.pack(pady=(3,12))
        ttk.Label(frame, text="Palavra-passe").pack(anchor="w")
        password = ttk.Entry(frame, width=38, show="*"); password.pack(pady=(3,18))
        def entrar(event=None):
            with conectar() as con:
                row = con.execute("""SELECT id,nome,username,salt,senha_hash,perfil,unidade_id
                                     FROM utilizadores WHERE username=? AND ativo=1""",
                                  (username.get().strip(),)).fetchone()
            if row and verificar_senha(password.get(), row[3], row[4]):
                self.user = dict(id=row[0], nome=row[1], username=row[2], perfil=row[5], unidade_id=row[6])
                self.registar_acao("Iniciou sessão")
                self.dashboard()
            else: messagebox.showerror("Acesso não autorizado", "Credenciais incorretas ou conta inativa.")
        ttk.Button(frame, text="Entrar", command=entrar).pack(fill="x")
        password.bind("<Return>", entrar)
        ttk.Label(frame, text="Demonstração académica • Utilize dados fictícios", foreground="#666").pack(pady=18)
        ttk.Label(frame, text="Acesso inicial: admin  |  Palavra-passe: Admin@123").pack()

    def dashboard(self):
        self.limpar()
        top = ttk.Frame(self.root, padding=15); top.pack(fill="x")
        ttk.Label(top, text="SII — Saúde do Uíge", style="Title.TLabel").pack(side="left")
        ttk.Label(top, text=f"{self.user['nome']} • {self.user['perfil']}").pack(side="right")
        body = ttk.Frame(self.root, padding=15); body.pack(fill="both", expand=True)
        nav = ttk.Frame(body); nav.pack(side="left", fill="y", padx=(0,18))
        area = ttk.Frame(body); area.pack(side="left", fill="both", expand=True)
        self.area = area
        buttons = [
            ("Painel geral", self.painel),
            ("Pacientes", self.pacientes),
            ("Histórico clínico", self.historico),
            ("Encaminhamentos", self.encaminhamentos),
            ("Unidades sanitárias", self.unidades),
            ("Relatórios", self.relatorios)]
        if self.user["perfil"] == "Administrador":
            buttons.append(("Utilizadores", self.utilizadores))
        for label, fn in buttons:
            ttk.Button(nav, text=label, command=fn, width=22).pack(fill="x", pady=4)
        ttk.Separator(nav).pack(fill="x", pady=12)
        ttk.Button(nav, text="Terminar sessão", command=self.logout).pack(fill="x")
        self.painel()

    def limpar_area(self):
        for w in self.area.winfo_children(): w.destroy()

    def titulo(self, texto):
        ttk.Label(self.area, text=texto, style="Title.TLabel").pack(anchor="w", pady=(0,14))

    def painel(self):
        self.limpar_area(); self.titulo("Painel geral")
        with conectar() as con:
            p = con.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]
            u = con.execute("SELECT COUNT(*) FROM unidades").fetchone()[0]
            r = con.execute("SELECT COUNT(*) FROM registos_clinicos").fetchone()[0]
            e = con.execute("SELECT COUNT(*) FROM encaminhamentos WHERE estado='Pendente'").fetchone()[0]
        cards = ttk.Frame(self.area); cards.pack(fill="x", pady=10)
        for label, value in [("Pacientes",p),("Unidades",u),("Registos clínicos",r),("Encaminhamentos pendentes",e)]:
            box=ttk.LabelFrame(cards,text=label,padding=18); box.pack(side="left",fill="x",expand=True,padx=5)
            ttk.Label(box,text=str(value),font=("Segoe UI",22,"bold")).pack()
        ttk.Label(self.area,text="Plataforma demonstrativa para partilha autorizada de informação entre unidades sanitárias.",
                  wraplength=750).pack(anchor="w",pady=25)

    def tabela(self, parent, cols, headings):
        frame=ttk.Frame(parent); frame.pack(fill="both",expand=True,pady=8)
        tree=ttk.Treeview(frame,columns=cols,show="headings")
        for c,h in zip(cols,headings):
            tree.heading(c,text=h); tree.column(c,width=130,anchor="w")
        sy=ttk.Scrollbar(frame,orient="vertical",command=tree.yview); tree.configure(yscrollcommand=sy.set)
        tree.pack(side="left",fill="both",expand=True); sy.pack(side="right",fill="y")
        return tree

    def pacientes(self):
        self.limpar_area(); self.titulo("Gestão e partilha de pacientes")
        bar=ttk.Frame(self.area); bar.pack(fill="x")
        search=ttk.Entry(bar,width=35); search.pack(side="left",padx=(0,6))
        tree=self.tabela(self.area,("codigo","nome","sexo","municipio","origem"),("Código","Nome","Sexo","Município","Unidade de origem"))
        def carregar():
            for x in tree.get_children(): tree.delete(x)
            termo=f"%{search.get().strip()}%"
            with conectar() as con:
                rows=con.execute("""SELECT p.codigo,p.nome,p.sexo,p.municipio,COALESCE(u.nome,'-')
                    FROM pacientes p LEFT JOIN unidades u ON u.id=p.unidade_origem
                    WHERE p.nome LIKE ? OR p.codigo LIKE ? ORDER BY p.nome""",(termo,termo)).fetchall()
            for row in rows: tree.insert("","end",values=row)
        ttk.Button(bar,text="Pesquisar",command=carregar).pack(side="left")
        ttk.Button(bar,text="Novo paciente",command=self.novo_paciente).pack(side="right")
        carregar()

    def novo_paciente(self):
        win=tk.Toplevel(self.root); win.title("Registar paciente"); win.geometry("430x470"); win.transient(self.root)
        fields={}
        labels=["Nome completo","Data de nascimento (AAAA-MM-DD)","Sexo","Telefone","Município"]
        for label in labels:
            ttk.Label(win,text=label).pack(anchor="w",padx=18,pady=(10,0))
            ent=ttk.Entry(win,width=45); ent.pack(padx=18); fields[label]=ent
        fields["Sexo"].insert(0,"Não indicado")
        def guardar():
            nome=fields["Nome completo"].get().strip()
            if not nome: messagebox.showwarning("Validação","O nome é obrigatório."); return
            codigo="SII-"+secrets.token_hex(4).upper()
            with conectar() as con:
                con.execute("""INSERT INTO pacientes(codigo,nome,nascimento,sexo,telefone,municipio,unidade_origem,criado_em)
                    VALUES(?,?,?,?,?,?,?,?)""",(codigo,nome,fields[labels[1]].get().strip(),fields["Sexo"].get().strip(),
                    fields["Telefone"].get().strip(),fields["Município"].get().strip(),self.user["unidade_id"],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.registar_acao("Registou paciente "+codigo); win.destroy(); self.pacientes()
            messagebox.showinfo("Sucesso",f"Paciente registado. Código: {codigo}")
        ttk.Button(win,text="Guardar paciente",command=guardar).pack(pady=18)

    def obter_paciente(self, parent):
        with conectar() as con: rows=con.execute("SELECT id,codigo,nome FROM pacientes ORDER BY nome").fetchall()
        if not rows: messagebox.showinfo("Informação","Registe primeiro um paciente."); return None
        return rows

    def historico(self):
        self.limpar_area(); self.titulo("Histórico clínico partilhado")
        rows=self.obter_paciente(self.area)
        if not rows: return
        choices=[f"{r[1]} — {r[2]}" for r in rows]
        combo=ttk.Combobox(self.area,values=choices,state="readonly",width=60); combo.pack(anchor="w")
        combo.current(0)
        tree=self.tabela(self.area,("data","unidade","tipo","descricao","profissional"),("Data","Unidade","Tipo","Descrição","Profissional"))
        def carregar():
            pid=rows[combo.current()][0]
            for x in tree.get_children(): tree.delete(x)
            with conectar() as con:
                data=con.execute("""SELECT rc.data,u.nome,rc.tipo,rc.descricao,COALESCE(rc.profissional,'')
                    FROM registos_clinicos rc JOIN unidades u ON u.id=rc.unidade_id
                    WHERE rc.paciente_id=? ORDER BY rc.data DESC""",(pid,)).fetchall()
            for x in data: tree.insert("","end",values=x)
        def adicionar():
            pid=rows[combo.current()][0]
            win=tk.Toplevel(self.root); win.title("Adicionar registo clínico"); win.geometry("430x350")
            inputs={}
            for label in ["Tipo (Consulta/Exame/Tratamento)","Descrição","Profissional"]:
                ttk.Label(win,text=label).pack(anchor="w",padx=15,pady=(10,0))
                ent=ttk.Entry(win,width=48); ent.pack(padx=15); inputs[label]=ent
            def save():
                desc=inputs["Descrição"].get().strip()
                if not desc: messagebox.showwarning("Validação","A descrição é obrigatória."); return
                with conectar() as con:
                    con.execute("""INSERT INTO registos_clinicos(paciente_id,unidade_id,data,tipo,descricao,profissional)
                        VALUES(?,?,?,?,?,?)""",(pid,self.user["unidade_id"],datetime.now().strftime("%Y-%m-%d %H:%M"),
                        inputs["Tipo (Consulta/Exame/Tratamento)"].get().strip() or "Consulta",desc,
                        inputs["Profissional"].get().strip()))
                self.registar_acao("Adicionou registo clínico"); win.destroy(); carregar()
            ttk.Button(win,text="Guardar registo",command=save).pack(pady=18)
        ttk.Button(self.area,text="Consultar histórico",command=carregar).pack(anchor="w",pady=8)
        ttk.Button(self.area,text="Adicionar registo clínico",command=adicionar).pack(anchor="w")
        carregar()

    def unidades(self):
        self.limpar_area(); self.titulo("Unidades sanitárias integradas")
        tree=self.tabela(self.area,("nome","tipo","municipio","contacto"),("Unidade","Tipo","Município","Contacto"))
        with conectar() as con: rows=con.execute("SELECT nome,tipo,municipio,contacto FROM unidades ORDER BY nome").fetchall()
        for r in rows: tree.insert("","end",values=r)
        if self.user["perfil"]=="Administrador":
            ttk.Button(self.area,text="Registar unidade",command=self.nova_unidade).pack(anchor="w")

    def nova_unidade(self):
        win=tk.Toplevel(self.root); win.title("Nova unidade sanitária"); win.geometry("400x330")
        entries={}
        for label in ["Nome","Tipo","Município","Contacto"]:
            ttk.Label(win,text=label).pack(anchor="w",padx=15,pady=(8,0))
            e=ttk.Entry(win,width=42); e.pack(padx=15); entries[label]=e
        def save():
            if not entries["Nome"].get().strip() or not entries["Município"].get().strip():
                messagebox.showwarning("Validação","Nome e município são obrigatórios."); return
            with conectar() as con:
                con.execute("INSERT INTO unidades(nome,tipo,municipio,contacto) VALUES(?,?,?,?)",
                    tuple(entries[k].get().strip() for k in ["Nome","Tipo","Município","Contacto"]))
            self.registar_acao("Registou unidade sanitária"); win.destroy(); self.unidades()
        ttk.Button(win,text="Guardar",command=save).pack(pady=16)

    def encaminhamentos(self):
        self.limpar_area(); self.titulo("Coordenação e encaminhamento de pacientes")
        patients=self.obter_paciente(self.area)
        if not patients: return
        with conectar() as con: units=con.execute("SELECT id,nome FROM unidades ORDER BY nome").fetchall()
        if len(units)<2: return
        pbox=ttk.Combobox(self.area,values=[f"{p[1]} — {p[2]}" for p in patients],state="readonly",width=55); pbox.pack(anchor="w",pady=4); pbox.current(0)
        ubox=ttk.Combobox(self.area,values=[u[1] for u in units],state="readonly",width=55); ubox.pack(anchor="w",pady=4)
        destino=next((i for i,u in enumerate(units) if u[0]!=self.user["unidade_id"]),0); ubox.current(destino)
        motivo=ttk.Entry(self.area,width=58); motivo.pack(anchor="w",pady=4); motivo.insert(0,"Motivo do encaminhamento")
        def criar():
            pid=patients[pbox.current()][0]; uid=units[ubox.current()][0]; why=motivo.get().strip()
            if uid==self.user["unidade_id"] or not why:
                messagebox.showwarning("Validação","Escolha outra unidade e indique o motivo."); return
            with conectar() as con:
                con.execute("""INSERT INTO encaminhamentos(paciente_id,origem_id,destino_id,data,motivo)
                    VALUES(?,?,?,?,?)""",(pid,self.user["unidade_id"],uid,datetime.now().strftime("%Y-%m-%d %H:%M"),why))
            self.registar_acao("Criou encaminhamento"); carregar(); messagebox.showinfo("Sucesso","Encaminhamento registado.")
        ttk.Button(self.area,text="Criar encaminhamento",command=criar).pack(anchor="w",pady=5)
        tree=self.tabela(self.area,("paciente","origem","destino","data","motivo","estado"),("Paciente","Origem","Destino","Data","Motivo","Estado"))
        def carregar():
            for x in tree.get_children(): tree.delete(x)
            with conectar() as con:
                rows=con.execute("""SELECT p.nome,o.nome,d.nome,e.data,e.motivo,e.estado
                    FROM encaminhamentos e JOIN pacientes p ON p.id=e.paciente_id
                    JOIN unidades o ON o.id=e.origem_id JOIN unidades d ON d.id=e.destino_id
                    ORDER BY e.id DESC""").fetchall()
            for r in rows: tree.insert("","end",values=r)
        carregar()

    def relatorios(self):
        self.limpar_area(); self.titulo("Relatórios e indicadores")
        with conectar() as con:
            dados=[
                ("Total de pacientes",con.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]),
                ("Unidades sanitárias",con.execute("SELECT COUNT(*) FROM unidades").fetchone()[0]),
                ("Registos clínicos",con.execute("SELECT COUNT(*) FROM registos_clinicos").fetchone()[0]),
                ("Encaminhamentos",con.execute("SELECT COUNT(*) FROM encaminhamentos").fetchone()[0]),
                ("Encaminhamentos pendentes",con.execute("SELECT COUNT(*) FROM encaminhamentos WHERE estado='Pendente'").fetchone()[0])]
        for label,value in dados: ttk.Label(self.area,text=f"{label}: {value}",font=("Segoe UI",12)).pack(anchor="w",pady=8)

    def utilizadores(self):
        self.limpar_area(); self.titulo("Gestão de utilizadores")
        tree=self.tabela(self.area,("nome","username","perfil","unidade"),("Nome","Utilizador","Perfil","Unidade"))
        with conectar() as con:
            rows=con.execute("""SELECT a.nome,a.username,a.perfil,COALESCE(u.nome,'-')
                FROM utilizadores a LEFT JOIN unidades u ON u.id=a.unidade_id ORDER BY a.nome""").fetchall()
        for r in rows: tree.insert("","end",values=r)
        ttk.Button(self.area,text="Criar utilizador",command=self.novo_utilizador).pack(anchor="w")

    def novo_utilizador(self):
        win=tk.Toplevel(self.root); win.title("Criar utilizador"); win.geometry("420x400")
        fields={}
        for label in ["Nome completo","Nome de utilizador","Palavra-passe"]:
            ttk.Label(win,text=label).pack(anchor="w",padx=15,pady=(8,0))
            e=ttk.Entry(win,width=44,show="*" if label=="Palavra-passe" else ""); e.pack(padx=15); fields[label]=e
        ttk.Label(win,text="Perfil").pack(anchor="w",padx=15,pady=(8,0))
        perfil=ttk.Combobox(win,values=["Profissional","Administrador"],state="readonly"); perfil.pack(padx=15); perfil.current(0)
        with conectar() as con: units=con.execute("SELECT id,nome FROM unidades").fetchall()
        ttk.Label(win,text="Unidade").pack(anchor="w",padx=15,pady=(8,0))
        unidade=ttk.Combobox(win,values=[u[1] for u in units],state="readonly"); unidade.pack(padx=15); unidade.current(0)
        def save():
            nome=fields["Nome completo"].get().strip(); username=fields["Nome de utilizador"].get().strip(); senha=fields["Palavra-passe"].get()
            if not nome or not username or len(senha)<8:
                messagebox.showwarning("Validação","Preencha os campos e use palavra-passe com pelo menos 8 caracteres."); return
            salt,digest=hash_senha(senha)
            try:
                with conectar() as con:
                    con.execute("""INSERT INTO utilizadores(nome,username,salt,senha_hash,perfil,unidade_id)
                        VALUES(?,?,?,?,?,?)""",(nome,username,salt,digest,perfil.get(),units[unidade.current()][0]))
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro","Esse nome de utilizador já existe."); return
            self.registar_acao("Criou utilizador "+username); win.destroy(); self.utilizadores()
        ttk.Button(win,text="Guardar utilizador",command=save).pack(pady=18)

    def logout(self):
        self.registar_acao("Terminou sessão"); self.user=None; self.login()

if __name__ == "__main__":
    inicializar_bd()
    root=tk.Tk()
    app=SIIApp(root)
    root.mainloop()

 