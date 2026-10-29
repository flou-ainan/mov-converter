#!/usr/bin/env python3
"""
Converte todos os vídeos .MOV da pasta atual (ou de uma pasta indicada)
para .MP4 na subpasta "convertidos", usando FFMPEG.

Uso:
    converter-mov                # converte os .MOV da pasta atual
    converter-mov /caminho/pasta # converte os .MOV da pasta indicada
    converter-mov -s             # não pergunta antes de deletar os .MOV ok

- Usa a GPU NVIDIA (NVENC, codec HEVC) quando disponível; senão usa a CPU.
- Mantém a qualidade (alta qualidade constante, 10 bits/HDR preservado).
- Saída com framerate CONSTANTE (o iPhone grava com framerate variável).
"""

import argparse
import datetime
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import traceback

LARGURA_BARRA = 30

# Qualidade: quanto MENOR, melhor (e maior o arquivo). 18-20 é visualmente idêntico.
QUALIDADE_GPU = 19   # -cq do NVENC
QUALIDADE_CPU = 18   # -crf do libx265

FPS_PADRAO = [23.976, 24, 25, 29.97, 30, 48, 50, 59.94, 60, 120, 240]

PASTA = ""
SAIDA = ""
LOG = ""
_log_iniciado = False


# ---------------------------------------------------------------- log de erros

def registrar_erro(titulo, detalhes=""):
    """Acrescenta um erro ao converter_error_log.txt (criado só se houver erro).
    A cada execução, o primeiro erro grava um cabeçalho com dados do sistema."""
    global _log_iniciado
    try:
        with open(LOG, "a", encoding="utf-8") as log:
            if not _log_iniciado:
                _log_iniciado = True
                versao = subprocess.run(["ffmpeg", "-version"],
                                        capture_output=True, text=True)
                gpu = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,driver_version",
                     "--format=csv,noheader"], capture_output=True, text=True) \
                    if shutil.which("nvidia-smi") else None
                log.write("=" * 70 + "\n")
                log.write(f"Execução: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")
                log.write(f"Pasta:    {PASTA}\n")
                log.write(f"Sistema:  {platform.platform()} | Python {platform.python_version()}\n")
                log.write(f"FFMPEG:   {(versao.stdout.splitlines() or ['?'])[0]}\n")
                log.write(f"GPU:      {gpu.stdout.strip() if gpu and gpu.returncode == 0 else 'nvidia-smi indisponível'}\n")
                log.write("=" * 70 + "\n")
            log.write(f"\n[{datetime.datetime.now():%H:%M:%S}] {titulo}\n")
            if detalhes:
                for linha in str(detalhes).rstrip().splitlines():
                    log.write(f"    {linha}\n")
    except OSError:
        pass  # sem permissão de escrita: não interrompe a conversão


# ---------------------------------------------------------------- utilidades

def ffprobe_json(arquivo):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", arquivo],
        capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def info_video(arquivo):
    """Duração, fps médio, se é 10 bits, cores e codec de áudio."""
    dados = ffprobe_json(arquivo)
    info = {"duracao": 0.0, "fps": 30.0, "dez_bits": False,
            "cores": {}, "audio": None}
    try:
        info["duracao"] = float(dados.get("format", {}).get("duration", 0))
    except ValueError:
        pass
    for s in dados.get("streams", []):
        if s.get("codec_type") == "video" and "fps_bruto" not in info:
            info["fps_bruto"] = s.get("avg_frame_rate", "0/0")
            num, _, den = info["fps_bruto"].partition("/")
            try:
                fps = float(num) / float(den or 1)
                if fps > 0:
                    info["fps"] = fps
            except (ValueError, ZeroDivisionError):
                pass
            pix = s.get("pix_fmt", "")
            info["dez_bits"] = "10" in pix or "12" in pix
            for chave in ("color_primaries", "color_transfer", "color_space"):
                valor = s.get(chave)
                if valor and valor != "unknown":
                    info["cores"][chave] = valor
        elif s.get("codec_type") == "audio" and info["audio"] is None:
            info["audio"] = s.get("codec_name")
    return info


def fps_constante(fps_medio):
    """Arredonda o fps médio (variável) para o padrão mais próximo."""
    mais_proximo = min(FPS_PADRAO, key=lambda p: abs(p - fps_medio))
    if abs(mais_proximo - fps_medio) / mais_proximo < 0.03:
        fps = mais_proximo
    else:
        fps = round(fps_medio, 3)
    # Frações exatas para 23.976 / 29.97 / 59.94
    return {23.976: "24000/1001", 29.97: "30000/1001",
            59.94: "60000/1001"}.get(fps, str(fps))


