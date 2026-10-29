#!/usr/bin/env python3
"""
Interface gráfica leve do converter-mov (tkinter, só stdlib).

Aberta com: converter-mov gui

Fluxos:
- Pasta: mesma rotina do CLI — converte todos os .MOV para "converted/",
  mostra barra do arquivo e barra do total, verifica e pergunta se deleta
  os originais; no fim volta para a tela inicial.
- Arquivo único: pergunta onde salvar (padrão: converted/<nome>.mp4),
  converte, verifica e pergunta se exclui o original; volta ao início.

Visual: Material Design 3 dark, desenhado à mão no Canvas (botões pílula,
barras arredondadas, cartão do log) — paleta e constantes no topo do arquivo.
Sem dependências fora do stdlib (ADR-002).

Os workers rodam em uma thread e só falam com a interface por uma fila de
eventos; nenhuma chamada deles toca no tkinter. As caixas de diálogo passam
por messagebox/filedialog do módulo, o que permite trocá-las nos testes.
"""

import contextlib
import os
import queue
import threading
import tkinter as tk
import tkinter.font as tkfont
import traceback
from tkinter import filedialog, messagebox

import converter_mov as core

POLL_MS = 80  # frequência de leitura da fila, em ms

# ------------------------------------------------- paleta Material 3 (dark)
# Trocar estes hex muda toda a interface (é a única parte "de design").
PRIMARIA = "#D0BCFF"  # botão preenchido, percentuais, acentos
SOBRE_PRIMARIA = "#381E72"  # texto sobre o botão preenchido
CONTAINER = "#4F378B"  # fundo de chips/estado selecionado
SUPERFICIE = "#1C1B1F"  # fundo da janela
CONTAINER2 = "#2B2930"  # cartão do log
VARIAVEL = "#49454F"  # trilho da barra, contorno do cartão
TEXTO = "#E6E0E9"
TEXTO_FOFO = "#CAC4D0"
CONTORNO = "#938F99"
ERRO = "#FFB4AB"
OK = "#63D471"
PRETO = "#000000"

FONTES_TEXTO = ("Roboto", "Cantarell", "Noto Sans", "Ubuntu", "DejaVu Sans")
FONTES_MONO = ("Roboto Mono", "DejaVu Sans Mono", "Ubuntu Mono", "Liberation Mono")


# ------------------------------------------------------ helpers de desenho


def _rgb(cor):
    c = cor.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def misturar(cor1, cor2, t):
    """Mistura duas cores #RRGGBB (t=0 → cor1, t=1 → cor2).
    Tk não tem canal alfa, então hover/sombra são misturas calculadas."""
    a, b = _rgb(cor1), _rgb(cor2)
    r = round(a[0] + (b[0] - a[0]) * t)
    g = round(a[1] + (b[1] - a[1]) * t)
    az = round(a[2] + (b[2] - a[2]) * t)
    return f"#{r:02x}{g:02x}{az:02x}"


def retangulo(canvas, x1, y1, x2, y2, raio, **kwargs):
    """Retângulo arredondado num Canvas (polígono suave — o Tk não tem cantos redondos)."""
    r = max(0.0, min(raio, (x2 - x1) / 2, (y2 - y1) / 2))
    pontos = [
        x1 + r,
        y1,
        x2 - r,
        y1,
        x2,
        y1,
        x2,
        y1 + r,
        x2,
        y2 - r,
        x2,
        y2,
        x2 - r,
        y2,
        x1 + r,
        y2,
        x1,
        y2,
        x1,
        y2 - r,
        x1,
        y1 + r,
        x1,
        y1,
        x1 + r,
        y1,
    ]
    return canvas.create_polygon(pontos, smooth=True, **kwargs)


def _familia_instalada(candidatas):
    """Primeira fonte da lista que existe no sistema (senão None)."""
    disponiveis = set(tkfont.families())
    return next((n for n in candidatas if n in disponiveis), None)


