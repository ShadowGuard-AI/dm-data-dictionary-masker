import argparse
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Masks data based on a user-provided dictionary.")
    parser.add_argument("input_file", help="The input file containing the data to mask (e.g., JSON, CSV).")
    parser.add_argument("dictionary_file", help="The JSON file containing the masking dictionary.")
    parser.add_argument("output_file", help="The output file to write the masked data to.")
    parser.add_argument("--input_format", choices=['json', 'csv', 'txt'], default='json', help="Format of the input file (default: json)")  # Added input format argument
    parser.add_argument("--output_format", choices=['json', 'csv', 'txt'], default='json', help="Format of the output file (default: json)") # Added output format argument
    return parser.parse_args()


def load_dictionary(dictionary_file):
    """
    Loads the masking dictionary from a JSON file.

    Args:
        dictionary_file (str): The path to the JSON file.

    Returns:
        dict: The masking dictionary.  Returns None if an error occurs.
    """
    try:
        with open(dictionary_file, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                logging.error("Dictionary file must contain a JSON object (dictionary).")
                return None
            return data
    except FileNotFoundError:
        logging.error(f"Dictionary file not found: {dictionary_file}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in dictionary file: {dictionary_file}")
        return None
    except Exception as e:
        logging.error(f"Error loading dictionary: {e}")
        return None


def mask_data(data, dictionary, counter=None):
    """
    Masks the data based on the provided dictionary.

    Args:
        data (any): The data to mask.
        dictionary (dict): The masking dictionary.
        counter (list, optional): One item list incremented on each match.

    Returns:
        any: The masked data.
    """
    if isinstance(data, dict):
        masked_data = {}
        # Keys are never masked, only the values under them. A
        # sensitive word sitting in a field name stays exactly as it
        # was, at every depth of the structure.
        for key, value in data.items():
            masked_data[key] = mask_data(value, dictionary, counter)
        return masked_data
    elif isinstance(data, list):
        masked_data = [mask_data(item, dictionary, counter) for item in data]
        return masked_data
    else:
        if data in dictionary:
            if counter is not None:
                counter[0] += 1
            return dictionary[data]
        # Dictionary keys loaded from JSON are always strings, so a typed
        # JSON value such as 123 could never equal its "123" key and went
        # unmasked. Plain scalars get one string-form lookup before giving
        # up. Booleans are excluded: str(True) is "True", and matching that
        # against a dictionary key would be a surprise, not a mask.
        if isinstance(data, (int, float)) and not isinstance(data, bool):
            text_key = str(data)
            if text_key in dictionary:
                if counter is not None:
                    counter[0] += 1
                return dictionary[text_key]
        return data  # Return original value if not in dictionary


def load_input_data(input_file, input_format):
    """
    Loads data from the input file based on its format. Supports JSON, CSV, and TXT.

    Args:
        input_file (str): The path to the input file.
        input_format (str): The format of the input file ('json', 'csv', 'txt').

    Returns:
        any: The loaded data.  Returns None if an error occurs.
    """
    try:
        if input_format == 'json':
            with open(input_file, 'r') as f:
                return json.load(f)
        elif input_format == 'csv':
            import csv
            with open(input_file, 'r') as f:
                reader = csv.DictReader(f)
                return list(reader)
        elif input_format == 'txt':
            with open(input_file, 'r') as f:
                # Lines are stripped as they are loaded, so leading
                # and trailing spaces are lost for every line, matched
                # or not, and a blank line becomes an empty string
                # entry that is carried into the output.
                return [line.strip() for line in f]  # Read as a list of lines
        else:
            logging.error(f"Unsupported input format: {input_format}")
            return None
    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in input file: {input_file}")
        return None
    except Exception as e:
        logging.error(f"Error loading input data: {e}")
        return None

def write_output_data(data, output_file, output_format):
    """
    Writes the masked data to the output file based on its format. Supports JSON, CSV, and TXT.

    Args:
        data (any): The masked data.
        output_file (str): The path to the output file.
        output_format (str): The format of the output file ('json', 'csv', 'txt').
    """
    # Returns True only when a file was actually written. Failures used
    # to return None on the same footing as success, and main then logged
    # completion and exited 0 with no output file at all.
    try:
        if output_format == 'json':
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=4)
        elif output_format == 'csv':
            import csv
            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                logging.error("CSV output requires a list of dictionaries.")
                return False
            if data:  # Check if data is not empty to avoid errors if the header can't be determined.
                keys = data[0].keys()
                with open(output_file, 'w', newline='') as f:  # newline='' to prevent extra blank rows on Windows
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data)
            else:
                 logging.warning("No data to write to CSV file.")
                 return False
        elif output_format == 'txt':
            if not isinstance(data, list):
                logging.error("TXT output requires a list of strings.")
                return False
            with open(output_file, 'w') as f:
                for item in data:
                    f.write(str(item) + '\n')
        else:
            logging.error(f"Unsupported output format: {output_format}")
            return False

    except Exception as e:
        logging.error(f"Error writing output data: {e}")
        return False
    return True

def main():
    """
    Main function to orchestrate the data masking process.
    """
    args = setup_argparse()

    # Input validation
    if not (args.input_file and args.dictionary_file and args.output_file):
        logging.error("Input file, dictionary file, and output file are required.")
        sys.exit(1)

    if not (args.input_format in ['json', 'csv', 'txt']):
        logging.error(f"Invalid input format: {args.input_format}")
        sys.exit(1)

    if not (args.output_format in ['json', 'csv', 'txt']):
        logging.error(f"Invalid output format: {args.output_format}")
        sys.exit(1)

    # Refuse in place output before any file is written.
    from pathlib import Path
    if Path(args.input_file).resolve() == Path(args.output_file).resolve():
        logging.error("Output file is the same as the input file. Refusing to overwrite the input.")
        sys.exit(1)

    # Load the masking dictionary
    dictionary = load_dictionary(args.dictionary_file)
    if dictionary is None:
        sys.exit(1)

    # Load the input data
    input_data = load_input_data(args.input_file, args.input_format)
    if input_data is None:
        sys.exit(1)

    # Mask the data
    # The input and output formats are independent choices here, so a
    # conversion can be asked for: JSON in, CSV out works only when
    # the masked data is a list of flat dictionaries, and that is not
    # learned until the write step at the end of the run.
    counter = [0]
    masked_data = mask_data(input_data, dictionary, counter)
    if counter[0] == 0:
        print("No values matched the dictionary.")
        sys.exit(1)

    # Write the masked data to the output file
    if not write_output_data(masked_data, args.output_file, args.output_format):
        sys.exit(1)

    logging.info("Data masking complete.")


if __name__ == "__main__":
    main()