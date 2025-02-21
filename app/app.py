from flask import Flask, render_template, request, send_file
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

def simplex(c, A, b, tipo):
    """ Resuelve el problema de programación lineal usando el método Simplex """
    num_vars = len(c)
    num_restricciones = len(A)

    if tipo == "max":
        c = [-x for x in c]  # Convertimos a problema de minimización

    # Crear la tabla del método Simplex
    tabla = np.zeros((num_restricciones + 1, num_vars + num_restricciones + 1))
    
    # Llenar la tabla con restricciones
    for i in range(num_restricciones):
        tabla[i, :num_vars] = A[i]
        tabla[i, num_vars + i] = 1  # Variables de holgura
        tabla[i, -1] = b[i]

    # Agregar la función objetivo
    tabla[-1, :num_vars] = c
    pasos = []

    while True:
        pasos.append(tabla.copy().tolist())  # Guardamos copia de la tabla

        # Buscar la columna pivote (menor coeficiente en la fila de Z)
        col_pivote = np.argmin(tabla[-1, :-1])
        if tabla[-1, col_pivote] >= 0:
            break  # No hay más mejoras

        # Buscar la fila pivote (mínima razón positiva)
        ratios = []
        for i in range(num_restricciones):
            if tabla[i, col_pivote] > 0:
                ratios.append(tabla[i, -1] / tabla[i, col_pivote])
            else:
                ratios.append(np.inf)

        fila_pivote = np.argmin(ratios)
        if ratios[fila_pivote] == np.inf:
            return "Solución no acotada", None, None, None

        # Normalizar la fila pivote
        tabla[fila_pivote, :] /= tabla[fila_pivote, col_pivote]

        # Hacer ceros en la columna pivote
        for i in range(num_restricciones + 1):
            if i != fila_pivote:
                tabla[i, :] -= tabla[i, col_pivote] * tabla[fila_pivote, :]

    pasos.append(tabla.copy().tolist())  # Guardamos la última tabla

    # Extraer la solución
    solucion = [0] * num_vars
    holguras = [0] * num_restricciones

    for i in range(num_vars):
        col = tabla[:-1, i]
        if sum(col == 1) == 1 and sum(col == 0) == num_restricciones - 1:
            fila = np.where(col == 1)[0][0]
            solucion[i] = tabla[fila, -1]

    for i in range(num_restricciones):
        col = tabla[:-1, num_vars + i]
        if sum(col == 1) == 1 and sum(col == 0) == num_restricciones - 1:
            fila = np.where(col == 1)[0][0]
            holguras[i] = tabla[fila, -1]

    valor_optimo = round(tabla[-1, -1] if tipo == "max" else -tabla[-1, -1], 2)
    
    return valor_optimo, solucion, holguras, pasos

