
import os
import ast
import json
import numpy as np
import soundfile as sf
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestCentroid
import torch
import torchaudio
import shutil

# --- COMPATIBILITY PATCH FOR TORCHAUDIO >= 2.1.0 ---
# SpeechBrain expects torchaudio.list_audio_backends() to exist, but it was removed.
if not hasattr(torchaudio, 'list_audio_backends'):
    torchaudio.list_audio_backends = lambda: ['soundfile']
# ---------------------------------------------------

# --- COMPATIBILITY PATCH FOR WINDOWS SYMLINKS ---
# SpeechBrain forcibly symlinks HuggingFace cache to tmpdir. Windows denies this without Admin.
# We override os.symlink to just physically copy the file instead.
import os
_original_symlink = os.symlink
def safe_symlink(*args, **kwargs):
    try:
        if len(args) >= 2:
            shutil.copy2(args[0], args[1])
    except Exception as e:
        print(f"Fallback copy failed: {e}")
os.symlink = safe_symlink
# ------------------------------------------------

from speechbrain.inference.speaker import SpeakerRecognition

from speechbrain.inference.speaker import SpeakerRecognition

AUDIO_DIR = os.path.join('bot', 'audio')
BOT_FILE = os.path.join('bot', 'bot.py')
CACHE_FILE = 'voice_embeddings_cache.json'

# User provided ground truth
LABELED_GROUPS = {
    'group_1': ['afk', 'ate', 'fish', 'wait', 'no', 'myaoe', 'spag', 'me', 'yay'],
    'group_2': ['0friend', '1friend', '2ja', 'iyo', 'luv', 'black', 'dc', 'respect', 'forgot', 'wp'],
    'group_3': ['barracks', 'air', 'in', 'nowood'],
    'group_4': ['14', 'yay2'],
    'group_5': ['hard', 'imp', 'lager'],
    'group_6': ['bb', 'bb2', 'ah', 'ah2', 'jizz', 'jizz2', 'kaka'],
    'group_7': ['sit', 'g']
}

# Lazy initialization of SpeechBrain model to save time if we don't need it
_MODEL = None

def get_model():
    global _MODEL
    if _MODEL is None:
        print("Loading SpeechBrain VoxCeleb Model... (This might take a minute the first time to download)", flush=True)
        _MODEL = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb", 
            savedir="tmpdir",
            hparams_file="hyperparams.yaml",
            run_opts={"device": "cpu"}
        )
    return _MODEL

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

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
    """Extracts a 192-dimensional structural x-vector embedding of the voice."""
    try:
        model = get_model()
        data, fs = sf.read(file_path)
        
        # soundfile returns numpy arrays, speechbrain expects torch tensors
        if data.ndim > 1:
            data = data.mean(axis=1) # mix to mono
        
        # Normalize to float32
        data = data.astype(np.float32)
        signal = torch.from_numpy(data).unsqueeze(0) # [batch, time]
        
        # SpeechBrain VoxCeleb models expect 16000 Hz, single channel
        if fs != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=fs, new_freq=16000)
            signal = resampler(signal)
            
        # Extract embeddings (Returns shape [batch, 1, embedding_size])
        with torch.no_grad():
            embeddings = model.encode_batch(signal)
            
        # Squeeze down to flat 1D numpy array
        features = embeddings.squeeze().cpu().numpy()
        return features.tolist() # return as list for JSON cache serialization

    except Exception as e:
        print(f"Failed to process {file_path}: {e}")
        return None

def main():
    print("Reading files...", flush=True)
    if not os.path.exists(AUDIO_DIR):
        print(f"Directory not found: {AUDIO_DIR}")
        return

    excluded_files = get_excluded_files()
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

    # Manage Feature Cache
    cache = load_cache()
    features = []
    valid_files = []
    cache_dirty = False

    print(f"Extracting X-Vectors for {len(files_to_process)} files...", flush=True)
    
    for i, f in enumerate(files_to_process):
        path = os.path.join(AUDIO_DIR, f)
        
        # Pull from cache if available, otherwise hit the Neural Net
        if f in cache:
            feat = cache[f]
        else:
            print(f"[{i+1}/{len(files_to_process)}] Processing raw audio for {f}...", flush=True)
            feat = extract_features(path)
            if feat is not None:
                cache[f] = feat
                cache_dirty = True
                
        if feat is not None:
            features.append(feat)
            valid_files.append(f)

    if cache_dirty:
        print("Saving new embeddings to cache...", flush=True)
        save_cache(cache)

    if not features:
        print("No features extracted.")
        return

    # Back to numpy for Scikit-Learn (No need to scale X-vectors for Cosine Similarity)
    X = np.array(features)
    valid_files = np.array(valid_files)

    # Map filename -> index in X
    file_to_idx = {fname: i for i, fname in enumerate(valid_files)}

    print("Training Centroids on User Labels...", flush=True)
    
    # Calculate Custom Centroids using Median Pooling (more robust to noisy outliers)
    centroids = {}
    for group_name, filenames in LABELED_GROUPS.items():
        group_vectors = []
        for name in filenames:
            fname = f"{name}.ogg"
            if fname in file_to_idx:
                idx = file_to_idx[fname]
                group_vectors.append(X[idx])
                
        if group_vectors:
            # Median pooling is much better for noisy data than Mean pooling
            median_vector = np.median(group_vectors, axis=0)
            # Normalize the centroid so cosine similarity is just a dot product
            centroids[group_name] = median_vector / np.linalg.norm(median_vector)

    if not centroids:
        print("Error: None of the labeled files were found or processed successfully.")
        return

    # Predict for ALL files using Cosine Similarity
    # Cosine Similarity = Dot Product of two normalized vectors. 
    # Closer to 1.0 means more similar.
    predicted_labels = []
    
    # Normalize all extracted features
    X_norms = np.linalg.norm(X, axis=1, keepdims=True)
    X_normalized = X / X_norms
    
    group_names = list(centroids.keys())
    centroid_matrix = np.array(list(centroids.values())) # shape: (num_groups, embedding_dim)
    
    for i in range(len(X_normalized)):
        vector = X_normalized[i]
        # Calculate cosine similarity against all centroids at once via dot product
        similarities = np.dot(centroid_matrix, vector)
        
        # Find the group with the highest similarity score
        best_match_idx = np.argmax(similarities)
        best_score = similarities[best_match_idx]
        
        # If the highest similarity is too low, the AI isn't confident (likely noisy or multiple speakers)
        if best_score < 0.30:
            predicted_labels.append("Unknown (Needs Review)")
        else:
            predicted_labels.append(group_names[best_match_idx])

    # Organize results
    clusters = {}
    for filename, label in zip(valid_files, predicted_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(filename[:-4]) 

    print("\n" + "="*50)
    print("AI SPEAKER RECOGNITION RESULTS (COSINE SIMILARITY)")
    print("="*50)
    
    # Print labeled groups first in order
    for label in sorted(LABELED_GROUPS.keys()):
        if label in clusters:
            group_files = sorted(clusters[label])
            print(f"\n{label} ({len(group_files)} files):")
            print(", ".join(group_files))
            
    # Print the Unknown bucket at the very bottom
    if "Unknown (Needs Review)" in clusters:
        unknown_files = sorted(clusters["Unknown (Needs Review)"])
        print(f"\nUnknown (Needs Review) ({len(unknown_files)} files):")
        print(", ".join(unknown_files))

if __name__ == "__main__":
    main()