class Botao(tk.Canvas):
    """Botão Material desenhado à mão: pílula arredondada, hover e pressionado.
    O botão padrão do Tk é quadrado e sem estado; no Canvas ganhamos cantos
    redondos, state layers (misturas de cor) e a elevação do botão preenchido."""

    ELEVAÇÃO = 3

    def __init__(
        self,
        pai,
        texto,
        comando=None,
        tipo="primario",
        largura=260,
        altura=48,
        fonte=None,
        fundo=SUPERFICIE,
    ):
        self.elevacao = self.ELEVAÇÃO if tipo == "primario" else 0
        super().__init__(
            pai,
            width=largura,
            height=altura + self.elevacao,
            bd=0,
            highlightthickness=0,
            bg=fundo,
        )
        self.texto = texto
        self.comando = comando
        self.tipo = tipo
        self.altura = altura
        self.fonte = fonte
        self.fundo = fundo
        self.sobre = False
        self.pressionado = False
        self.bind("<Enter>", self._ao_entrar)
        self.bind("<Leave>", self._ao_sair)
        self.bind("<ButtonPress-1>", self._ao_pressionar)
        self.bind("<ButtonRelease-1>", self._ao_soltar)
        self.bind("<Configure>", self._ao_redimensionar)
        self._desenhar()

    def _ao_entrar(self, _evento):
        self.sobre = True
        self._desenhar()

    def _ao_sair(self, _evento):
        self.sobre = False
        self.pressionado = False
        self._desenhar()

    def _ao_pressionar(self, _evento):
        self.pressionado = True
        self._desenhar()

    def _ao_soltar(self, evento):
        dentro = 0 <= evento.x < self.winfo_width() and 0 <= evento.y < self.altura
        self.pressionado = False
        self._desenhar()
        if dentro and self.comando:
            self.comando()

    def _ao_redimensionar(self, evento):
        self._desenhar(evento.width)

    def _desenhar(self, larg=None):
        larg = larg or self.winfo_width() or int(self.cget("width"))
        if larg <= 4:
            return
        alt = self.altura
        raio = alt / 2
        self.delete("all")
        if self.tipo == "primario":
            if self.elevacao:  # sombra: banda deslocada, cor misturada com o fundo
                retangulo(
                    self,
                    0,
                    self.elevacao,
                    larg,
                    alt + self.elevacao,
                    raio,
                    fill=misturar(self.fundo, PRETO, 0.55),
                    outline="",
                )
            corpo = PRIMARIA
            if self.pressionado:
                corpo = misturar(corpo, PRETO, 0.30)
            elif self.sobre:
                corpo = misturar(corpo, "#FFFFFF", 0.12)
            rotulo, linha = SOBRE_PRIMARIA, ""
            espessura = 0
        else:  # contornado
            camada = 0.16 if self.pressionado else 0.10 if self.sobre else 0.0
            corpo = misturar(self.fundo, PRIMARIA, camada)
            rotulo = PRIMARIA
            linha = PRIMARIA if (self.sobre or self.pressionado) else CONTORNO
            espessura = 2
        retangulo(self, 0, 0, larg - 1, alt - 1, raio, fill=corpo, outline=linha, width=espessura)
        self.create_text(
            larg / 2,
            alt / 2,
            text=self.texto,
            fill=rotulo,
            font=self.fonte,
            anchor="center",
        )


class BarraProgresso(tk.Canvas):
    """Barra Material desenhada à mão: trilho e preenchimento arredondados
    (o ttk.Progressbar é quadrado e sem cantos redondos)."""

    def __init__(
        self, pai, altura=14, cor_preenchimento=PRIMARIA, cor_trilho=VARIAVEL, fundo=SUPERFICIE
    ):
        super().__init__(pai, height=altura, bd=0, highlightthickness=0, bg=fundo)
        self.altura = altura
        self.cor_preenchimento = cor_preenchimento
        self.cor_trilho = cor_trilho
        self.fracao = 0.0
        self.bind("<Configure>", lambda _evento: self._desenhar())

    def definir(self, fracao):
        self.fracao = max(0.0, min(1.0, fracao))
        self._desenhar()

    def _desenhar(self):
        larg = self.winfo_width()
        if larg <= 4:
            return
        self.delete("all")
        raio = self.altura / 2
        retangulo(self, 0, 0, larg - 1, self.altura - 1, raio, fill=self.cor_trilho, outline="")
        if self.fracao > 0:
            preenchido = max(self.altura, round(larg * self.fracao))
            retangulo(
                self,
                0,
                0,
                min(preenchido, larg) - 1,
                self.altura - 1,
                raio,
                fill=self.cor_preenchimento,
                outline="",
            )


