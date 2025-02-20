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

def menor_costo(supply, demand, cost_matrix):
    supply = supply.copy()
    demand = demand.copy()
    allocation = np.zeros_like(cost_matrix)
    
    while np.any(supply > 0) and np.any(demand > 0):
        min_cost_index = np.unravel_index(np.argmin(np.where((supply[:, None] > 0) & (demand > 0), cost_matrix, np.inf)), cost_matrix.shape)
        i, j = min_cost_index
        qty = min(supply[i], demand[j])
        allocation[i, j] = qty
        supply[i] -= qty
        demand[j] -= qty
    
    return allocation

def aproximacion_vogel(supply, demand, cost_matrix):
    supply = supply.copy()
    demand = demand.copy()
    allocation = np.zeros_like(cost_matrix)
    
    while np.any(supply > 0) and np.any(demand > 0):
        penalty_rows = []
        penalty_cols = []
        
        # Cálculo de penalizaciones por fila
        for i in range(len(supply)):
            if supply[i] > 0:
                row = cost_matrix[i, :]
                row_valid = row[demand > 0]
                if len(row_valid) > 1:
                    sorted_row = np.sort(row_valid)
                    penalty_rows.append(sorted_row[1] - sorted_row[0])
                else:
                    penalty_rows.append(0)
            else:
                penalty_rows.append(-1)

        # Cálculo de penalizaciones por columna
        for j in range(len(demand)):
            if demand[j] > 0:
                col = cost_matrix[:, j]
                col_valid = col[supply > 0]
                if len(col_valid) > 1:
                    sorted_col = np.sort(col_valid)
                    penalty_cols.append(sorted_col[1] - sorted_col[0])
                else:
                    penalty_cols.append(0)
            else:
                penalty_cols.append(-1)
        
        # Determinar si la penalización más alta está en fila o columna
        max_penalty_row = np.max(penalty_rows)
        max_penalty_col = np.max(penalty_cols)

        if max_penalty_row >= max_penalty_col:
            i = np.argmax(penalty_rows)
            j = np.argmin(np.where(demand > 0, cost_matrix[i, :], np.inf))
        else:
            j = np.argmax(penalty_cols)
            i = np.argmin(np.where(supply > 0, cost_matrix[:, j], np.inf))

        qty = min(supply[i], demand[j])
        allocation[i, j] = qty
        supply[i] -= qty
        demand[j] -= qty

    return allocation

def calcular_costo_total(allocation, cost_matrix):
    return np.sum(allocation * cost_matrix)

def es_solucion_degenerada(allocation, filas, columnas):
    celdas_asignadas = np.count_nonzero(allocation)
    celdas_requeridas = filas + columnas - 1
    
    explicacion = f"🔎 <strong>Cálculo de degeneración:</strong><br>"
    explicacion += f"- Se asignaron <strong>{celdas_asignadas}</strong> celdas con valores distintos de cero.<br>"
    explicacion += f"- Según la regla: m + n - 1 = {filas} + {columnas} - 1 = <strong>{celdas_requeridas}</strong>.<br>"

    if celdas_asignadas < celdas_requeridas:
        explicacion += "<span style='color:red; font-weight:bold;'>❌ La solución es degenerada</span> porque el número de celdas asignadas es menor al mínimo requerido."
        return True, explicacion
    else:
        explicacion += "<span style='color:green; font-weight:bold;'>✅ La solución no es degenerada</span> porque cumple con el número mínimo de celdas asignadas."
        return False, explicacion

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
    elif metodo == "Menor Costo":
        solucion = menor_costo(supply.copy(), demand.copy(), cost_matrix)
    elif metodo == "Aproximación de Vogel":
        solucion = aproximacion_vogel(supply.copy(), demand.copy(), cost_matrix)
    else:
        return "Método no implementado."

    costo_total = calcular_costo_total(solucion, cost_matrix)
    degenerada, mensaje_degenerada = es_solucion_degenerada(solucion, filas - 1, columnas - 1)

    return render_template("resultado2.html", solucion=solucion, metodo=metodo, costo_total=costo_total, degenerada=mensaje_degenerada)

if __name__ == "__main__":
    app.run(debug=True)