def gran_m(c, A, b, tipo):
    """ Resuelve el problema de programación lineal usando el método de la Gran M """
    num_vars = len(c)
    num_restricciones = len(A)

    if tipo == "max":
        c = [-x for x in c]  # Convertimos a problema de minimización

    # Crear la tabla del método Simplex con variables artificiales
    tabla = np.zeros((num_restricciones + 1, num_vars + num_restricciones + 1))
    
    # Llenar la tabla con restricciones
    for i in range(num_restricciones):
        tabla[i, :num_vars] = A[i]
        tabla[i, num_vars + i] = 1  # Variables de holgura
        tabla[i, -1] = b[i]

    # Agregar la función objetivo con penalización M
    M = 1000000  # Valor grande para M
    tabla[-1, :num_vars] = c
    for i in range(num_restricciones):
        if b[i] < 0:
            tabla[-1, num_vars + i] = M

    pasos = []

    while True:
        pasos.append(tabla.copy().tolist())  # Guardamos copia de la tabla

        # Buscar la columna pivote (menor coeficiente en la fila de Z)
        col_pivote = np.argmin(tabla[-1, :-1])
        if tabla[-1, col_pivote] >= 0:
            break  # No hay más mejoras

        # Buscar la fila pivote (mínima razón positiva)
        ratios = []
        for i in range(num_restricciones):
            if tabla[i, col_pivote] > 0:
                ratios.append(tabla[i, -1] / tabla[i, col_pivote])
            else:
                ratios.append(np.inf)

        fila_pivote = np.argmin(ratios)
        if ratios[fila_pivote] == np.inf:
            return "Solución no acotada", None, None, None

        # Normalizar la fila pivote
        tabla[fila_pivote, :] /= tabla[fila_pivote, col_pivote]

        # Hacer ceros en la columna pivote
        for i in range(num_restricciones + 1):
            if i != fila_pivote:
                tabla[i, :] -= tabla[i, col_pivote] * tabla[fila_pivote, :]

    pasos.append(tabla.copy().tolist())  # Guardamos la última tabla

    # Extraer la solución
    solucion = [0] * num_vars
    holguras = [0] * num_restricciones

    for i in range(num_vars):
        col = tabla[:-1, i]
        if sum(col == 1) == 1 and sum(col == 0) == num_restricciones - 1:
            fila = np.where(col == 1)[0][0]
            solucion[i] = tabla[fila, -1]

    for i in range(num_restricciones):
        col = tabla[:-1, num_vars + i]
        if sum(col == 1) == 1 and sum(col == 0) == num_restricciones - 1:
            fila = np.where(col == 1)[0][0]
            holguras[i] = tabla[fila, -1]

    valor_optimo = round(tabla[-1, -1] if tipo == "max" else -tabla[-1, -1], 2)
    
    return valor_optimo, solucion, holguras, pasos

def dos_fases(c, A, b, tipo):
    """ Resuelve el problema de programación lineal usando el método de Dos Fases """
    num_vars = len(c)
    num_restricciones = len(A)

    if tipo == "max":
        c = [-x for x in c]  # Convertimos a problema de minimización

    # Fase 1: Minimizar la suma de variables artificiales
    c_fase1 = [0] * num_vars + [1] * num_restricciones
    A_fase1 = [fila + [1 if i == j else 0 for j in range(num_restricciones)] for i, fila in enumerate(A)]
    b_fase1 = b

    valor_optimo_fase1, solucion_fase1, holguras_fase1, pasos_fase1 = simplex(c_fase1, A_fase1, b_fase1, "min")

    if valor_optimo_fase1 != 0:
        return "No existe solución factible", None, None, None

    # Fase 2: Resolver el problema original sin variables artificiales
    tabla_fase2 = np.zeros((num_restricciones + 1, num_vars + num_restricciones + 1))
    
    for i in range(num_restricciones):
        tabla_fase2[i, :num_vars] = A[i]
        tabla_fase2[i, num_vars + i] = 1  # Variables de holgura
        tabla_fase2[i, -1] = b[i]

    tabla_fase2[-1, :num_vars] = c
    pasos_fase2 = []

    while True:
        pasos_fase2.append(tabla_fase2.copy().tolist())  # Guardamos copia de la tabla

        # Buscar la columna pivote (menor coeficiente en la fila de Z)
        col_pivote = np.argmin(tabla_fase2[-1, :-1])
        if tabla_fase2[-1, col_pivote] >= 0:
            break  # No hay más mejoras

        # Buscar la fila pivote (mínima razón positiva)
        ratios = []
        for i in range(num_restricciones):
            if tabla_fase2[i, col_pivote] > 0:
                ratios.append(tabla_fase2[i, -1] / tabla_fase2[i, col_pivote])
            else:
                ratios.append(np.inf)

        fila_pivote = np.argmin(ratios)
        if ratios[fila_pivote] == np.inf:
            return "Solución no acotada", None, None, None

        # Normalizar la fila pivote
        tabla_fase2[fila_pivote, :] /= tabla_fase2[fila_pivote, col_pivote]

        # Hacer ceros en la columna pivote
        for i in range(num_restricciones + 1):
            if i != fila_pivote:
                tabla_fase2[i, :] -= tabla_fase2[i, col_pivote] * tabla_fase2[fila_pivote, :]

    pasos_fase2.append(tabla_fase2.copy().tolist())  # Guardamos la última tabla

    # Extraer la solución
    solucion = [0] * num_vars
    holguras = [0] * num_restricciones

    for i in range(num_vars):
        col = tabla_fase2[:-1, i]
        if sum(col == 1) == 1 and sum(col == 0) == num_restricciones - 1:
            fila = np.where(col == 1)[0][0]
            solucion[i] = tabla_fase2[fila, -1]

    for i in range(num_restricciones):
        col = tabla_fase2[:-1, num_vars + i]
        if sum(col == 1) == 1 and sum(col == 0) == num_restricciones - 1:
            fila = np.where(col == 1)[0][0]
            holguras[i] = tabla_fase2[fila, -1]

    valor_optimo = round(tabla_fase2[-1, -1] if tipo == "max" else -tabla_fase2[-1, -1], 2)
    
    return valor_optimo, solucion, holguras, pasos_fase2

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resolver', methods=['POST'])
def resolver():
    try:
        tipo = request.form['tipo']
        num_variables = int(request.form['num_variables'])
        num_restricciones = int(request.form['num_restricciones'])
        metodo = request.form['metodo']

        c = [float(request.form[f'c{i}']) for i in range(num_variables)]
        A = []
        b = []

        for i in range(num_restricciones):
            restriccion = [float(request.form[f'a{i}_{j}']) for j in range(num_variables)]
            b_valor = float(request.form[f'b_{i}'])
            desigualdad = request.form[f'des_{i}']

            if desigualdad == ">=":
                restriccion = [-x for x in restriccion]
                b_valor = -b_valor

            A.append(restriccion)
            b.append(b_valor)

        if metodo == "simplex":
            resultado, solucion, holguras, pasos = simplex(c, A, b, tipo)
        elif metodo == "dos_fases":
            resultado, solucion, holguras, pasos = dos_fases(c, A, b, tipo)
        elif metodo == "gran_m":
            resultado, solucion, holguras, pasos = gran_m(c, A, b, tipo)
        else:
            return "Método no válido", 400

        return render_template('resultado.html', resultado=resultado, solucion=solucion, holguras=holguras, pasos=pasos, num_variables=num_variables, num_restricciones=num_restricciones)

    except Exception as e:
        return f"Error en la resolución: {e}"

