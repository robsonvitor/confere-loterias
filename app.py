#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sqlite3
from datetime import datetime


def inicializar_banco():
    conn = sqlite3.connect(settings['database']['file'])
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS apostas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo TEXT,
                        numeros TEXT,
                        concurso_inicial INTEGER,
                        concurso_final INTEGER
                     )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resultados (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        concurso INTEGER UNIQUE,
                        tipo TEXT,
                        numeros_sorteados TEXT,
                        acertos INTEGER,
                        premiado INTEGER,
                        premio_total REAL,
                        data_concurso TEXT,
                        data_proximo_concurso TEXT
                     )''')
    conn.commit()
    conn.close()

def obter_resultado(concurso, loteria):
    url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{loteria}/{concurso}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API da Caixa: {e}")
        return None
    
    try:
        dados = response.json()
        return {
            "numeros_sorteados": dados.get("listaDezenas", []),
            "numero_concurso_proximo": dados.get("numeroConcursoProximo"),
            "data_proximo_concurso": dados.get("dataProximoConcurso"),
            "rateios": dados.get("listaRateioPremio", []),
            "data_concurso": dados.get("dataApuracao")
        }
    except json.JSONDecodeError:
        if settings["env"]["DEBUG"]:
            print("Erro ao processar a resposta da API da Caixa.")
        return None

def conferir_aposta(numeros_apostados, numeros_sorteados):
    acertos = set(numeros_apostados) & set(numeros_sorteados)
    if settings["env"]["DEBUG"]:
        print(f"Números sorteados: {numeros_sorteados}")
        print(f"Seus acertos: {sorted(acertos)} ({len(acertos)} acertos)")
    return len(acertos)

def calcular_premio(rateios, acertos):
    for rateio in rateios:
        if rateio.get("descricaoFaixa").startswith(f"{acertos} acertos"):
            ganhadores = rateio.get("numeroDeGanhadores", 0)
            premio_total = rateio.get("valorPremio", 0.0)
            return ganhadores, premio_total
    return 0, 0.0

def enviar_telegram(mensagem):
    token = settings['telegram']['token']
    chat_id = settings['telegram']['chat_id']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": mensagem})

def carregar_settings():
    try:
        with open("settings.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def obter_apostas():
    conn = sqlite3.connect("loteria.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo, numeros, concurso_inicial, concurso_final FROM apostas")
    apostas = cursor.fetchall()
    conn.close()
    return apostas

def salvar_resultado(concurso, tipo, numeros_sorteados, acertos, premiado, premio_total, data_concurso, data_proximo_concurso):
    conn = sqlite3.connect("loteria.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO resultados (concurso, tipo, numeros_sorteados, acertos, premiado, premio_total, data_concurso, data_proximo_concurso)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (concurso, tipo, ",".join(numeros_sorteados), acertos, premiado, premio_total, data_concurso, data_proximo_concurso))
    conn.commit()
    conn.close()

def obter_data_proximo_concurso(tipo):
    conn = sqlite3.connect("loteria.db")
    cursor = conn.cursor()
    cursor.execute("SELECT data_proximo_concurso FROM resultados WHERE tipo = ? ORDER BY concurso DESC LIMIT 1", (tipo,))
    resultado = cursor.fetchone()
    conn.close()
    return datetime.strptime(resultado[0], "%d/%m/%Y").replace(hour=22, minute=0, second=0, microsecond=0) if resultado and resultado[0] else None

def ja_verificado(concurso):
    conn = sqlite3.connect("loteria.db")
    cursor = conn.cursor()
    cursor.execute("SELECT concurso FROM resultados WHERE concurso = ?", (concurso,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

if __name__ == "__main__":
    settings = carregar_settings()
    inicializar_banco()
    apostas = obter_apostas()
    hoje = datetime.now().strftime("%d/%m/%Y")
    loop = 0

    for aposta in apostas:
        aposta_id, tipo, numeros, concurso_inicial, concurso_final = aposta
        numeros_apostados = numeros.split(",")
        concurso_atual = concurso_inicial      
        

        while concurso_atual <= concurso_final:
                       
            if ja_verificado(concurso_atual):
                if settings["env"]["DEBUG"]:
                    print(f"Concurso {concurso_atual} da {tipo.upper()} já verificado. Pulando...")
                concurso_atual += 1
                continue

            data_hoje = datetime.today()
            data_proximo_concurso = obter_data_proximo_concurso(tipo)

            if  data_proximo_concurso is None or data_proximo_concurso <= data_hoje:
                dados_concurso = obter_resultado(concurso_atual, tipo.lower())
                if not dados_concurso:
                    break
                
                if not dados_concurso["numeros_sorteados"]:
                    print(f"Resultado do concurso {concurso_atual} ainda não disponível. Aguardando...")
                    break
                
                acertos = conferir_aposta(numeros_apostados, dados_concurso["numeros_sorteados"])
                ganhadores, premio_total = calcular_premio(dados_concurso["rateios"], acertos)
                premiado = 1 if acertos >= 11 else 0
                salvar_resultado(concurso_atual, tipo, dados_concurso["numeros_sorteados"], acertos, premiado, premio_total, dados_concurso["data_concurso"], dados_concurso["data_proximo_concurso"])
                
                if acertos >= 11:
                    mensagem = (f"Você acertou {acertos} números no concurso {concurso_atual}!")
                    if ganhadores > 0:
                        mensagem += f"\nNúmero de ganhadores: {ganhadores}\nValor do prêmio: R$ {premio_total:.2f}"
                    enviar_telegram(mensagem)
                    print("Mensagem enviada para o Telegram.")
                
                concurso_atual += 1
            else:
                # print(f"Data do próximo concurso: {data_proximo_concurso}, Hoje: {data_hoje}, Proximo concurso: {concurso_atual}")
                # print(f"Concurso {concurso_atual} ainda não ocorreu. Aguardando...")
                break
    
