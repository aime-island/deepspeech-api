import os
from deepspeech import Model


def create_model(path, config):
    # Extract config
    model = path.get('model') + 'output_graph.pbmm' or \
        path.get('model') + 'output_graph.pb'
    lm_path = path.get('lm_path')
    beam_width = config.get('beam_width')
    lm_weight = config.get('lm_weight')
    w_weight = config.get('w_weight')
    n_features = config.get('n_features')
    n_context = config.get('n_context')

    # Búa til lm paths
    alphabet = os.path.join(lm_path, 'alphabet.txt')
    lm = os.path.join(lm_path, 'lm.binary')
    trie = os.path.join(lm_path, 'trie')

    # Búa til módel
    ds = Model(model, n_features, n_context, alphabet, beam_width)
    ds.enableDecoderWithLM(alphabet, lm, trie, lm_weight, w_weight)

    return ds
