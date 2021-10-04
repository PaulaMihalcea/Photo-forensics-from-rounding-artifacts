import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import random
import time
import tqdm
from argparse import ArgumentParser, Namespace
from datetime import datetime
from main import main as mm
from postprocessing import plot_roc#, get_mean_roc  # TODO
from utils import get_filename, get_file_list, get_last_directory


# Get image information from filename
def get_image_info(filename, extension):
    # Split filename
    el = filename.split('_')

    # Extract information
    if extension in ['png', 'PNG']:
        quality = None
        manip_size = int(el[-1])
        manip_type = el[-2]
    elif extension in ['jpeg', 'jpg', 'jpe', 'jfif', 'jif', 'JPEG', 'JPG', 'JPE', 'JFIF', 'JIF']:
        quality = int(el[-1])
        manip_size = int(el[-2])
        manip_type = el[-3]
    else:
        raise ValueError('Invalid file extension (allowed extensions: .png, .jpeg, .jpg, .jpe, .jfif or .jif.)')

    return manip_size, manip_type, quality


def main(args):
    # Welcome message
    print('Photo Forensics from Rounding Artifacts: results script')
    print('Author: Paula Mihalcea')
    print('Version: 1.0')
    print('Based on a research by S. Agarwal and H. Farid. Details & source code at https://github.com/PaulaMihalcea/Photo-Forensics-from-Rounding-Artifacts.')
    print()

    # Analyze images and save results
    if args.generate:

        # Get file list & shuffle
        file_list = get_file_list(args.dir_path)
        random.shuffle(file_list)

        # Create results subfolder
        if not os.path.exists('results/'):
            os.makedirs('results/')

        # Dimples strength dataframe loading
        dimples_df = pd.read_csv('results/report.csv')

        # Dataframe creation
        results = pd.DataFrame(columns=['img_name', 'dimples_strength', 'format', 'quality', 'manip_type', 'manip_size', 'win_size', 'auc'])
        results_fpr = pd.DataFrame(columns=['img_name', 'fpr'])
        results_tpr = pd.DataFrame(columns=['img_name', 'tpr'])

        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')

        results_path = 'results/results_' + get_last_directory(args.dir_path) + '_' + timestamp + '.csv'
        results_path_fpr = 'results/results_' + get_last_directory(args.dir_path) + '_' + timestamp + '_fpr.csv'
        results_path_tpr = 'results/results_' + get_last_directory(args.dir_path) + '_' + timestamp + '_tpr.csv'

        results.to_csv(results_path, index=False)
        results_fpr.to_csv(results_path_fpr, index=False)
        results_tpr.to_csv(results_path_tpr, index=False)

        '''
        img_name: Image name (without extension).
        dimples: JPEG dimples strength (previously calculated; None otherwise).
        format: Image format (0: PNG, 1: JPEG).
        quality: JPEG quality; -1: PNG image.
        manip_type: Manipulation type.
        manip_size: Manipulation ROI size.
        win_size: EM algorithm window size.
        auc: AUC score.
        fpr: False positive rate (FPR); saved in a separate file.
        tpr: True positive rate (TPR); saved in a separate file.
        '''

        # Main setup (uses default parameters)
        args_mm = Namespace()
        args_mm.win_size = args.win_size
        args_mm.stop_threshold = 1e-2
        args_mm.prob_r_b_in_c1 = 0.3
        args_mm.interpolate = False
        args_mm.show = False
        args_mm.save = False
        args_mm.show_roc_plot = False
        args_mm.save_roc_plot = False
        args_mm.show_diff_plot = False
        args_mm.save_diff_plot = False
        args_mm.verbose = False

        imgs_tot = len(file_list)
        imgs_done = 0

        # Progress bar
        progress_bar = tqdm.tqdm(total=imgs_tot)

        # Time
        start = time.time()

        # Main loop
        for i in file_list:
            # Image information
            args_mm.img_path = i
            filename, extension = get_filename(i)
            manip_size, manip_type, quality = get_image_info(filename, extension)
            dimples_strength = dimples_df[dimples_df.img_name == filename].dimples_strength.values[0]

            # Update progress bar
            progress_bar.set_description('Processing image {}'.format(filename + '.{}'.format(extension)))

            # Main EM algorithm
            output_map, auc, fpr, tpr = mm(args_mm)

            # Save results
            results_dict = {'img_name': filename, 'dimples_strength': dimples_strength, 'format': extension, 'quality': quality, 'manipulation_type': manip_type, 'manip_size': manip_size, 'win_size': args.win_size, 'auc': auc}
            results_fpr_dict = {'img_name': filename, 'fpr': fpr}
            results_tpr_dict = {'img_name': filename, 'tpr': tpr}

            results = pd.DataFrame(results_dict, index=[0])
            results_fpr = pd.DataFrame(results_fpr_dict)
            results_tpr = pd.DataFrame(results_tpr_dict)

            results.to_csv(results_path, mode='a', header=False)
            results_fpr.to_csv(results_path_fpr, mode='a', header=False)
            results_tpr.to_csv(results_path_tpr, mode='a', header=False)

            # Update progress bar
            progress_bar.update(1)
            imgs_done += 1

        end = time.time()

        # Final message
        print()
        print('Summary')
        print('Images analyzed: {}/'.format(imgs_done) + '{} (missing images have generated errors).'.format(imgs_tot))
        if (end - start) / 60 ** 2 >= 1:
            print('Elapsed time: {:.0f} h'.format((end - start) / 60 ** 2) + ' {:.0f} m'.format((end - start) / 60) + ' {:.2f} s.'.format((end - start) % 60))
        elif (end - start) / 60 >= 1:
            print('Elapsed time: {:.0f} m'.format((end - start) / 60) + ' {:.2f} s.'.format((end - start) % 60))
        else:
            print('Elapsed time: {:.2f} s.'.format(end - start))

    else:
        # Time
        start = time.time()

        results = pd.DataFrame()
        # TODO load results from file

        end = time.time()

        # Final message
        print()
        print('Summary')
        print('Loaded data from {} images.'.format(len(results)))
        if (end - start) / 60 ** 2 >= 1:
            print('Elapsed time: {:.0f} h'.format((end - start) / 60 ** 2) + ' {:.0f} m'.format(
                (end - start) / 60) + ' {:.2f} s.'.format((end - start) % 60))
        elif (end - start) / 60 >= 1:
            print('Elapsed time: {:.0f} m'.format((end - start) / 60) + ' {:.2f} s.'.format((end - start) % 60))
        else:
            print('Elapsed time: {:.2f} s.'.format(end - start))

        pass

    # TODO generate plots from results

    return


if __name__ == '__main__':

    # Initialize parser
    parser = ArgumentParser(description='Results script for the "Photo Forensics from Rounding Artifacts" project; generates results by analyzing JPEG and PNG images from two given directories (e.g. "path/to/jpeg_images/" and "path/to/png_images/") as described in the referenced paper, or loads existing results from the "results/" folder.')

    # Add parser arguments
    parser.add_argument('generate', help='Analyze images and generate results; only loads existing results if False (default: False).')
    parser.add_argument('-path', '--dir_path', help='Path of the directory containing the images to be analyzed. Only needed if generate is True.')
    parser.add_argument('-ws', '--win_size', type=int, help='Window size in pixel (default: 256). Note: must be a multiple of 8. Only needed if generate is True.')

    args = parser.parse_args()

    # Run main script
    main(args)