from flask import Flask, render_template, request, redirect, url_for, send_file
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

def generar_grafo(nodos, conexiones):
    G = nx.Graph()
    G.add_nodes_from(nodos)
    for conexion in conexiones:
        nodo1, nodo2, costo = conexion
        G.add_edge(nodo1, nodo2, weight=costo)
    return G

def calcular_ruta_optima(G, inicio, fin):
    try:
        ruta = nx.dijkstra_path(G, inicio, fin, weight='weight')
        costo = nx.dijkstra_path_length(G, inicio, fin, weight='weight')
        return ruta, costo
    except nx.NetworkXNoPath:
        return None, None

def graficar_red(G, ruta_optima=None):
    pos = nx.spring_layout(G)
    plt.figure(figsize=(10, 6))
    
    # Dibujar todos los nodos y aristas
    nx.draw_networkx_nodes(G, pos, node_size=700, node_color='lightblue')
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.5)
    
    # Resaltar la ruta óptima si existe
    if ruta_optima:
        edges = [(ruta_optima[i], ruta_optima[i + 1]) for i in range(len(ruta_optima) - 1)]
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color='red', width=2.5)
        nx.draw_networkx_nodes(G, pos, nodelist=ruta_optima, node_color='red', node_size=700)
    
    # Etiquetas
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_labels(G, pos, font_size=12, font_family='sans-serif')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    
    # Guardar la imagen en un buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    imagen = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return imagen

@app.route('/descargar', methods=['POST'])
def descargar():
    try:
        tipo_archivo = request.form['tipo_archivo']
        ruta_optima = request.form.getlist('ruta_optima[]')
        costo = request.form['costo']
        imagen = request.form['imagen']

        if tipo_archivo == 'pdf':
            # Crear un archivo PDF en memoria
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawString(100, 750, "Resultado de la Ruta Óptima en la Red")
            p.drawString(100, 730, f"Ruta Óptima: {' -> '.join(ruta_optima)}")
            p.drawString(100, 710, f"Costo Total: {costo}")

            # Insertar la imagen en el PDF
            imagen_bytes = base64.b64decode(imagen)
            imagen_io = io.BytesIO(imagen_bytes)
            p.drawImage(imagen_io, 100, 400, width=400, height=300)

            p.showPage()
            p.save()

            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='resultado.pdf', mimetype='application/pdf')

        elif tipo_archivo == 'txt':
            # Crear un archivo TXT en memoria
            output = io.StringIO()
            output.write("Resultado de la Ruta Óptima en la Red\n")
            output.write(f"Ruta Óptima: {' -> '.join(ruta_optima)}\n")
            output.write(f"Costo Total: {costo}\n")

            buffer = io.BytesIO()
            buffer.write(output.getvalue().encode('utf-8'))
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='resultado.txt', mimetype='text/plain')

    except Exception as e:
        return f"Error al generar el archivo: {e}"



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nodos = request.form.get("nodos").split(',')
        inicio = request.form.get("inicio")
        fin = request.form.get("fin")
        conexiones = []
        
        # Recoger todas las conexiones ingresadas
        for i in range(len(nodos)):
            for j in range(len(nodos)):
                if i != j:
                    costo = request.form.get(f"costo_{nodos[i]}_{nodos[j]}")
                    if costo and float(costo) > 0:
                        conexiones.append((nodos[i], nodos[j], float(costo)))
        
        return redirect(url_for("ver_red", nodos=','.join(nodos), conexiones=';'.join([f"{a},{b},{c}" for a, b, c in conexiones]), inicio=inicio, fin=fin))
    return render_template("index3.html")

@app.route("/ver_red")
def ver_red():
    nodos = request.args.get("nodos").split(',')
    conexiones = [tuple(c.split(',')) for c in request.args.get("conexiones").split(';')]
    conexiones = [(a, b, float(c)) for a, b, c in conexiones]
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")
    
    G = generar_grafo(nodos, conexiones)
    imagen = graficar_red(G)
    
    return render_template("ver_red.html", imagen=imagen, nodos=nodos, inicio=inicio, fin=fin, conexiones=request.args.get("conexiones"))

@app.route("/resolver", methods=["POST"])
def resolver():
    nodos = request.form.get("nodos").split(',')
    conexiones = [tuple(c.split(',')) for c in request.form.get("conexiones").split(';')]
    conexiones = [(a, b, float(c)) for a, b, c in conexiones]
    inicio = request.form.get("inicio")
    fin = request.form.get("fin")
    
    G = generar_grafo(nodos, conexiones)
    ruta_optima, costo = calcular_ruta_optima(G, inicio, fin)
    
    imagen = graficar_red(G, ruta_optima)
    
    return render_template("resultado3.html", imagen=imagen, ruta_optima=ruta_optima, costo=costo)

if __name__ == "__main__":
    app.run(debug=True)