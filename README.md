# Quilt Generator from Lightfield Captures

## Overview
[Looking Glass Factory](https://lookingglassfactory.com) has created a file format for exchanging 
[light field](https://en.wikipedia.org/wiki/Light_field) images and video called 
[quilts](https://docs.lookingglassfactory.com/keyconcepts/quilts). 

Lightfield images, unlike traditional 2D images, contain multiple viewpoints for display on a glasses-free 3D displays 
they make. The file format uses existing image formats like PNG, JPEG, MP4, and webm, but the format describes how to 
store multiple viewpoints in the same file. The trick is the store them in a grid, aka 
[quilt](https://docs.lookingglassfactory.com/keyconcepts/quilts).

This utility script works off the principle of
[linear light field capture](https://docs.lookingglassfactory.com/keyconcepts/capturing-a-lightfield/linear-light-field-capture) 
and turns a set of images or a video, captured on a [linear rail](https://en.wikipedia.org/wiki/Camera_dolly) (dollying left to right)
into a quilt. The script is built on ffmpeg filters 

### Limitations
Theoretically this script could stitch multiple videos into a 4D (video) quilt, but there currently isn't any tech 
commercially available to capture 48 or more views simultaneously. So I've only tested this with an array of images 
or a single video, where the script extracts multiple frames from the video and assumes it was recorded on an 
[automated dolly rail](https://lkg-learn.netlify.app/tutorials/how-to-capture-light-field-photos).

You could generate the multiple views with computer graphics, but 
[there are already tools to create quilts](https://lookingglassfactory.com/software)
directly in major game engines and web technology today, so you won't need this script then.

## Usage
This is a command-line tool written in Python. So if you have Python 3.12 or higher installed, you can install it with...
```shell
pip install lkg-quilt
```
If you prefer to use conda as your package and environment manager...
```shell
conda install lkg-quilt
```
### Generating Quilts
```text
usage: lkg-quilt [-h] [-r ROWS] [-c COLUMNS] [-a ASPECT] [-W WIDTH] [-H HEIGHT] [--output OUTPUT] [--invert] 
                [--focus FOCUS] [--rail] [-v] [input ...]

Create an lightfield quilt.

positional arguments:
  input                 A list of light field capture views. File name patterns are accepted. ffmpeg supports C printf 
                        syntax for referencing multiple files. (default: frame_%04d.png)

options:
  -h, --help            show this help message and exit
  -r ROWS, --rows ROWS  Number of rows in the grid. (default: 6)
  -c COLUMNS, --columns COLUMNS
                        Number of columns in the grid. (default: 8)
  -a ASPECT, --aspect ASPECT
                        Aspect ratio for cropping the input images (width/height). (default: 0.75)
  -W WIDTH, --width WIDTH
                        Pixel width of the quilt. (default: 3360)
  -H HEIGHT, --height HEIGHT
                        Pixel height of the quilt. (default: 3360)
  --output OUTPUT       Output file name. (default: output_qs{columns}x{rows}a{aspect}.png)
  --invert              Reverse the order of the light field images. (default: False)
  --focus FOCUS         A shift of the focal plane. Larger values push into the image. (default: 0.0)
  --rail                Treat the input as a video filmed on a linear photo rail to extract views from. (default: False)
  -v, --verbose         Output more information. (default: False)
```

#### Generating a quilt from sequentially named frames
Assuming you've got your light field capture frames exported to JPEG files in a directory, and they are named 
`frame_001.jpg`, `frame_002.jpg`, etc. This argument is passed directly to ffmpeg which supports C printf syntax. 
This example will match all files prefixed with `frame_` followed by 3 digits before the file extension.
```shell
lkg-quilt example/frame_%03.jpg
```

#### Generating a quilt from randomly named frames
Assuming you've got your light field capture frames exported but you've got clear
naming strategy, or they are out of order, or they don't sort alphanumerically 
(ex. `frame1.jpg`, `frame10.jpg`, `frame2.jpg`, etc..)
```shell
lkg-quilt frame1.jpg frameTwo.jpg 003_view.jpg fourth.jpg ...
```

#### Generating a quilt from a video
If you have a video that you captured, you can point to the single video file and the script will
extract the views it needs. 
```shell
lkg-quilt --rail capture.mp4
```
*Note for linear video capture:* The script assumes the video is a capture of a dolly/track movement of constant speed, 
so it's recommended that you trim out the beginning and end in a video editor so that it only includes the frames of the video that are in motion on 
the camera rail.

#### Reversing a quilt
Here is how to generate a quilt if the capture was in the wrong direction (right to left instead of left to right)
```shell
lkg-quilt --invert path/to/my/frames_%02.png
```

#### Generating a quilt for a non-portrait device
I have a Looking Glass Portrait, so the defaults create a quilt that displays well on it's vertical 3:4 aspect ratio. You might 
want to generate quilts for other aspect ratios. For example, if you have a horizontal 16:9 device you'll want to override the
aspect ratio. You might also want to consult the best combinations of 
[quilt settings for your device](https://docs.lookingglassfactory.com/keyconcepts/quilts#quilt-settings-by-device).
```shell
# Looking Glass 16"
lkg-quilt -a 1.7778 -c 5 -r 9 -W 4096 -H 4096

# Looking Glass 32"
lkg-quilt -a 1.7778 -c 5 -r 9 -W 8192 -H 8192

# Looking Glass 65"
lkg-quilt -a 1.7778 -c 8 -r 9 -W 8192 -H 8192
```

#### Adjusting the focal plane
Your light field capture may appear blurry when displayed. This is because in a raw capture everything moves in the
capture, except for things that are infinitely far away. To fix this you can manually adjust the focal plane, which 
practically means shifting the set of captured views toward the center causing a new plane of the real world to not move
from view to view, the focal plane. 

```shell
lkg-quilt --focus 0.5
```

*Note about focus:* I'm not sure what the "units" of focus mean in this context, but 0.0 keeps the focal plane infinitely far away and 1.0
moves the focal plane to where the leftmost and rightmost fields of view intersect. 

*Tip:* I don't have an interactive way to tune this focus value, so you'll need to experiment.
I can eyeball the focal plane in a quilt at a glance by looking up and down the columns to see what part of the image
isn't moving. For example, in a headshot I adjust the focus until my eyes don't change position.

Values larger than 1.0 are allowed but the left and right sides of the capture will be greatly cutoff, narrowing the usable view.
