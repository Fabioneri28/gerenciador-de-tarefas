import customtkinter as ctk
from datetime import datetime
import calendar
import sqlite3
from tkinter import simpledialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------- CONFIG ----------------
APP_WIDTH = 1350
APP_HEIGHT = 780
DB_FILE = "habitos.db"

ctk.set_default_color_theme("blue")

# ---------------- DATABASE ----------------
def get_conn():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS habitos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            habito_id INTEGER,
            dia INTEGER,
            feito INTEGER,
            PRIMARY KEY (habito_id, dia)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estado (
            dia INTEGER PRIMARY KEY,
            humor INTEGER,
            motivacao INTEGER
        )
    """)
    conn.commit()
    conn.close()


# ---------------- APP ----------------
class DashboardHabitos(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dashboard de Hábitos")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(1200, 720)

        self.modo = "light"
        ctk.set_appearance_mode(self.modo)

        self.hoje = datetime.now()
        self.mes = self.hoje.month
        self.ano = self.hoje.year
        self.dias_mes = calendar.monthrange(self.ano, self.mes)[1]

        init_db()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.layout()
        self.render_tabela()
        self.atualizar_progresso()
        self.atualizar_graficos()

    # ---------------- LAYOUT ----------------
    def layout(self):
        self.topo()
        self.sidebar()
        self.tabela_frame = ctk.CTkScrollableFrame(self)
        self.tabela_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.rodape()

    def topo(self):
        t = ctk.CTkFrame(self, height=80)
        t.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        t.grid_columnconfigure((0,1,2,3), weight=1)

        mes_nome = calendar.month_name[self.mes].capitalize()
        ctk.CTkLabel(t, text=f"{mes_nome} / {self.ano}", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, sticky="w", padx=20)

        self.lbl_prog = ctk.CTkLabel(t, text="Progresso Geral: 0%")
        self.lbl_prog.grid(row=0, column=1)

        self.pb = ctk.CTkProgressBar(t, width=300)
        self.pb.grid(row=0, column=2)

        ctk.CTkButton(t, text="+ Hábito", command=self.add_habito).grid(row=0, column=3, sticky="e", padx=10)
        ctk.CTkButton(t, text="🌗 Tema", width=80, command=self.toggle_tema).grid(row=0, column=4, sticky="e", padx=10)

    def sidebar(self):
        self.side = ctk.CTkFrame(self, width=300)
        self.side.grid(row=1, column=0, sticky="nsw", padx=10, pady=10)
        self.side.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self.side, text="Análise por Hábito", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=10)
        self.lista = ctk.CTkScrollableFrame(self.side, height=220)
        self.lista.grid(row=1, column=0, sticky="nsew", padx=10)

        self.fig1 = plt.Figure(figsize=(3,2.2), dpi=100)
        self.ax1 = self.fig1.add_subplot(111)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.side)
        self.canvas1.get_tk_widget().grid(row=2, column=0, padx=10, pady=10)

        self.fig2 = plt.Figure(figsize=(3,2.2), dpi=100)
        self.ax2 = self.fig2.add_subplot(111)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.side)
        self.canvas2.get_tk_widget().grid(row=3, column=0, padx=10, pady=10)

    def rodape(self):
        r = ctk.CTkFrame(self, height=90)
        r.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        r.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(r, text="Humor (1–10)").grid(row=0, column=0)
        self.s_humor = ctk.CTkSlider(r, from_=1, to=10, number_of_steps=9, command=self.set_estado)
        self.s_humor.grid(row=0, column=1, sticky="ew", padx=10)

        ctk.CTkLabel(r, text="Motivação (1–10)").grid(row=0, column=2)
        self.s_motiv = ctk.CTkSlider(r, from_=1, to=10, number_of_steps=9, command=self.set_estado)
        self.s_motiv.grid(row=0, column=3, sticky="ew", padx=10)

    # ---------------- DATA ----------------
    def get_habitos(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM habitos")
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------------- TABELA ----------------
    def render_tabela(self):
        for w in self.tabela_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.tabela_frame, text="Hábito", width=200).grid(row=0, column=0)
        for d in range(1, self.dias_mes+1):
            ctk.CTkLabel(self.tabela_frame, text=str(d), width=26).grid(row=0, column=d)

        self.vars = {}
        for i,(hid,nome) in enumerate(self.get_habitos(), start=1):
            ctk.CTkLabel(self.tabela_frame, text=nome, width=200, anchor="w").grid(row=i, column=0)
            self.vars[hid] = []
            for d in range(1, self.dias_mes+1):
                v = ctk.BooleanVar(value=self.get_check(hid,d))
                ctk.CTkCheckBox(self.tabela_frame, text="", variable=v, width=18,
                                command=lambda h=hid: self.on_check(h)).grid(row=i, column=d)
                self.vars[hid].append(v)

            ctk.CTkButton(self.tabela_frame, text="🗑", width=30,
                          command=lambda h=hid: self.remover_habito(h)).grid(row=i, column=self.dias_mes+1)

        self.render_lista()

    def get_check(self, hid, dia):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT feito FROM checks WHERE habito_id=? AND dia=?", (hid,dia))
        r = cur.fetchone()
        conn.close()
        return bool(r[0]) if r else False

    def on_check(self, hid):
        conn = get_conn()
        cur = conn.cursor()
        for dia,v in enumerate(self.vars[hid], start=1):
            cur.execute("REPLACE INTO checks VALUES (?,?,?)", (hid,dia,int(v.get())))
        conn.commit(); conn.close()
        self.atualizar_progresso(); self.render_lista(); self.atualizar_graficos()

    # ---------------- SIDEBAR ----------------
    def render_lista(self):
        for w in self.lista.winfo_children(): w.destroy()
        conn = get_conn(); cur = conn.cursor()
        for hid,nome in self.get_habitos():
            cur.execute("SELECT COUNT(*) FROM checks WHERE habito_id=? AND feito=1", (hid,))
            feitos = cur.fetchone()[0]
            pct = int((feitos/(self.dias_mes))*100) if self.dias_mes else 0
            ctk.CTkLabel(self.lista, text=f"{nome} — {pct}%").pack(anchor="w", padx=6, pady=2)
        conn.close()

    # ---------------- GRAFICOS ----------------
    def atualizar_graficos(self):
        self.ax1.clear(); self.ax2.clear()
        conn = get_conn(); cur = conn.cursor()

        diario = []
        for d in range(1, self.dias_mes+1):
            cur.execute("SELECT COUNT(*) FROM checks WHERE dia=? AND feito=1", (d,))
            diario.append(cur.fetchone()[0])
        self.ax1.plot(diario); self.ax1.set_title("Progresso Diário")

        cur.execute("SELECT dia, humor, motivacao FROM estado ORDER BY dia")
        rows = cur.fetchall()
        if rows:
            dias = [r[0] for r in rows]
            humor = [r[1] for r in rows]
            motiv = [r[2] for r in rows]
            self.ax2.plot(dias, humor, label="Humor")
            self.ax2.plot(dias, motiv, label="Motivação")
            self.ax2.legend()
            self.ax2.set_title("Estado Mental")

        conn.close()
        self.canvas1.draw(); self.canvas2.draw()

    # ---------------- ESTADO ----------------
    def set_estado(self, _=None):
        dia = self.hoje.day
        conn = get_conn(); cur = conn.cursor()
        cur.execute("REPLACE INTO estado VALUES (?,?,?)", (dia,int(self.s_humor.get()),int(self.s_motiv.get())))
        conn.commit(); conn.close()
        self.atualizar_graficos()

    # ---------------- CRUD ----------------
    def add_habito(self):
        nome = simpledialog.askstring("Novo Hábito", "Nome do hábito:")
        if nome:
            try:
                conn = get_conn(); cur = conn.cursor()
                cur.execute("INSERT INTO habitos(nome) VALUES (?)", (nome,))
                conn.commit(); conn.close()
                self.render_tabela()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Hábito já existe")

    def remover_habito(self, hid):
        if messagebox.askyesno("Confirmar", "Remover hábito?"):
            conn = get_conn(); cur = conn.cursor()
            cur.execute("DELETE FROM habitos WHERE id=?", (hid,))
            cur.execute("DELETE FROM checks WHERE habito_id=?", (hid,))
            conn.commit(); conn.close()
            self.render_tabela(); self.atualizar_progresso(); self.atualizar_graficos()

    # ---------------- PROGRESSO ----------------
    def atualizar_progresso(self):
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM checks WHERE feito=1")
        feitos = cur.fetchone()[0]
        total = self.dias_mes * max(len(self.get_habitos()),1)
        p = feitos/total if total else 0
        self.pb.set(p)
        self.lbl_prog.configure(text=f"Progresso Geral: {int(p*100)}%")
        conn.close()

    # ---------------- TEMA ----------------
    def toggle_tema(self):
        self.modo = "dark" if self.modo=="light" else "light"
        ctk.set_appearance_mode(self.modo)


# ---------------- RUN ----------------
if __name__ == '__main__':
    app = DashboardHabitos()
    app.mainloop()