def tem_nvenc():
    """Testa se o NVENC HEVC realmente funciona nesta máquina."""
    r = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
         "color=c=black:s=256x256:d=0.2", "-c:v", "hevc_nvenc",
         "-f", "null", "-"],
        capture_output=True, text=True)
    return r.returncode == 0


def tem_cuda_decode():
    r = subprocess.run(["ffmpeg", "-v", "error", "-hwaccels"],
                       capture_output=True, text=True)
    return "cuda" in r.stdout


# ---------------------------------------------------------------- tela

def barra(fracao, largura):
    fracao = max(0.0, min(1.0, fracao))
    cheio = int(largura * fracao)
    return "[" + "#" * cheio + "-" * (largura - cheio) + f"] {fracao * 100:3.0f}%"


class Painel:
    """Bloco fixo no rodapé: nome do arquivo atual, barra do arquivo e,
    sempre na última linha, a barra TOTAL. Mensagens (log) aparecem acima
    do bloco, que é redesenhado no lugar sem se repetir."""

    def __init__(self):
        self.linhas = 0          # quantas linhas o bloco ocupa agora na tela
        self.cabecalho = ""
        self.frac_arquivo = 0.0
        self.frac_total = 0.0
        self._ultimo = None

    def _apagar_bloco(self):
        if self.linhas:
            sobe = f"\033[{self.linhas - 1}A" if self.linhas > 1 else ""
            sys.stdout.write(f"{sobe}\r\033[J")   # volta ao topo e limpa
            self.linhas = 0

    def _desenhar(self):
        colunas = shutil.get_terminal_size((80, 20)).columns
        largura = max(5, min(LARGURA_BARRA, colunas - 20))
        linhas = [self.cabecalho,
                  f"  Arquivo {barra(self.frac_arquivo, largura)}",
                  f"  Total   {barra(self.frac_total, largura)}"]
        # corta cada linha na largura do terminal para nunca quebrar
        sys.stdout.write("\n".join(l[:colunas - 1] for l in linhas))
        sys.stdout.flush()
        self.linhas = len(linhas)

    def novo_arquivo(self, cabecalho):
        self.cabecalho = cabecalho[:300]
        self.frac_arquivo = 0.0
        self._ultimo = None
        self.atualizar(0.0, self.frac_total)

    def atualizar(self, frac_arquivo, frac_total):
        estado = (int(frac_arquivo * 1000), int(frac_total * 1000))
        if estado == self._ultimo:
            return
        self._ultimo = estado
        self.frac_arquivo, self.frac_total = frac_arquivo, frac_total
        self._apagar_bloco()
        self._desenhar()

    def log(self, mensagem):
        """Escreve uma mensagem acima do bloco e redesenha o bloco embaixo."""
        self._apagar_bloco()
        sys.stdout.write(mensagem + "\n")
        self._desenhar()

    def finalizar(self, mensagem):
        """Remove o bloco e deixa só a mensagem final e a barra total."""
        self._apagar_bloco()
        colunas = shutil.get_terminal_size((80, 20)).columns
        largura = max(5, min(LARGURA_BARRA, colunas - 20))
        sys.stdout.write(mensagem + "\n")
        sys.stdout.write(f"  Total   {barra(self.frac_total, largura)}"[:colunas - 1] + "\n")
        sys.stdout.flush()


painel = Painel()


# ---------------------------------------------------------------- conversão

def montar_comando(entrada, saida, info, usar_gpu, decodificar_gpu):
    fps = fps_constante(info["fps"])
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error"]
    if decodificar_gpu:
        cmd += ["-hwaccel", "cuda"]
    cmd += ["-i", entrada, "-map", "0:v:0", "-map", "0:a?",
            "-vf", f"fps={fps}", "-r", fps]

    if usar_gpu:
        cmd += ["-c:v", "hevc_nvenc", "-preset", "p7", "-tune", "hq",
                "-rc", "vbr", "-cq", str(QUALIDADE_GPU), "-b:v", "0",
                "-spatial-aq", "1", "-temporal-aq", "1",
                "-rc-lookahead", "32"]
        if info["dez_bits"]:
            cmd += ["-profile:v", "main10", "-pix_fmt", "p010le"]
        else:
            cmd += ["-profile:v", "main", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "libx265", "-crf", str(QUALIDADE_CPU),
                "-preset", "medium", "-x265-params", "log-level=error",
                "-pix_fmt", "yuv420p10le" if info["dez_bits"] else "yuv420p"]

    # Preserva informações de cor (importante para vídeos HDR do iPhone)
    mapa = {"color_primaries": "-color_primaries",
            "color_transfer": "-color_trc",
            "color_space": "-colorspace"}
    for chave, opcao in mapa.items():
        if chave in info["cores"]:
            cmd += [opcao, info["cores"][chave]]

    # Áudio: copia sem perda se já for AAC, senão converte em alta qualidade
    if info["audio"] == "aac":
        cmd += ["-c:a", "copy"]
    else:
        cmd += ["-c:a", "aac", "-b:a", "256k"]

    cmd += ["-tag:v", "hvc1", "-map_metadata", "0",
            "-movflags", "+faststart",
            "-progress", "pipe:1", "-nostats", saida]
    return cmd


