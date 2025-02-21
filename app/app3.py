from flask import Flask, render_template, request, redirect, url_for
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64

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