# ------------------------------------------------------- rotinas em thread


def _trabalho_pasta(pasta, *, avisar):
    """Conversão em pasta, idêntica à do CLI (converter-mov [pasta])."""
    core.PASTA = pasta
    core.SAIDA = os.path.join(pasta, "converted")
    core.LOG = os.path.join(pasta, "converter_error_log.txt")
    core._log_iniciado = False

    arquivos = sorted(
        f
        for f in os.listdir(pasta)
        if f.lower().endswith(".mov") and os.path.isfile(os.path.join(pasta, f))
    )
    if not arquivos:
        avisar("sem_arquivos", pasta)
        return

    avisar("log", f"Pasta: {pasta}")
    avisar("log", "Arquivos .MOV encontrados:")
    for f in arquivos:
        avisar("log", f"  - {f}")
    avisar("log", f"Total: {len(arquivos)} arquivo(s)")

    gpu = core.tem_nvenc()
    cuda = gpu and core.tem_cuda_decode()
    if gpu:
        avisar(
            "log",
            "GPU NVIDIA detectada: usando NVENC (HEVC)"
            + (" + decodificação CUDA." if cuda else "."),
        )
    else:
        avisar("log", "GPU NVIDIA não disponível: usando a CPU (mais lento).")

    os.makedirs(core.SAIDA, exist_ok=True)

    infos = {f: core.info_video(os.path.join(pasta, f)) for f in arquivos}
    dur_total = sum(i["duracao"] for i in infos.values()) or 1
    feito = 0.0
    falhas = []

    def progresso(frac, total):
        avisar("progresso", frac, total)

    for i, f in enumerate(arquivos, 1):
        entrada = os.path.join(pasta, f)
        saida = os.path.join(core.SAIDA, os.path.splitext(f)[0] + ".mp4")
        info = infos[f]
        avisar(
            "cabecalho",
            f"({i}/{len(arquivos)}) {f}  [{info['fps']:.2f} fps -> "
            f"{core.fps_constante(info['fps'])}"
            f"{', 10 bits' if info['dez_bits'] else ''}]",
        )
        ok, erro = core.converter(
            entrada, saida, f, info, feito, dur_total, gpu, cuda, progresso=progresso
        )
        feito += info["duracao"]
        if ok:
            avisar(
                "log", f"  OK    ({i}/{len(arquivos)}) {f} -> converted/{os.path.basename(saida)}"
            )
        else:
            avisar("log", f"  ERRO  ({i}/{len(arquivos)}) {f}: {erro or 'desconhecido'}")
            falhas.append(f)

    avisar("log", "Verificando arquivos convertidos...")
    verificados = []
    for f in arquivos:
        if f in falhas:
            continue
        convertido = os.path.join(core.SAIDA, os.path.splitext(f)[0] + ".mp4")
        ok, msg = core.verificar(os.path.join(pasta, f), convertido)
        detalhe = ""
        if isinstance(msg, tuple):
            msg, detalhe = msg
        avisar("log", f"  {'OK   ' if ok else 'FALHA'} {f} -> {msg}")
        if ok:
            verificados.append(f)
        else:
            falhas.append(f)
            core.registrar_erro(
                f"{f}: falhou na verificação - {msg}",
                f"Arquivo convertido: {convertido}\n"
                f"Original: {core.info_video(os.path.join(pasta, f))}\n"
                f"Convertido: {core.info_video(convertido)}\n{detalhe}",
            )

    if core._log_iniciado:
        avisar("log", f"Detalhes dos erros em: {core.LOG}")
    avisar(
        "fim",
        {
            "modo": "pasta",
            "pasta": pasta,
            "arquivos": arquivos,
            "verificados": verificados,
            "falhas": falhas,
        },
    )


