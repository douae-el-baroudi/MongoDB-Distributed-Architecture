
import os
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, render_template_string
from pymongo import MongoClient, UpdateOne

app = Flask(__name__)

# Connexion au replica set MongoDB
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27018,localhost:27019,localhost:27020/?replicaSet=rs0"
)

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

# Base de données et collection
db = client["ecommerceDB"]
collection = db["commandes"]

# Empêcher les doublons
collection.create_index("order_id", unique=True)


def importer_commandes():
    """Importer les commandes Excel sans créer de doublons."""

    fichier = os.path.join(

        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "dataset_commandes.xlsx"
    )
    if not os.path.exists(fichier):
        raise FileNotFoundError(
            f"Fichier Excel introuvable : {fichier}"
        )

    df = pd.read_excel(fichier)

    # Vérifier les colonnes obligatoires
    if "order_id" not in df.columns:
        raise ValueError("La colonne order_id est obligatoire.")

    if df["order_id"].duplicated().any():
        raise ValueError(
            "Le fichier Excel contient des order_id en double."
        )

    # Convertir les valeurs manquantes en None
    df = df.astype(object).where(pd.notna(df), None)

    operations = []

    for commande in df.to_dict(orient="records"):
        # Convertir les dates pandas en dates Python
        for cle, valeur in commande.items():
            if isinstance(valeur, pd.Timestamp):
                commande[cle] = valeur.to_pydatetime()

        operations.append(
            UpdateOne(
                {"order_id": commande["order_id"]},
                {"$setOnInsert": commande},
                upsert=True
            )
        )

    if not operations:
        return 0

    resultat = collection.bulk_write(
        operations,
        ordered=False
    )

    return resultat.upserted_count


@app.route("/")
def accueil():
    try:
        commandes = list(
            collection.find({}, {"_id": 0}).sort("order_id", 1)
        )

        total_commandes = collection.count_documents({})
        chiffre_affaires = sum(
            float(c.get("total") or 0)
            for c in commandes
        )

        html = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Gestion des commandes</title>
            <style>
                * { box-sizing: border-box; }
                body {
                    margin: 0;
                    font-family: Arial, sans-serif;
                    background: #f3f6fb;
                    color: #1e293b;
                }
                header {
                    background: #123b70;
                    color: white;
                    padding: 28px 6%;
                }
                header h1 { margin: 0 0 8px; }
                header p { margin: 0; color: #dbeafe; }
                main { padding: 30px 5%; }
                .stats {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 18px;
                    margin-bottom: 25px;
                }
                .stat {
                    background: white;
                    padding: 22px;
                    border-radius: 12px;
                    flex: 1;
                    min-width: 200px;
                    box-shadow: 0 2px 10px #0000000a;
                }
                .stat p { margin: 0 0 10px; color: #64748b; }
                .stat strong { font-size: 25px; color: #123b70; }
                .actions { margin-bottom: 20px; }
                button {
                    border: 0;
                    border-radius: 7px;
                    padding: 12px 18px;
                    background: #1765bd;
                    color: white;
                    font-weight: bold;
                    cursor: pointer;
                }
                button:hover { background: #104d91; }
                #message { margin-left: 10px; }
                .table-container {
                    overflow-x: auto;
                    background: white;
                    border-radius: 12px;
                    padding: 15px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    min-width: 900px;
                }
                th, td {
                    padding: 13px 12px;
                    text-align: left;
                    border-bottom: 1px solid #e2e8f0;
                }
                th { background: #edf4fc; color: #123b70; }
                tr:hover td { background: #f8fafc; }
                footer {
                    text-align: center;
                    padding: 22px;
                    color: #64748b;
                }
            </style>
        </head>
        <body>
            <header>
                <h1>Gestion des commandes</h1>
                <p>Projet Big Data — MongoDB Replica Set</p>
            </header>

            <main>
                <section class="stats">
                    <div class="stat">
                        <p>Nombre de commandes</p>
                        <strong>{{ total_commandes }}</strong>
                    </div>
                    <div class="stat">
                        <p>Chiffre d'affaires total</p>
                        <strong>{{ "%.2f"|format(chiffre_affaires) }} DH</strong>
                    </div>
                </section>

                <div class="actions">
                    <button onclick="importer()">Importer depuis Excel</button>
                    <span id="message"></span>
                </div>

                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Order ID</th>
                                <th>Client</th>
                                <th>Ville</th>
                                <th>Produit</th>
                                <th>Quantité</th>
                                <th>Prix unitaire</th>
                                <th>Total</th>
                                <th>Paiement</th>
                                <th>Statut</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                        {% for c in commandes %}
                            <tr>
                                <td>{{ c.get("order_id", "") }}</td>
                                <td>{{ c.get("client", "") }}</td>
                                <td>{{ c.get("ville", "") }}</td>
                                <td>{{ c.get("produit", "") }}</td>
                                <td>{{ c.get("quantite", "") }}</td>
                                <td>{{ c.get("prix_unitaire", "") }}</td>
                                <td>{{ c.get("total", "") }}</td>
                                <td>{{ c.get("paiement", "") }}</td>
                                <td>{{ c.get("statut", "") }}</td>
                                <td>{{ c.get("date_commande", "") }}</td>
                            </tr>
                        {% else %}
                            <tr>
                                <td colspan="10">Aucune commande. Clique sur Importer depuis Excel.</td>
                            </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                </div>
            </main>

            <footer>Projet de gestion et stockage des commandes avec MongoDB</footer>

            <script>
                async function importer() {
                    const message = document.getElementById("message");
                    message.textContent = "Importation en cours...";

                    try {
                        const response = await fetch("/importer", {
                            method: "POST"
                        });
                        const resultat = await response.json();

                        if (!response.ok) {
                            throw new Error(resultat.erreur || "Erreur d'importation");
                        }

                        message.textContent =
                            resultat.ajoutees + " nouvelles commandes importées.";
                        window.location.reload();
                    } catch (erreur) {
                        message.textContent = "Erreur : " + erreur.message;
                    }
                }
            </script>
        </body>
        </html>
        """

        return render_template_string(
            html,
            commandes=commandes,
            total_commandes=total_commandes,
            chiffre_affaires=chiffre_affaires
        )

    except Exception as erreur:
        return (
            f"Erreur lors de la lecture de MongoDB : {str(erreur)}",
            500
        )


@app.route("/importer", methods=["POST"])
def importer():
    try:
        nombre = importer_commandes()

        return jsonify({
            "message": "Importation terminée",
            "ajoutees": nombre
        })

    except Exception as erreur:
        return jsonify({
            "erreur": str(erreur)
        }), 500


@app.route("/sante")
def sante():
    try:
        client.admin.command("ping")

        return jsonify({
            "status": "OK",
            "mongodb": "connecté",
            "database": db.name,
            "collection": collection.name
        })

    except Exception as erreur:
        return jsonify({
            "status": "ERREUR",
            "message": str(erreur)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
    