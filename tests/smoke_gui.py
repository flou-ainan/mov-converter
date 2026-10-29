#!/usr/bin/env python3
"""
Smoke test headless do CLI e da GUI (sem mídia no repositório).

Gera clips sintéticos com ffmpeg em um diretório temporário e verifica:
- CLI: converte para `converted/`, pede confirmação antes de deletar
  (responde "n" → original fica); com `-s` deleta os verificados;
- GUI (sob xvfb, diálogos trocados por stubs): fluxo de pasta e fluxo
  de arquivo único, ambos voltando para a tela inicial no fim.

Uso:
    xvfb-run -a python3 tests/smoke_gui.py
"""

import os
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, REPO)
CLI = os.path.join(REPO, "converter_mov.py")


def gerar_mov(destino, segundos=1.0):
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size=320x240:rate=30:duration={segundos}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={segundos}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-f",
            "mov",
            destino,
        ],
        check=True,
    )


def teste_cli(tmp):
    pasta = os.path.join(tmp, "cli")
    os.makedirs(pasta)
    for n in ("a", "b"):
        gerar_mov(os.path.join(pasta, f"{n}.MOV"))

    r = subprocess.run(
        [sys.executable, CLI, pasta], input="n\n", capture_output=True, text=True, timeout=180
    )
    assert r.returncode == 0, r.stderr
    assert os.path.isfile(os.path.join(pasta, "converted", "a.mp4"))
    assert os.path.isfile(os.path.join(pasta, "converted", "b.mp4"))
    assert os.path.isfile(os.path.join(pasta, "a.MOV")), "respondeu n: mantém"
    assert "converted" in r.stdout, "saída deve citar a pasta converted"
    print("CLI (confirma, responde n): ok")

    pasta2 = os.path.join(tmp, "cli_s")
    os.makedirs(pasta2)
    gerar_mov(os.path.join(pasta2, "c.MOV"))
    r = subprocess.run(
        [sys.executable, CLI, pasta2, "-s"], capture_output=True, text=True, timeout=180
    )
    assert r.returncode == 0, r.stderr
    assert os.path.isfile(os.path.join(pasta2, "converted", "c.mp4"))
    assert not os.path.exists(os.path.join(pasta2, "c.MOV")), "-s deleta"
    print("CLI (-s deleta verificados): ok")


def _esperar(app, limite_seg=180):
    inicio = time.time()
    while not app.terminou:
        if time.time() - inicio > limite_seg:
            raise TimeoutError("GUI não terminou no tempo limite")
        app.update()
        time.sleep(0.02)
    app.update()


def teste_gui(tmp):
    import gui  # requer DISPLAY (xvfb-run) — gui.py importa tkinter no topo

    gui.messagebox.askyesno = lambda *a, **k: False  # nunca deleta nos testes

    pasta = os.path.join(tmp, "gui")
    os.makedirs(pasta)
    for n in ("x", "y"):
        gerar_mov(os.path.join(pasta, f"{n}.MOV"))

    app = gui.Aplicacao()
    app.update()
    app.iniciar_pasta(pasta)
    _esperar(app)
    assert os.path.isfile(os.path.join(pasta, "converted", "x.mp4"))
    assert os.path.isfile(os.path.join(pasta, "converted", "y.mp4"))
    assert os.path.isfile(os.path.join(pasta, "x.MOV")), "sem deletar"
    app.destroy()
    print("GUI fluxo pasta (barras + volta ao início): ok")

    # arquivo único: diálogo de salvar trocado pelo caminho padrão converted/
    destino = os.path.join(pasta, "converted", "x.mp4")
    gui.filedialog.asksaveasfilename = lambda **k: destino
    app = gui.Aplicacao()
    app.update()
    app.iniciar_arquivo(os.path.join(pasta, "x.MOV"))
    _esperar(app)
    assert os.path.isfile(destino)
    assert os.path.isfile(os.path.join(pasta, "x.MOV")), "sem deletar"
    app.destroy()
    print("GUI fluxo arquivo único (pergunta salvar + volta ao início): ok")


def main():
    with tempfile.TemporaryDirectory(prefix="mov_converter_teste_") as tmp:
        teste_cli(tmp)
        teste_gui(tmp)
    print("SMOKE TEST OK")


if __name__ == "__main__":
    main()
