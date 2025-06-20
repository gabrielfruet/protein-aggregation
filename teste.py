from src.protein.thermostability.temberture import calculate_temberture_score
from src.protein.thermostability.temberture import calculate_temberture_temperature

if __name__ == "__main__":
    # Example protein sequence
    seq = "ARNDCEQGHILKMFPSTWYV"
    score = calculate_temberture_score(seq)
    temperature = calculate_temberture_temperature(seq)
    print(f"Thermophilicity prediction score 1: {score}, melting temperature: {temperature}") 