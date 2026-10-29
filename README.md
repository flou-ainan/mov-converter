# 🎬 MOV Converter

CLI para converter em lote todos os vídeos `.MOV` (iPhone) de uma pasta para `.MP4` (HEVC), com verificação automática de integridade. Feito para rodar em **qualquer pasta**, sem precisar copiar script nenhum.

---

## 🎯 Objetivo

- Converter todos os `.MOV` de uma pasta para `.MP4` com um único comando.
- Preservar qualidade máxima: HEVC 10 bits, HDR e informações de cor do iPhone.
- Corrigir o framerate **variável** do iPhone para framerate **constante**.
- Usar a GPU NVIDIA (NVENC) quando disponível, com fallback automático para CPU.
- Verificar cada arquivo convertido (abre, duração igual, sem corrupção) antes de aceitar.

---

## 🛠️ Requisitos

- Python 3.8+
- `ffmpeg` e `ffprobe` no PATH
- (Opcional) GPU NVIDIA com NVENC — usado automaticamente se disponível

---

## 🚀 Instalação

```bash
git clone <repo> ~/mov-converter
chmod +x ~/mov-converter/converter_mov.py
ln -sf ~/mov-converter/converter_mov.py ~/.local/bin/converter-mov
```

---

## 💻 Uso

```bash
converter-mov                  # converte os .MOV da pasta atual
converter-mov /caminho/pasta   # converte os .MOV da pasta indicada
converter-mov -s               # deleta os .MOV já convertidos sem perguntar
converter-mov --help           # ajuda
```

Os `.MP4` resultantes ficam na subpasta `convertidos/` dentro da pasta processada.

---

## ⚙️ Como funciona

1. Lista todos os `.MOV` da pasta (ordem alfabética).
2. Detecta GPU NVIDIA (teste real de NVENC + decodificação CUDA).
3. Para cada arquivo:
   - Lê fps médio, bits de cor, HDR e codec de áudio via `ffprobe`.
   - Converte com fallback automático: GPU+CUDA → NVENC → CPU (libx265).
   - Framerate convertido para constante (23.976/29.97/59.94 em frações exatas).
   - Áudio AAC é copiado sem perda; outros codecs são reencodados em 256k.
4. Verifica cada `.mp4`: abre, tem vídeo, duração igual e decodifica início/fim.
5. Pergunta se deseja deletar os `.MOV` originais (apaga só os verificados com OK).

Erros (se houver) ficam em `converter_error_log.txt` na pasta processada, com detalhes do comando FFMPEG e saída de erro.

---

## 📁 Estrutura

```
mov-converter/
├── converter_mov.py   # o programa
├── README.md
└── .gitignore
```
