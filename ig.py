# ig.py
# This script generates an image using AutoPipelineForText2Image.

from diffusers import AutoPipelineForText2Image
import torch
from PIL import Image
import sys

def generate_image(prompt):
    pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16", cache_dir="E:\\models")
    pipe.to("cuda")

    image = pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]

    image_path = "generated_image.png"
    image.save(image_path)

    return image_path

def open_image(image_path):
    # Open and display the image using Pillow
    img = Image.open(image_path)
    img.show()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--no-listen":
        prompt = input("Enter image generation prompt: ")
        image_path = generate_image(prompt)
        if image_path:
            print(f"Image generated. [Image Path: {image_path}]")
            open_image(image_path)
        else:
            print("Failed to generate the image.")
    else:
        print("Please use --no-listen flag when calling ig.py from the main script.")
