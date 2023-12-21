import os, re
import argparse
import ffmpeg


def get_video_info(filename):
    probe = ffmpeg.probe(filename)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    width = int(video_stream['width'])
    height = int(video_stream['height'])
    frame_count = int(video_stream['nb_frames']) if 'nb_frames' in video_stream else 1

    # Extract frame rate
    if 'r_frame_rate' in video_stream and video_stream['r_frame_rate'] != '0/0':
        r_frame_rate = video_stream['r_frame_rate']
        frame_rate = eval(r_frame_rate)
    else:
        frame_rate = 0  # Default to 0 if frame rate information is not available

    rotation = int(video_stream.get('tags', {}).get('rotate', 0))
    # extract rotation info from side_data_list, popular for iOS
    if len(video_stream.get('side_data_list', [])) != 0:
        side_data = next(iter(video_stream.get('side_data_list')))
        side_data_rotation = int(side_data.get('rotation', 0))
        if side_data_rotation != 0:
            rotation -= side_data_rotation

    # if the video is rotated, flip the dimensions. We'll rotate the video later to account for it.
    if rotation in [90, 270]:
        width, height = height, width

    return width, height, frame_count, frame_rate, rotation


def create_quilt_filter(
        row_count,
        column_count,
        input_pattern,
        aspect_ratio,
        reverse_order,
        focus,
        rail,
        quilt_w,
        quilt_h):

    # Adjusting if only one file is listed (changes ffmpeg behavior)
    if isinstance(input_pattern, list) and len(input_pattern) == 1:
        input_pattern = input_pattern[0]

    total_views = row_count * column_count
    orig_width, orig_height, total_frames, frame_rate, rotation = get_video_info(input_pattern)

    # When panning for focus, how much padding do we need?
    padding_factor = ((focus + 1) * 2) + 1
    # When focusing, what the max number of pixels we need to shift the images by
    max_focus_shift = orig_width * abs(focus * 2)

    # Get the input views (this can be an imageset, a video set, or a single video (if rail is true)
    filter_stream = ffmpeg.input(input_pattern)
    # If the input is a photo rail video, we need to select the views from it as single frames
    if rail:
        filter_stream = filter_stream.filter('select', f'not(mod(n,{int(total_frames / total_views)}))')

    # A quick "ffmpeg-way" of reversing the order of the views...
    # ...is to flip the tiles and then reverse the flip after the tiling filter.
    #
    # The ffmpeg tile layout starts in the top-left corner (which is wrong for either view order).
    # quilt tile layout starts in the bottom-left corner.

    # Define the flip method based on the order of the views
    flip_method = 'hflip' if reverse_order else 'vflip'

    tile_w = quilt_w / column_count
    tile_h = quilt_h / row_count

    # Now build the chain of filters to turn the input images or video into a quilt
    return (
        filter_stream
        # Focal plane, shift the views left or right by the focus factor
        #  (needs padding around the original image to pan outside the border)
        .filter('pad',
                width=f'iw * {padding_factor}',
                height=f'ih * {padding_factor}',
                x=f'(ow - iw) / 2',
                y=f'(oh - ih) / 2')
        .filter('zoompan',
                z=padding_factor,
                x=f'if(eq(time,0),{orig_width} * {(padding_factor - 1) / 2} - {max_focus_shift / 2},px + {max_focus_shift / total_views})',
                y=f'ih/2-(ih/zoom/2)',
                d=1,
                s=f'{int(orig_width * padding_factor)}x{int(orig_height * padding_factor)}')
        # Crop each tile down to the final aspect ratio
        .filter('crop',
                w='iw',
                h=f'iw / {aspect_ratio}')
        # Scale each tile down to the final size
        .filter('scale',
                width=tile_w,
                height=tile_h)
        # Prepare for ordering the views
        .filter(flip_method)
        # Tile all the views together
        .filter('tile', layout=f'{column_count}x{row_count}')
        # Reorder the views
        .filter(flip_method)
    )


def print_filter_chain(node, level=0):
    # print_all_attributes(node)
    if hasattr(node, 'node'):
        print('  ' * level + 'Node:', node)
        print_filter_chain(node.node, level + 1)

    if hasattr(node, 'incoming_edges'):
        for incoming_edge in node.incoming_edges:
            print('  ' * level + 'Edge:', incoming_edge.upstream_node)
            # print_all_attributes(incoming_edge.upstream_node)
            print_filter_chain(incoming_edge.upstream_node, level + 1)

    if hasattr(node, 'inputs'):
        for input_node in node.inputs:
            print('  ' * level + 'Input:', input_node)
            print_filter_chain(input_node, level + 1)


def strip_printf_substitutions(filename):
    # Define the regex pattern for printf-style substitutions
    pattern = r'[_-]?%([-+0 #]{0,5})(\d*|\*)?(\.\d+)?([hlLzjt]{0,2})([diuoxXfFeEgGaAcspn%])'
    # Replace the matched patterns with an empty string
    stripped_filename = re.sub(pattern, '', filename)
    return stripped_filename


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Create an lightfield quilt.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--rows', type=int, default=6, help='Number of rows in the grid.')
    parser.add_argument('-c', '--columns', type=int, default=8, help='Number of columns in the grid.')
    parser.add_argument('-a', '--aspect', type=float, default=0.75, help='Aspect ratio for cropping the input images (width/height).')
    parser.add_argument('-W', '--width', type=int, default=3360, help='Pixel width of the quilt.')
    parser.add_argument('-H', '--height', type=int, default=3360, help='Pixel height of the quilt.')
    parser.add_argument('input', type=str, nargs='*', default='frame_%04d.png', help='A list of light field capture views. File name patterns are accepted. ffmpeg supports C printf syntax for referencing multiple files.')
    parser.add_argument('--output', type=str, default='{input_prefix}_qs{columns}x{rows}a{aspect}.png', help='Output file name.')
    parser.add_argument('--invert', action='store_true', help='Reverse the order of the light field images.')
    parser.add_argument('--focus', type=float, default=0.0, help='A shift of the focal plane. Larger values push into the image.')
    parser.add_argument('--rail', action='store_true', help='Treat the input as a video filmed on a linear photo rail to extract views from.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Output more information.')
    args = parser.parse_args()

    # Try to probe the first file in the sequence
    try:
        # Create the filter graph for the grid
        quilt_filter = create_quilt_filter(
            args.rows,
            args.columns,
            args.input,
            args.aspect,
            args.invert,
            args.focus,
            args.rail,
            args.width,
            args.height
        )
    except ffmpeg.Error as e:
        # ANSI escape codes
        RED = "\033[31m"  # Red text
        RESET = "\033[0m"  # Reset to default color
        print(f"{RED}Error: Unable to find any files in the list or pattern matching '{args.input}'.{RESET}\n")
        parser.print_help()
        return

    # Set the resolution and output file
    output_filename = args.output.format(
        columns=args.columns,
        rows=args.rows,
        aspect=args.aspect,
        focus=args.focus,
        width=args.width,
        height=args.height,
        input_prefix=strip_printf_substitutions(os.path.splitext(args.input[0])[0])
    )
    output = quilt_filter.output(
        output_filename,
        s=f'{args.width}x{args.height}',
        vframes=1,  # TODO: I want to support merging videos into a quilt
        loglevel='verbose' if args.verbose else 'error')

    # Print the filter chain for debugging
    if args.verbose:
        print_filter_chain(output)

    # Run the FFmpeg command
    print(f"Processing {args.input} for quilt...")
    ffmpeg.run(output)
    print(f"Wrote quilt to {output_filename}.")


if __name__ == "__main__":
    main()
