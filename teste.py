from src.protein.thermostability.temberture import calculate_temberture_score

if __name__ == "__main__":
    # Example protein sequence
    seq = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    seq2 = "MVHLTPVEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    score = calculate_temberture_score(seq)
    score2 = calculate_temberture_score(seq2)
    print(f"Thermophilicity prediction score 1: {score}, 2: {score2}")