import numpy as np

def create_sequences(df, feature_cols, window):
    data = df[feature_cols].values
    sequences = []
    targets = []
    
    for i in range(len(data) - window):
        sequences.append(data[i:i+window])
        targets.append(data[i+window])
    
    return np.array(sequences), np.array(targets)