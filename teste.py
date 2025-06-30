import requests
import os
import sys

# Adiciona o diretório src ao path para que possamos importar de lá
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def run_system_check():
    """
    Executa uma série de testes para validar a arquitetura de dois containers.
    """
    print("="*60)
    print("INICIANDO VERIFICAÇÃO DO SISTEMA DE DOIS CONTAINERS")
    print("="*60)

    # --- Teste 1: Validar Container Local (TemBERTure) ---
    print("\n[TESTE 1/2] Verificando o ambiente local e o TemBERTure...")
    try:
        from src.protein.thermostability.temberture import calculate_temberture_score

        #temberture = TemBERTure(tm_model_path, cls_model_path, half_precision=False)
        test_sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVL"
        
        print("Realizando uma predição com o TemBERTure...")
        prediction = calculate_temberture_score(test_sequence)
        
        print(f"Resultado da Predição (TemBERTure): {prediction}")
        print("✅ SUCESSO! O container local (genetic-algorithm) e o TemBERTure estão funcionando.")

    except Exception as e:
        print(f"❌ FALHA! Ocorreu um erro no ambiente local do TemBERTure.")
        print(f"   Erro detalhado: {e}")
        return

    # --- Teste 2: Validar Comunicação com o Serviço ESMFold ---
    print("\n[TESTE 2/2] Verificando a comunicação com o esmfold-service...")
    try:
        api_url = "http://esmfold-service:5001/predict"
        test_sequence_esm = "MKVETARVSVFSEYPGEEPVYFVSFTLEGSFLVKALYLVEGERGPLYRPKA"
        
        print(f"Enviando sequência para a API em: {api_url}")
        response = requests.post(api_url, json={'sequence': test_sequence_esm}, timeout=300)
        
        response.raise_for_status()
        
        data = response.json()
        
        # --- AQUI ESTÁ A CORREÇÃO ---
        # Verificamos se a chave 'pdb' existe, se o valor não está vazio,
        # e se a palavra "ATOM" aparece no texto (ignorando espaços em branco no início).
        if 'pdb' in data and data['pdb'] and "ATOM" in data['pdb'].strip():
            print("Resposta da API recebida com sucesso!")
            print(f"Início do PDB recebido:\n{data['pdb'][:200]}...")
            print("\n✅ SUCESSO! O serviço ESMFold respondeu corretamente pela API.")
        else:
            print("❌ FALHA! A API respondeu, mas não retornou um PDB válido.")
            print(f"   Resposta recebida: {data}")

    except requests.exceptions.RequestException as e:
        print(f"❌ FALHA! Não foi possível se comunicar com o serviço ESMFold.")
        print("   Possíveis causas: O container 'esmfold-service' não está rodando ou houve um erro nele.")
        print(f"   Erro detalhado: {e}")
    except Exception as e:
        print(f"❌ FALHA! Ocorreu um erro inesperado ao testar a API do ESMFold.")
        print(f"   Erro detalhado: {e}")

if __name__ == "__main__":
    run_system_check()