def _trabalho_arquivo(entrada, saida, *, avisar):
    """Um arquivo só: converte para `saida` (já escolhido) e verifica."""
    pasta = os.path.dirname(entrada) or os.getcwd()
    nome = os.path.basename(entrada)
    core.PASTA = pasta
    core.SAIDA = os.path.dirname(saida) or pasta
    core.LOG = os.path.join(pasta, "converter_error_log.txt")
    core._log_iniciado = False

    info = core.info_video(entrada)
    gpu = core.tem_nvenc()
    cuda = gpu and core.tem_cuda_decode()
    if gpu:
        avisar(
            "log",
            "GPU NVIDIA detectada: usando NVENC (HEVC)"
            + (" + decodificação CUDA." if cuda else "."),
        )
    else:
        avisar("log", "GPU NVIDIA não disponível: usando a CPU (mais lento).")

    os.makedirs(core.SAIDA, exist_ok=True)
    avisar(
        "cabecalho",
        f"{nome}  [{info['fps']:.2f} fps -> "
        f"{core.fps_constante(info['fps'])}"
        f"{', 10 bits' if info['dez_bits'] else ''}]",
    )

    def progresso(frac, total):
        avisar("progresso", frac, total)

    dur = info["duracao"] or 1
    ok, erro = core.converter(entrada, saida, nome, info, 0, dur, gpu, cuda, progresso=progresso)
    verificados = []
    falhas = []
    if ok:
        avisar("log", f"  OK    {nome} -> {saida}")
        avisar("progresso", 1.0, 1.0)
        avisar("log", "Verificando arquivo convertido...")
        ok_v, msg = core.verificar(entrada, saida)
        detalhe = ""
        if isinstance(msg, tuple):
            msg, detalhe = msg
        avisar("log", f"  {'OK   ' if ok_v else 'FALHA'} {nome} -> {msg}")
        if ok_v:
            verificados.append(nome)
        else:
            falhas.append(nome)
            core.registrar_erro(
                f"{nome}: falhou na verificação - {msg}",
                f"Arquivo convertido: {saida}\n"
                f"Original: {core.info_video(entrada)}\n"
                f"Convertido: {core.info_video(saida)}\n{detalhe}",
            )
    else:
        avisar("log", f"  ERRO  {nome}: {erro or 'desconhecido'}")
        falhas.append(nome)

    if core._log_iniciado:
        avisar("log", f"Detalhes dos erros em: {core.LOG}")
    avisar(
        "fim",
        {
            "modo": "arquivo",
            "pasta": pasta,
            "entrada": entrada,
            "arquivos": [nome],
            "verificados": verificados,
            "falhas": falhas,
        },
    )


# ---------------------------------------------------------------- janela


