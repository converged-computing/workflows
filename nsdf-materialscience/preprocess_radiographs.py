import argparse
import os
import sys
import cv2 as cv
import numpy as np
import multiprocessing
from pathlib import Path

# This script preprocessed rasiographs to measure the amount of stretch and compression along Silica or any other material


def preprocess(image, scanid, data_root):
    """
    This function preprocess each image from the radiograph set with a series of steps
    """
    # Read original image
    print(f"Reading image: {image}")
    original_img = cv.imread(image, cv.IMREAD_GRAYSCALE).astype(np.float32)
    basename = os.path.basename(image)

    # Don't run twice
    outfile = os.path.join(
        data_root, "preprocessed", scanid, f"Preprocessed_{basename}"
    )
    if os.path.exists(outfile):
        return

    # Gaussian blur with sigma=30
    sigma = 30.0
    blurred_img = cv.GaussianBlur(original_img, (0, 0), sigma)

    # Substract blurred image from original image
    substracted_img = cv.subtract(original_img, blurred_img)

    # Adjust contrast and brightness
    alpha = 25
    beta = 125
    # https://stackoverflow.com/questions/39308030/how-do-i-increase-the-contrast-of-an-image-in-python-opencv
    enhanced_img = cv.addWeighted(substracted_img, alpha, substracted_img, 0, beta)

    alpha = 2.0
    beta = -125
    # https://docs.opencv.org/3.4/d3/dc1/tutorial_basic_linear_transform.html
    contrast_img = cv.convertScaleAbs(enhanced_img, alpha=alpha, beta=beta)

    # Rotate image 90 degrees clockwise
    rotated_img = cv.rotate(contrast_img, cv.ROTATE_90_CLOCKWISE)

    # Save results
    cv.imwrite(outfile, rotated_img.astype(np.uint8))


def average(images, average_dir):
    """
    This function averages by N=4 preprocessed images
    """
    # Get index from first and last image
    names = (
        "Radiographs_"
        + str(images[0].split("__")[1].split(".")[0])
        + "--"
        + str(images[-1].split("__")[1].split(".")[0])
    )

    # Read first image and make it equal to avg_img
    avg_image = cv.imread(images[0], cv.IMREAD_GRAYSCALE)

    # Function taken from: https://leslietj.github.io/2020/06/28/How-to-Average-Images-Using-OpenCV/
    for i, image in enumerate(images):
        if i == 0:
            continue

        # Read next image
        image = cv.imread(image, cv.IMREAD_GRAYSCALE)
        alpha = 1.0 / (i + 1)
        beta = 1.0 - alpha
        # Average image
        avg_image = cv.addWeighted(image, alpha, avg_image, beta, 0.0)

    average_img = os.path.join(average_dir, f"Average_{names}.tiff")
    cv.imwrite(average_img, avg_image)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Radiograph Processor",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")
    preprocess = subparsers.add_parser(
        "preprocess",
        description="add an alias to a container recipe.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    for command in [preprocess]:
        command.add_argument("data", help="Data root with originals subdirectory.")
        command.add_argument("scanid", help="Full scan id")
        command.add_argument(
            "--n-averages",
            dest="n_averages",
            help="Divisor for averaging images, split images by this many (default 4)",
            default=4,
        )
    return parser


def main():
    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    # Show args to the user
    print("       data: %s" % args.data)
    print("     scanid: %s" % args.scanid)
    print(" n-averages: %s" % args.n_averages)

    # Data directory must exist with original and scan id
    data_dir = os.path.join(args.data, "original", args.scanid)

    print(f"Contents of {args.data}:")
    print(os.listdir(args.data))
    if not os.path.exists(data_dir):
        sys.exit(f"{data_dir} does not exist.")

    data_preprocess = os.path.join(args.data, "preprocessed", args.scanid)
    data_averaged = os.path.join(args.data, "averaged", args.scanid)
    for dirname in data_preprocess, data_averaged:
        Path(dirname).mkdir(parents=True, exist_ok=True)

    # Pre-processing the radiographs in parallel per set
    original_images = os.listdir(data_dir)
    listargs = [
        [os.path.join(data_dir, x), args.scanid, args.data] for x in original_images
    ]
    with multiprocessing.Pool() as pool:
        pool.starmap(preprocess, listargs)
    print("Finish preprocessing")

    # Averaging by 4 the pre-processed radiographs
    images = [os.path.join(data_preprocess, x) for x in os.listdir(data_preprocess)]
    images.sort()
    sets = int(len(images) / args.n_averages)
    four_split = np.array_split(images, sets)
    listargs = [[x, data_averaged] for x in four_split]
    with multiprocessing.Pool() as pool:
        pool.starmap(average, listargs)
    print("Finish averaging")


if __name__ == "__main__":
    main()
