![Banner](banner.png)

# dm-data-dictionary-masker
Masks data based on a user-provided dictionary, replacing specific values with corresponding masked values defined in the dictionary file. - Focused on Tools designed to generate or mask sensitive data with realistic-looking but meaningless values

## Install
`git clone https://github.com/ShadowGuardAI/dm-data-dictionary-masker`

## Usage
`./dm-data-dictionary-masker [params]`

Naming the output file as the input file is refused at exit 1 before any write, including alias and symlink spellings of the same path. When no value matches the dictionary, the run prints `No values matched the dictionary.`, exits 1, and writes no output file.

## Parameters
- `-h`: Show help message and exit
- `--input_format`: Format of the input file (default: json)
- `--output_format`: Format of the output file (default: json)

## License
Copyright (c) ShadowGuardAI
