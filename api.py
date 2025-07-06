from flask import Flask, request, jsonify
import esm
import torch

app = Flask(__name__)

print("Loading ESMFold model...")
model = esm.pretrained.esmfold_v1()
model = model.eval().cuda()
print("Model successfully loaded!")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or 'sequence' not in data:
        return jsonify({"error": "Sequence not provided"}), 400

    sequence = data['sequence']
    
    try:
        print(f"Processin sequence: {sequence[:15]}...")
        with torch.no_grad():
            pdb_output = model.infer_pdb(sequence)
        print("Prediction conluded.")
        return jsonify({"pdb": pdb_output})
    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)