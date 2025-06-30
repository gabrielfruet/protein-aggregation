from flask import Flask, request, jsonify
import esm
import torch

app = Flask(__name__)

# Carrega o modelo ESMFold uma única vez quando o servidor inicia
print("Carregando o modelo ESMFold...")
model = esm.pretrained.esmfold_v1()
model = model.eval().cuda()
print("Modelo carregado com sucesso!")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or 'sequence' not in data:
        return jsonify({"error": "Sequência não fornecida"}), 400

    sequence = data['sequence']
    
    try:
        print(f"Processando sequência: {sequence[:15]}...")
        with torch.no_grad():
            pdb_output = model.infer_pdb(sequence)
        print("Predição concluída com sucesso.")
        return jsonify({"pdb": pdb_output})
    except Exception as e:
        print(f"Erro durante a predição: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)