def executar(cmd, nome, dur, feito_antes, dur_total):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    for linha in proc.stdout:
        if linha.startswith(("out_time_us=", "out_time_ms=")):
            try:
                seg = int(linha.split("=")[1]) / 1_000_000
            except ValueError:
                continue
            frac = seg / dur if dur else 0
            total = (feito_antes + min(seg, dur)) / dur_total if dur_total else 0
            painel.atualizar(frac, total)
    erro = proc.stderr.read()
    proc.wait()
    return proc.returncode == 0, erro.strip()


def converter(entrada, saida, nome, info, feito_antes, dur_total, gpu, cuda):
    tentativas = []
    if gpu and cuda:
        tentativas.append((True, True))    # decodifica e codifica na GPU
    if gpu:
        tentativas.append((True, False))   # só codifica na GPU
    tentativas.append((False, False))      # CPU (último recurso)

    erro = ""
    for n, (usar_gpu, dec_gpu) in enumerate(tentativas, 1):
        cmd = montar_comando(entrada, saida, info, usar_gpu, dec_gpu)
        ok, erro = executar(cmd, nome, info["duracao"], feito_antes, dur_total)
        if ok:
            return True, ""
        modo = ("GPU (decodificação CUDA + NVENC)" if dec_gpu else
                "GPU (NVENC)" if usar_gpu else "CPU (libx265)")
        ultima = n == len(tentativas)
        registrar_erro(
            f"{nome}: tentativa {n}/{len(tentativas)} falhou - {modo}"
            + ("" if ultima else " (tentando o próximo modo)"),
            f"Info do original: {info}\n"
            f"Comando: {shlex.join(cmd)}\n"
            f"Saída de erro do FFMPEG:\n{erro or '(vazia)'}")
    return False, erro


# ---------------------------------------------------------------- verificação

def verificar(original, convertido):
    """Checa se o .mp4 abre, tem vídeo, duração igual e framerate constante."""
    if not os.path.isfile(convertido) or os.path.getsize(convertido) == 0:
        return False, "arquivo não existe ou está vazio"
    dados = ffprobe_json(convertido)
    video = [s for s in dados.get("streams", []) if s.get("codec_type") == "video"]
    if not video:
        return False, "sem trilha de vídeo legível"

    d_orig = info_video(original)["duracao"]
    try:
        d_conv = float(dados.get("format", {}).get("duration", 0))
    except ValueError:
        d_conv = 0
    if d_orig and abs(d_orig - d_conv) > 1.0:
        return False, f"duração diferente ({d_orig:.1f}s x {d_conv:.1f}s)"

    # Decodifica um trecho do início e do fim para detectar corrupção
    for inicio in ("0", str(max(0.0, d_conv - 2))):
        r = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-ss", inicio, "-t", "2",
             "-i", convertido, "-f", "null", "-"],
            capture_output=True, text=True)
        if r.returncode != 0 or r.stderr.strip():
            return False, (f"erro ao decodificar o vídeo (a partir de {inicio}s)",
                           r.stderr.strip())

    fps = video[0].get("avg_frame_rate")
    cfr = fps == video[0].get("r_frame_rate")
    return True, f"ok ({video[0].get('codec_name')}, " \
                 f"{'framerate constante' if cfr else 'fps ' + str(fps)})"


def perguntar_sim_nao(pergunta):
    while True:
        resp = input(pergunta).strip().lower()
        if resp in ("sim", "s"):
            return True
        if resp in ("não", "nao", "n"):
            return False
        print("  Resposta inválida. Digite SIM ou NÃO.")


# ---------------------------------------------------------------- principal