@app.route('/descargar', methods=['POST'])
def descargar():
    try:
        tipo_archivo = request.form['tipo_archivo']
        resultado = request.form['resultado']
        solucion = request.form.getlist('solucion[]')
        holguras = request.form.getlist('holguras[]')
        pasos = request.form.getlist('pasos[]')
        num_variables = int(request.form['num_variables'])
        num_restricciones = int(request.form['num_restricciones'])

        if tipo_archivo == 'pdf':
            # Crear un archivo PDF en memoria
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawString(100, 750, "Resultado del Método Simplex")
            p.drawString(100, 730, f"Valor Óptimo: {resultado}")

            y = 710
            for i in range(num_variables):
                p.drawString(100, y, f"X{i+1} = {solucion[i]}")
                y -= 20

            for i in range(num_restricciones):
                p.drawString(100, y, f"S{i+1} = {holguras[i]}")
                y -= 20

            p.drawString(100, y, "Pasos:")
            y -= 20

            for i, paso in enumerate(pasos):
                p.drawString(100, y, f"Iteración {i+1}: {paso}")
                y -= 20

            p.showPage()
            p.save()

            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='resultado.pdf', mimetype='application/pdf')

        elif tipo_archivo == 'txt':
            # Crear un archivo TXT en memoria
            output = io.StringIO()
            output.write("Resultado del Método Simplex\n")
            output.write(f"Valor Óptimo: {resultado}\n")

            for i in range(num_variables):
                output.write(f"X{i+1} = {solucion[i]}\n")

            for i in range(num_restricciones):
                output.write(f"S{i+1} = {holguras[i]}\n")

            output.write("Pasos:\n")
            for i, paso in enumerate(pasos):
                output.write(f"Iteración {i+1}: {paso}\n")

            buffer = io.BytesIO()
            buffer.write(output.getvalue().encode('utf-8'))
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='resultado.txt', mimetype='text/plain')

    except Exception as e:
        return f"Error al generar el archivo: {e}"


if __name__ == '__main__':
    app.run(debug=True)