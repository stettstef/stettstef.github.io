import streamlit as st
import os
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import re
from faster_whisper import WhisperModel

# ===== CONFIG =====
FS = 16000
BASE_PATH = "./"

# ===== MODELO =====
@st.cache_resource
def carregar_modelo():
    return WhisperModel("small", device="cpu", compute_type="int8")

model = carregar_modelo()

# ===== FUNÇÕES =====

def gerar_nome_arquivo(autor, ano):
    return autor.lower().replace(" ", "") + ano + ".html"


def gravar_audio(duracao=10):
    st.write(f"Gravando por {duracao} segundos...")

    audio = sd.rec(int(duracao * FS), samplerate=FS, channels=1, dtype="int16")
    sd.wait()

    wav.write("gravacao.wav", FS, audio)
    st.success("Gravação finalizada!")


def transcrever_audio():
    segments, _ = model.transcribe("gravacao.wav", language="pt")

    texto = ""
    for seg in segments:
        texto += seg.text

    return texto.strip()


def adicionar_citacao(arquivo, autor, ano, texto):
    caminho = os.path.join(BASE_PATH, arquivo)

    bloco = f"""
<h3>{autor}</h3>

{texto} ({autor}, {ano}{f", p. {pagina}" if pagina else ""})
"""

    # cria arquivo se não existir
    if not os.path.exists(caminho):
        html_base = f"""<link href="css.css" rel="stylesheet" type="text/css" />

<div align="justify">

<h2 id="{arquivo}">{autor}, {ano}</h2>

{bloco}

</div>
"""
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html_base)
        return True  # página nova

    # adiciona no final
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    novo_conteudo = conteudo.replace("</div>", bloco + "\n</div>")

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)

    return False  # já existia


def atualizar_index(arquivo, autor, ano, categoria):
    with open("index.html", "r", encoding="utf-8") as f:
        linhas = f.readlines()

    # evita duplicação
    if any(arquivo in linha for linha in linhas):
        return

    nova_lista = []
    dentro_categoria = False
    inserido = False
    indentacao = ""

    for linha in linhas:
        if f">{categoria}</a>" in linha:
            dentro_categoria = True

        if dentro_categoria and "<ul" in linha:
            dentro_categoria = "UL"

        if dentro_categoria == "UL" and "<li>" in linha:
            indentacao = linha[:len(linha) - len(linha.lstrip())]

        if dentro_categoria == "UL" and "</ul>" in linha and not inserido:
            novo_item = f'{indentacao}<li><a href="#" data-page="{arquivo}">{autor}, {ano}</a></li>\n'
            nova_lista.append(novo_item)
            inserido = True
            dentro_categoria = False

        nova_lista.append(linha)

    with open("index.html", "w", encoding="utf-8") as f:
        f.writelines(nova_lista)
        
def corrigir_pontuacao(texto):

    replacements = {

    r"\bvírgula\b": ",",
    r"\bponto final\b": ".",
    r"\bponto\b": ".",
    r"\bdois pontos\b": ":",
    r"\bponto e vírgula\b": ";",
    r"\bbarra\b": "/",

    # parênteses (abre/abrir)
    r"\babre?r?\s+par[eê]nteses\b": "(",
    r"\bfecha?r?\s+par[eê]nteses\b": ")",

    # aspas
    r"\babre?r?\s+aspas\b": '"',
    r"\bfecha?r?\s+aspas\b": '"',

    # itálico (muito mais tolerante)
    r"\babre?r?\s*it[aá]lico\b": "<i>",
    r"\b(abri|abre|abrir)\s*it[aá]lico\b": "<i>",
    r"\bfecha?r?\s*it[aá]lico\b": "</i>",
    r"\b(feche|fecha|fechar)\s*it[aá]lico\b": "</i>",
}

    for padrao, substituto in replacements.items():
        texto = re.sub(padrao, substituto, texto, flags=re.IGNORECASE)

    # remover vírgulas duplicadas
    texto = re.sub(r",+", ",", texto)

    # remover ponto duplicado
    texto = re.sub(r"\.+", ".", texto)

    # remover vírgula antes de ponto
    texto = re.sub(r",\.", ".", texto)

    # remover espaços antes de pontuação
    texto = re.sub(r"\s+([,.;:])", r"\1", texto)

    # remover espaço depois de <i>
    texto = re.sub(r"<i>\s+", "<i>", texto)

    # remover espaço antes de </i>
    texto = re.sub(r"\s+</i>", "</i>", texto)

    # normalizar múltiplos espaços
    texto = re.sub(r"\s{2,}", " ", texto)
    
    texto = re.sub(r",\s*</i>", "</i>", texto)

    # corrigir parêntese duplicado ou invertido
    texto = re.sub(r"\(\s*\)", "", texto)
    texto = re.sub(r",\s*\)", ")", texto)
    
    # remover vírgula duplicada
    texto = re.sub(r",+", ",", texto)

    # remover vírgula antes de abrir parêntese
    texto = re.sub(r",\s*\(", " (", texto)

    # remover espaço depois de "("
    texto = re.sub(r"\(\s+", "(", texto)

    # remover espaço antes de ")"
    texto = re.sub(r"\s+\)", ")", texto)
    
    texto = re.sub(r"abrit[aá]lico", "<i>", texto, flags=re.IGNORECASE)
    texto = re.sub(r"feche?\s*it[aá]lico", "</i>", texto, flags=re.IGNORECASE)

    return texto.strip()


# ===== INTERFACE =====

st.title("Stef's Second Brain")

autor = st.text_input("Autor").upper()
ano = st.text_input("Ano")
pagina = st.text_input("Página (opcional)")

categoria = st.selectbox("Categoria", [
    "ZUMBIS", "WHITE GAZE", "CIÊNCIA", "HORROR", "HAITI", "REL. INTERN.", "ONTOLOGIA", "FUNGOS", "APOCALIPSE", "ÉTICA AMBIENTAL", "COLONIALISMO", "PÓS-HUMANISMO", "BIOLOGIA", "ANTROPOCENO", "CINEMA", "LINGUAGEM", "PSICANÁLISE", "FICÇÃO", "ESTUDOS CULTURAIS", "CRIP/QUEER/AFROFUTURISMO", "ESPECTROLOGIA", "ANTROPOLOGIA", "BASE TEÓRICA"
])

if autor and ano:
    nome_arquivo = gerar_nome_arquivo(autor, ano)
    st.write(f"📄 Página: {nome_arquivo}")

# ===== GRAVAÇÃO =====

audio_file = st.audio_input("🎙 Grave sua citação")

if audio_file:
    with open("gravacao.wav", "wb") as f:
        f.write(audio_file.read())

    texto = transcrever_audio()
    texto = corrigir_pontuacao(texto)

    st.session_state["texto"] = texto

# ===== EDIÇÃO E SALVAR =====

if "texto" in st.session_state:
    texto_editado = st.text_area(
        "Transcrição",
        st.session_state["texto"],
        height=200
    )

    if st.button("💾 Salvar citação"):
        pagina_nova = adicionar_citacao(
            nome_arquivo,
            autor,
            ano,
            texto_editado
        )

        # só atualiza index se for página nova
        if pagina_nova:
            atualizar_index(nome_arquivo, autor, ano, categoria)

        st.success("Citação salva!")

        # limpa para próxima
        st.session_state.pop("texto")