def main():
    global PASTA, SAIDA, LOG

    parser = argparse.ArgumentParser(
        prog="converter-mov",
        description="Converte todos os .MOV da pasta para .MP4 "
                    "(HEVC, GPU quando disponível) na subpasta 'convertidos'.")
    parser.add_argument("pasta", nargs="?", default=os.getcwd(),
                        help="pasta com os arquivos .MOV (padrão: pasta atual)")
    parser.add_argument("-s", "--sim", action="store_true",
                        help="deleta os .MOV convertidos sem perguntar")
    args = parser.parse_args()

    PASTA = os.path.abspath(os.path.expanduser(args.pasta))
    if not os.path.isdir(PASTA):
        print(f"Pasta não encontrada: {PASTA}")
        sys.exit(1)
    SAIDA = os.path.join(PASTA, "convertidos")
    LOG = os.path.join(PASTA, "converter_error_log.txt")

    arquivos = sorted(f for f in os.listdir(PASTA)
                      if f.lower().endswith(".mov")
                      and os.path.isfile(os.path.join(PASTA, f)))

    if not arquivos:
        print(f"Nenhum arquivo .MOV encontrado em: {PASTA}")
        return

    print(f"Pasta: {PASTA}\n")
    print("Arquivos .MOV encontrados:")
    for f in arquivos:
        print(f"  - {f}")
    print(f"\nTotal: {len(arquivos)} arquivo(s)\n")

    gpu = tem_nvenc()
    cuda = gpu and tem_cuda_decode()
    if gpu:
        print("GPU NVIDIA detectada: usando NVENC (HEVC)"
              + (" + decodificação CUDA." if cuda else "."))
    else:
        print("GPU NVIDIA não disponível no FFMPEG: usando a CPU (mais lento).")
    print()

    os.makedirs(SAIDA, exist_ok=True)

    infos = {f: info_video(os.path.join(PASTA, f)) for f in arquivos}
    dur_total = sum(i["duracao"] for i in infos.values()) or 1
    feito = 0.0
    falhas = []

    for i, f in enumerate(arquivos, 1):
        entrada = os.path.join(PASTA, f)
        saida = os.path.join(SAIDA, os.path.splitext(f)[0] + ".mp4")
        info = infos[f]
        painel.novo_arquivo(
            f"({i}/{len(arquivos)}) {f}  [{info['fps']:.2f} fps -> "
            f"{fps_constante(info['fps'])}{', 10 bits' if info['dez_bits'] else ''}]")
        ok, erro = converter(entrada, saida, f, info, feito, dur_total, gpu, cuda)
        feito += info["duracao"]
        painel.frac_total = feito / dur_total
        if ok:
            painel.log(f"  OK    ({i}/{len(arquivos)}) {f} -> convertidos/{os.path.basename(saida)}")
        else:
            painel.log(f"  ERRO  ({i}/{len(arquivos)}) {f}: {erro or 'desconhecido'}")
            falhas.append(f)

    painel.finalizar("\nConversão concluída.")
    print()

    print("Verificando arquivos convertidos...")
    verificados = []
    for f in arquivos:
        if f in falhas:
            continue
        convertido = os.path.join(SAIDA, os.path.splitext(f)[0] + ".mp4")
        ok, msg = verificar(os.path.join(PASTA, f), convertido)
        detalhe = ""
        if isinstance(msg, tuple):
            msg, detalhe = msg
        print(f"  {'OK   ' if ok else 'FALHA'} {f} -> {msg}")
        if ok:
            verificados.append(f)
        else:
            falhas.append(f)
            registrar_erro(f"{f}: falhou na verificação - {msg}",
                           f"Arquivo convertido: {convertido}\n"
                           f"Original: {info_video(os.path.join(PASTA, f))}\n"
                           f"Convertido: {info_video(convertido)}\n{detalhe}")

    print(f"\n{len(verificados)} convertido(s) com sucesso, {len(falhas)} com problema.")
    if _log_iniciado:
        print(f"Detalhes dos erros em: {LOG}")

    if falhas:
        print("Arquivos com problema (não serão apagados):")
        for f in falhas:
            print(f"  - {f}")

    if not verificados:
        return

    print()
    deletar = args.sim or perguntar_sim_nao(
        f"Deletar os {len(verificados)} arquivo(s) .MOV "
        "convertidos com sucesso? (SIM/NÃO): ")
    if deletar:
        for f in verificados:
            os.remove(os.path.join(PASTA, f))
        print("Arquivos .MOV deletados.")
    else:
        print("Nenhum arquivo foi deletado.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelado pelo usuário.")
    except Exception:
        registrar_erro("Erro inesperado no script", traceback.format_exc())
        print(f"\nErro inesperado. Detalhes em: {LOG}")
        sys.exit(1)
