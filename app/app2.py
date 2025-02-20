from flask import Flask, render_template, request
import numpy as np

app = Flask(__name__)

def esquina_noroeste(supply, demand, cost_matrix):
    rows, cols = len(supply), len(demand)
    allocation = np.zeros((rows, cols))
    i, j = 0, 0
    while i < rows and j < cols:
        qty = min(supply[i], demand[j])
        allocation[i, j] = qty
        supply[i] -= qty
        demand[j] -= qty
        if supply[i] == 0:
            i += 1
        if demand[j] == 0:
            j += 1
    return allocation

def calcular_costo_total(allocation, cost_matrix):
    return np.sum(allocation * cost_matrix)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        filas = int(request.form.get("filas", 0)) + 1
        columnas = int(request.form.get("columnas", 0)) + 1
        return render_template("index2.html", filas=filas, columnas=columnas)
    return render_template("index2.html", filas=None, columnas=None)

@app.route("/resolver", methods=["POST"])
def resolver():
    metodo = request.form.get("metodo", "")
    filas = int(request.form.get("filas", 0))
    columnas = int(request.form.get("columnas", 0))

    if filas == 0 or columnas == 0:
        return "Error: No se han ingresado filas o columnas válidas."

    cost_matrix = np.zeros((filas - 1, columnas - 1))
    supply = np.zeros(filas - 1)
    demand = np.zeros(columnas - 1)

    for i in range(filas - 1):
        for j in range(columnas - 1):
            cost_matrix[i, j] = int(request.form.get(f"cost_{i}_{j}", 0))

    for i in range(filas - 1):
        supply[i] = int(request.form.get(f"supply_{i}", 0))

    for j in range(columnas - 1):
        demand[j] = int(request.form.get(f"demand_{j}", 0))

    if sum(supply) != sum(demand):
        return "El problema está desbalanceado. Se requiere agregar una variable ficticia."

    if metodo == "Esquina Noroeste":
        solucion = esquina_noroeste(supply.copy(), demand.copy(), cost_matrix)
        costo_total = calcular_costo_total(solucion, cost_matrix)
    else:
        return "Método no implementado aún."

    return render_template("resultado2.html", solucion=solucion, metodo=metodo, costo_total=costo_total)

if __name__ == "__main__":
    app.run(debug=True)
