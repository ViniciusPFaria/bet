from flask import Flask, render_template, request, jsonify
import csv
import random
import os

app = Flask(__name__)
CSV_FILE = "cadastros.csv"

# Criar o arquivo CSV se não existir
def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Nome", "Empresa", "Função", "Segmento", "Email"])  # Cabeçalhos

# Inicializa o arquivo CSV ao iniciar o servidor
init_csv()

# Página de cadastro
@app.route("/")
def cadastro():
    return render_template("cadastro.html")

# Endpoint para cadastrar participantes
@app.route("/api/cadastro", methods=["POST"])
def cadastrar():
    data = request.json
    nome = data["nome"]
    empresa = data["empresa"]
    funcao = data["funcao"]
    segmento = data["segmento"]
    email = data["email"]

    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([nome, empresa, funcao, segmento, email])

    return jsonify({"success": True})

# Página de confirmação
@app.route("/confirmacao")
def confirmacao():
    return render_template("confirmacao.html")

# Rota para sortear um vencedor
@app.route("/sorteio")
def sorteio():
    with open(CSV_FILE, mode="r") as file:
        reader = csv.reader(file)
        next(reader)  # Pular cabeçalho
        participantes = [row[0] for row in reader]  # Pegando apenas os nomes

    vencedor = random.choice(participantes) if participantes else "Nenhum participante cadastrado"

    return render_template("vencedor.html", vencedor=vencedor)

# Página do vencedor
@app.route("/vencedor")
def vencedor():
    return render_template("vencedor.html", vencedor="Aguardando sorteio")

if __name__ == "__main__":
    app.run(debug=True)
