import base64
import os
import json

def image_to_base64(image_path):
    """
    Converts an image file to a Base64 encoded string with a data URI prefix.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The Base64 encoded string with a data URI, or None if the file is not found.
    """
    try:
        # Determine the image type (e.g., jpeg, png) from the file extension
        image_extension = os.path.splitext(image_path)[1].lower().replace('.', '')
        if image_extension == 'jpg':
            image_extension = 'jpeg' # Common practice for data URIs

        # Read the image file in binary mode
        with open(image_path, "rb") as image_file:
            # Read the binary data
            binary_data = image_file.read()

            # Encode the binary data to Base64 bytes
            base64_encoded_bytes = base64.b64encode(binary_data)

            # Decode the Base64 bytes to a string
            base64_encoded_string = base64_encoded_bytes.decode('utf-8')

            # Prepend the data URI scheme, which is needed for web/JSON contexts
            data_uri = f"data:image/{image_extension};base64,{base64_encoded_string}"

            return data_uri

    except FileNotFoundError:
        print(f"Error: The file '{image_path}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# --- Main execution ---
if __name__ == "__main__":
    # IMPORTANT: Replace 'img123.jpg' with the actual full name of your image file.
    # For example, if your image is a PNG, use 'img123.png'.
    image_filename = "img112.jpg"

    print(f"Attempting to convert '{image_filename}' to Base64...")

    # Convert the image
    base64_string = image_to_base64(image_filename)

    # Print the result as a full JSON object
    if base64_string:
        print("\n--- Conversion Successful ---")
        
        # Create a dictionary to represent the JSON payload
        json_payload = {
            "image_data": base64_string
        }
        
        # Print the full JSON string, neatly formatted
        print("\nFull JSON Payload:")
        print(json.dumps(json_payload, indent=4))
        print(f"\nThis JSON object is what you would send as the body of your API request.")