class Aplicacao(tk.Tk):
    """Duas telas empilhadas: inicial (escolher) e trabalho (barras + log)."""

    def __init__(self):
        super().__init__()
        self.title("Converter MOV → MP4 (HEVC)")
        self.geometry("780x580")
        self.minsize(700, 500)
        self.configure(bg=SUPERFICIE)
        self.fila = queue.Queue()
        self.rodando = False
        self.terminou = False  # vira True no fim de cada fluxo (testes leem)
        # Material usa Roboto; sem ela, a sans/mono do sistema
        self.familia = _familia_instalada(FONTES_TEXTO) or "Sans"
        self.mono = _familia_instalada(FONTES_MONO) or tkfont.nametofont("TkFixedFont").actual(
            "family"
        )
        self.fonte_titulo = (self.familia, 20, "bold")
        self.fonte_texto = (self.familia, 11)
        self.fonte_forte = (self.familia, 11, "bold")
        self.fonte_rotulo = (self.familia, 10)
        self.fonte_pct = (self.familia, 10, "bold")
        self.fonte_cabecalho = (self.mono, 10)
        self.fonte_log = (self.mono, 9)
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self._construir_inicio()
        self._construir_trabalho()
        self._mostrar_inicio()
        self._poll_id = self.after(POLL_MS, self._poll)
        threading.Thread(target=self._detectar_gpu, daemon=True).start()

    # telas

    def _construir_inicio(self):
        # place (não pack): as duas telas ocupam a janela inteira e o
        # tkraise() decide qual aparece por cima
        self.tela_inicio = tk.Frame(self, padx=36, pady=32, bg=SUPERFICIE)
        self.tela_inicio.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Frame(self.tela_inicio, bg=SUPERFICIE).pack(fill="both", expand=True)
        tk.Label(
            self.tela_inicio,
            text="Converter MOV → MP4 (HEVC)",
            font=self.fonte_titulo,
            bg=SUPERFICIE,
            fg=TEXTO,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            self.tela_inicio,
            anchor="w",
            wraplength=680,
            justify="left",
            font=self.fonte_texto,
            bg=SUPERFICIE,
            fg=TEXTO_FOFO,
            text=(
                "Escolha uma pasta (converte todos os .MOV para a subpasta "
                "'converted', com barra do arquivo e do total, e no fim pergunta "
                "se deleta os originais) ou um único arquivo (pergunta onde "
                "salvar e, no fim, se exclui o original)."
            ),
        ).pack(fill="x", pady=(10, 0))

        linha = tk.Frame(self.tela_inicio, bg=SUPERFICIE)
        linha.pack(anchor="w", pady=(28, 0))
        self.botao_pasta = Botao(
            linha,
            "Carregar pasta…",
            self._escolher_pasta,
            "primario",
            fonte=self.fonte_forte,
        )
        self.botao_pasta.pack(side="left", padx=(0, 16))
        self.botao_arquivo = Botao(
            linha,
            "Carregar arquivo…",
            self._escolher_arquivo,
            "contornado",
            fonte=self.fonte_forte,
        )
        self.botao_arquivo.pack(side="left")

        self.rotulo_gpu = tk.Label(
            self.tela_inicio,
            text="GPU: verificando…",
            font=self.fonte_rotulo,
            bg=SUPERFICIE,
            fg=TEXTO_FOFO,
            anchor="w",
        )
        self.rotulo_gpu.pack(fill="x", pady=(32, 0))
        tk.Frame(self.tela_inicio, bg=SUPERFICIE).pack(fill="both", expand=True)

    def _construir_trabalho(self):
        self.tela_trabalho = tk.Frame(self, padx=36, pady=32, bg=SUPERFICIE)
        self.tela_trabalho.place(x=0, y=0, relwidth=1, relheight=1)
        self.rotulo_cabecalho = tk.Label(
            self.tela_trabalho,
            anchor="w",
            font=self.fonte_cabecalho,
            bg=SUPERFICIE,
            fg=TEXTO,
        )
        self.rotulo_cabecalho.pack(fill="x", pady=(0, 16))

        caixa_barras = tk.Frame(self.tela_trabalho, bg=SUPERFICIE)
        caixa_barras.pack(fill="x")
        caixa_barras.columnconfigure(1, weight=1)
        tk.Label(
            caixa_barras,
            text="Arquivo",
            font=self.fonte_rotulo,
            bg=SUPERFICIE,
            fg=TEXTO_FOFO,
        ).grid(row=0, column=0, sticky="w")
        self.barra_arquivo = BarraProgresso(caixa_barras)
        self.barra_arquivo.grid(row=0, column=1, sticky="ew", padx=12)
        self.rotulo_pct_arquivo = tk.Label(
            caixa_barras,
            text="0%",
            width=5,
            font=self.fonte_pct,
            bg=SUPERFICIE,
            fg=PRIMARIA,
            anchor="e",
        )
        self.rotulo_pct_arquivo.grid(row=0, column=2, sticky="e")
        tk.Label(
            caixa_barras,
            text="Total",
            font=self.fonte_rotulo,
            bg=SUPERFICIE,
            fg=TEXTO_FOFO,
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))
        self.barra_total = BarraProgresso(caixa_barras)
        self.barra_total.grid(row=1, column=1, sticky="ew", padx=12, pady=(12, 0))
        self.rotulo_pct_total = tk.Label(
            caixa_barras,
            text="0%",
            width=5,
            font=self.fonte_pct,
            bg=SUPERFICIE,
            fg=PRIMARIA,
            anchor="e",
        )
        self.rotulo_pct_total.grid(row=1, column=2, sticky="e", pady=(12, 0))

        # log dentro de um cartão arredondado: um Canvas por baixo do Text
        cartao = tk.Frame(self.tela_trabalho, bg=SUPERFICIE)
        cartao.pack(fill="both", expand=True, pady=(24, 0))
        fundo = tk.Canvas(cartao, bd=0, highlightthickness=0, bg=SUPERFICIE)
        fundo.place(relx=0, rely=0, relwidth=1, relheight=1)
        fundo.bind("<Configure>", self._desenhar_cartao)
        self.caixa_log = tk.Text(
            cartao,
            height=14,
            state="disabled",
            bg=CONTAINER2,
            fg=TEXTO_FOFO,
            insertbackground=TEXTO,
            selectbackground=CONTAINER,
            relief="flat",
            bd=0,
            highlightthickness=0,
            wrap="word",
            font=self.fonte_log,
        )
        self.caixa_log.pack(fill="both", expand=True, padx=16, pady=16)

    @staticmethod
    def _desenhar_cartao(evento):
        canvas = evento.widget
        canvas.delete("all")
        larg, alt = canvas.winfo_width(), canvas.winfo_height()
        if larg > 8 and alt > 8:
            retangulo(
                canvas,
                0,
                0,
                larg - 1,
                alt - 1,
                16,
                fill=CONTAINER2,
                outline=VARIAVEL,
                width=1,
            )

    def _mostrar_inicio(self):
        self.tela_inicio.tkraise()

    # escolhas iniciais

    def _escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Escolha a pasta com os .MOV")
        if pasta:
            self.iniciar_pasta(pasta)

    def _escolher_arquivo(self):
        entrada = filedialog.askopenfilename(
            title="Escolha o arquivo .MOV",
            filetypes=[("Vídeo MOV", "*.mov *.MOV"), ("Todos os arquivos", "*.*")],
        )
        if entrada:
            self.iniciar_arquivo(entrada)

    # fluxos

    def iniciar_pasta(self, pasta):
        """Conversão em pasta: a mesma rotina do CLI."""
        self._iniciar(_trabalho_pasta, pasta)

    def iniciar_arquivo(self, entrada):
        """Um arquivo só: pergunta onde salvar (padrão: converted/<nome>.mp4)."""
        pasta = os.path.dirname(entrada) or os.getcwd()
        nome = os.path.basename(entrada)
        convertida = os.path.join(pasta, "converted")
        saida = filedialog.asksaveasfilename(
            title="Salvar arquivo convertido em…",
            initialdir=convertida if os.path.isdir(convertida) else pasta,
            initialfile=os.path.splitext(nome)[0] + ".mp4",
            defaultextension=".mp4",
            filetypes=[("Vídeo MP4", "*.mp4")],
        )
        if not saida:
            return  # cancelou: fica na tela inicial
        self._iniciar(_trabalho_arquivo, entrada, os.path.abspath(saida))

    def _iniciar(self, funcao, *argumentos):
        self.rodando = True
        self.terminou = False
        self._limpar_trabalho()
        self.tela_trabalho.tkraise()
        threading.Thread(target=self._rodar, args=(funcao, *argumentos), daemon=True).start()

    def _rodar(self, funcao, *argumentos):
        def avisar(*evento):
            self.fila.put(evento)

        try:
            funcao(*argumentos, avisar=avisar)
        except Exception:
            core.registrar_erro("Erro inesperado na GUI", traceback.format_exc())
            avisar("log", f"Erro inesperado. Detalhes em: {core.LOG}")
            avisar(
                "fim",
                {
                    "modo": "erro",
                    "pasta": core.PASTA,
                    "arquivos": [],
                    "verificados": [],
                    "falhas": [],
                },
            )

    # eventos vindos da thread

    def _poll(self):
        try:
            while True:
                self._processar(self.fila.get_nowait())
        except queue.Empty:
            pass
        self._poll_id = self.after(POLL_MS, self._poll)

    def _processar(self, evento):
        tipo = evento[0]
        if tipo == "progresso":
            frac = max(0.0, min(1.0, evento[1]))
            total = max(0.0, min(1.0, evento[2]))
            self.barra_arquivo.definir(frac)
            self.barra_total.definir(total)
            self.rotulo_pct_arquivo.config(text=f"{frac * 100:.0f}%")
            self.rotulo_pct_total.config(text=f"{total * 100:.0f}%")
        elif tipo == "log":
            self._log(evento[1])
        elif tipo == "cabecalho":
            self.rotulo_cabecalho.config(text=evento[1])
        elif tipo == "gpu":
            cor = OK if "NVENC" in evento[1] else ERRO
            self.rotulo_gpu.config(text=evento[1], fg=cor)
        elif tipo == "sem_arquivos":
            messagebox.showinfo("Converter MOV", f"Nenhum arquivo .MOV encontrado em:\n{evento[1]}")
            self.rodando = False
            self.terminou = True
            self._mostrar_inicio()
        elif tipo == "fim":
            self._finalizar(evento[1])

    def _finalizar(self, resultado):
        """Resumo, pergunta de exclusão (só de verificados) e volta ao início."""
        verificados = resultado.get("verificados", [])
        falhas = resultado.get("falhas", [])
        self.rodando = False

        self._log(f"\n{len(verificados)} convertido(s) com sucesso, {len(falhas)} com problema.")
        if falhas:
            self._log("Arquivos com problema (não serão apagados):")
            for f in falhas:
                self._log(f"  - {f}")

        if verificados:
            apagar = messagebox.askyesno(
                "Deletar originais",
                f"Deletar os {len(verificados)} arquivo(s) .MOV convertidos com sucesso?",
            )
            if apagar:
                for f in verificados:
                    with contextlib.suppress(OSError):
                        os.remove(os.path.join(resultado["pasta"], f))
                self._log("Arquivos .MOV deletados.")
            else:
                self._log("Nenhum arquivo foi deletado.")

        self.terminou = True
        self._mostrar_inicio()

    # auxiliares

    def _log(self, texto):
        self.caixa_log.config(state="normal")
        self.caixa_log.insert("end", texto + "\n")
        self.caixa_log.see("end")
        self.caixa_log.config(state="disabled")

    def _limpar_trabalho(self):
        self.rotulo_cabecalho.config(text="")
        self.barra_arquivo.definir(0)
        self.barra_total.definir(0)
        self.rotulo_pct_arquivo.config(text="0%")
        self.rotulo_pct_total.config(text="0%")
        self.caixa_log.config(state="normal")
        self.caixa_log.delete("1.0", "end")
        self.caixa_log.config(state="disabled")

    def _detectar_gpu(self):
        """Roda na startup para preencher o rótulo da tela inicial."""
        gpu = core.tem_nvenc()
        cuda = gpu and core.tem_cuda_decode()
        if gpu:
            texto = "GPU: NVENC (HEVC) + decodificação CUDA" if cuda else "GPU: NVENC (HEVC)"
        else:
            texto = "GPU: não disponível — conversão na CPU (mais lenta)"
        self.fila.put(("gpu", texto))

    def _fechar(self):
        if self.rodando and not messagebox.askyesno(
            "Sair", "Conversão em andamento. Sair mesmo assim?"
        ):
            return
        self.destroy()

    def destroy(self):
        """Cancela o timer da fila antes de destruir (evita erro do Tcl)."""
        if getattr(self, "_poll_id", None) is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._poll_id)
            self._poll_id = None
        super().destroy()


def rodar_interface():
    """Ponto de entrada: `converter-mov gui` (ou `python3 gui.py`)."""
    Aplicacao().mainloop()


if __name__ == "__main__":
    rodar_interface()
