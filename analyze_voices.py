
import os
import ast
import numpy as np
import soundfile as sf
import scipy.fft
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestCentroid

AUDIO_DIR = os.path.join('bot', 'audio')
BOT_FILE = os.path.join('bot', 'bot.py')

# User provided ground truth
LABELED_GROUPS = {
    'group_1': ['afk', 'ate', 'fish', 'wait', 'no', 'myaoe', 'spag', 'me', 'yay'],
    'group_2': ['2ja', 'iyo', 'luv', 'black', 'dc', 'respect', 'forgot', 'wp'],
    'group_3': ['barracks', 'air', 'in', 'nowood'],
    'group_4': ['14', 'yay2'],
    'group_5': ['hard', 'imp', 'lager'],
    'group_6': ['bb', 'bb2', 'ah', 'ah2', 'jizz', 'jizz2', 'kaka'],
    'group_7': ['sit', 'g']
}

def get_excluded_files():
    """Parses bot.py to find 'Other AOE sounds' and identifies numeric filenames."""
    excluded = set()
    if os.path.exists(BOT_FILE):
        with open(BOT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == 'LEGACY_CATEGORIES':
                                if isinstance(node.value, ast.List):
                                    for elt in node.value.elts:
                                        if isinstance(elt, ast.Tuple) and len(elt.elts) == 2:
                                            cat_name_node = elt.elts[0]
                                            if isinstance(cat_name_node, ast.Constant) and cat_name_node.value == 'Other AOE sounds':
                                                set_node = elt.elts[1]
                                                if isinstance(set_node, ast.Set):
                                                    for item in set_node.elts:
                                                        if isinstance(item, ast.Constant):
                                                            excluded.add(f"{item.value}.ogg")
            except Exception as e:
                print(f"Error parsing bot.py: {e}")
    return excluded

def extract_features(file_path):
    try:
        data, samplerate = sf.read(file_path)
        if len(data) == 0: return None
        
        if data.ndim > 1:
            data = data.mean(axis=1)
            
        max_samples = 2 * samplerate
        if len(data) > max_samples:
            data = data[:max_samples]
            
        zcr = ((data[:-1] * data[1:]) < 0).sum() / len(data)
        
        fft = np.abs(scipy.fft.rfft(data))
        freqs = scipy.fft.rfftfreq(len(data), 1/samplerate)
        
        min_freq = 100
        max_freq = 8000
        
        mask_range = (freqs >= min_freq) & (freqs <= max_freq)
        relevant_fft = fft[mask_range]
        relevant_freqs = freqs[mask_range]
        
        if len(relevant_freqs) == 0: 
            return np.zeros(21)

        n_bands = 20
        band_limits = np.logspace(np.log10(min_freq), np.log10(max_freq), n_bands + 1)
        
        band_energies = []
        for i in range(n_bands):
            mask = (relevant_freqs >= band_limits[i]) & (relevant_freqs < band_limits[i+1])
            if mask.any():
                energy = np.log(np.mean(relevant_fft[mask]) + 1e-6)
                band_energies.append(energy)
            else:
                band_energies.append(0)
                
        features = np.array([zcr] + band_energies)
        return features

    except Exception as e:
        return None

def main():
    print("Scanning audio files...", flush=True)
    if not os.path.exists(AUDIO_DIR):
        print(f"Directory not found: {AUDIO_DIR}")
        return

    excluded_files = get_excluded_files()
    
    # Also exclude explicitly labeled files from "excluded" list if they happen to overlap
    # (The user knows best)
    labeled_filenames = set()
    for flist in LABELED_GROUPS.values():
        for fname in flist:
            labeled_filenames.add(f"{fname}.ogg")

    all_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.ogg')]
    
    files_to_process = []
    for f in all_files:
        name_no_ext = f[:-4]
        
        if name_no_ext.isdigit(): continue
        
        if f in excluded_files and f not in labeled_filenames:
            continue
            
        files_to_process.append(f)

    print(f"Processing {len(files_to_process)} files...", flush=True)
    
    features = []
    valid_files = []
    
    for f in files_to_process:
        path = os.path.join(AUDIO_DIR, f)
        feat = extract_features(path)
        if feat is not None:
            features.append(feat)
            valid_files.append(f)

    if not features:
        print("No features extracted.")
        return

    X = np.array(features)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Prepare Training Data
    X_train = []
    y_train = []
    
    # Map filename -> index in X_scaled
    file_to_idx = {fname: i for i, fname in enumerate(valid_files)}

    print("Training on user labels...", flush=True)
    for group_name, filenames in LABELED_GROUPS.items():
        for name in filenames:
            fname = f"{name}.ogg"
            if fname in file_to_idx:
                idx = file_to_idx[fname]
                X_train.append(X_scaled[idx])
                y_train.append(group_name)
    
    if not X_train:
        print("Error: None of the labeled files were found or processed successfully.")
        return

    # Train Nearest Centroid Classifier
    clf = NearestCentroid()
    clf.fit(X_train, y_train)

    # Predict for ALL files
    predicted_labels = clf.predict(X_scaled)

    # Organize results
    clusters = {}
    for filename, label in zip(valid_files, predicted_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(filename[:-4]) # Store without extension for nicer output

    print("\n" + "="*50)
    print("SUPERVISED VOICE ANALYSIS RESULTS")
    print("="*50)
    
    for label in sorted(LABELED_GROUPS.keys()):
        if label in clusters:
            group_files = sorted(clusters[label])
            # Mark which ones were original hints with a star? Nah, assume user knows
            print(f"\n{label} ({len(group_files)} files):")
            print(", ".join(group_files))

if __name__ == "__main__":
    main()
