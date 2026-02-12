from dotenv import load_dotenv
import os
import time
import sys
from PIL import Image, ImageDraw
from matplotlib import pyplot as plt

# import namespaces
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential


def main():

    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')

    try:
        # Get Configuration Settings
        load_dotenv()
        ai_endpoint = os.getenv('AI_SERVICE_ENDPOINT')
        ai_key = os.getenv('AI_SERVICE_KEY')

        # Get image
        image_file = 'images/Lincoln.jpg'
        if len(sys.argv) > 1:
            image_file = sys.argv[1]

        # Authenticate Azure AI Vision client
        cv_client = ImageAnalysisClient(
            endpoint=ai_endpoint,
            credential=AzureKeyCredential(ai_key)
        )

        # Read text in image
        with open(image_file, "rb") as f:
            image_data = f.read()
        print(f"\nReading text in {image_file}")

        result = cv_client.analyze(
            image_data=image_data,
            visual_features=[VisualFeatures.READ]
        )

        # Print the text
        if result.read is not None:
            print("\nText:")
            for line in result.read.blocks[0].lines:
                print(f" {line.text}")
            
            # Annotate the text in the image
            annotate_lines(image_file, result.read)

            # Find individual words in each line
            annotate_words(image_file, result)

    except Exception as ex:
        print(ex)


def annotate_lines(image_file, detected_text):
    print(f'\nAnnotating lines of text in image...')

    # Prepare image for drawing
    image = Image.open(image_file)
    fig = plt.figure(figsize=(image.width / 100, image.height / 100))
    plt.axis('off')
    draw = ImageDraw.Draw(image)
    color = 'cyan'

    for line in detected_text.read.blocks[0].lines:
        # Draw line bounding polygon
        r = line.bounding_polygon
        rectangle = ((r[0].x, r[0].y), (r[1].x, r[1].y), (r[2].x, r[2].y), (r[3].x, r[3].y))
        draw.polygon(rectangle, outline=color, width=3)

    # Save image
    plt.imshow(image)
    plt.tight_layout(pad=0)
    textfile = 'lines.jpg'
    fig.savefig(textfile)
    print('  Results saved in', textfile)


def annotate_words(image_file, detected_text):
    print(f'\nAnnotating individual words in image...')

    # Prepare image for drawing
    image = Image.open(image_file)
    fig = plt.figure(figsize=(image.width / 100, image.height / 100))
    plt.axis('off')
    draw = ImageDraw.Draw(image)
    color = 'cyan'

    for line in detected_text.read.blocks[0].lines:
        for word in line.words:
            # Draw word bounding polygon
            r = word.bounding_polygon
            rectangle = ((r[0].x, r[0].y), (r[1].x, r[1].y), (r[2].x, r[2].y), (r[3].x, r[3].y))
            draw.polygon(rectangle, outline=color, width=3)

    # Save image
    plt.imshow(image)
    plt.tight_layout(pad=0)
    textfile = 'words.jpg'
    fig.savefig(textfile)
    print('  Results saved in', textfile)


if __name__ == "__main__":
    main()
