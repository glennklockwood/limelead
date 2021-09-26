---
title: Using the TI Deep Learning (TIDL) Python API
shortTitle: TIDL Python API
order: 40
---

These are my running notes for porting the [TIDL demo app that comes with the
BeagleBone AI][c++ demo] to a Python interface.

[c++ demo]: https://github.com/glennklockwood/beaglebone-ai/blob/main/classification/classification.cpp
[ti imagenet demo]: https://git.ti.com/cgit/tidl/tidl-api/tree/examples/pybind/imagenet.py

## Importing TIDL from Python

TIDL includes a Python3 interface which is included with the BeagleBone AI
version of the TIDL API.  However it's not obvious _how_ to use it since naively
trying to run the Python example apps fails:

    $ cd /usr/share/ti/examples/tidl/pybind
    $ ./one_eo_per_frame.py
    Traceback (most recent call last):
      File "./one_eo_per_frame.py", line 35, in <module>
        from tidl import DeviceId, DeviceType, Configuration, Executor, TidlError
    ModuleNotFoundError: No module named 'tidl'

Unlike most Python packages, the TIDL Python interface is a `.so`, not a
directory full of `.py` files so I had a hard time figuring out where to look
for it.  It turns out the trick is to add the following to your `PYTHONPATH`:

    $ PYTHONPATH=/usr/share/ti/tidl/tidl_api ./imagenet.py
    Input: ../test/testvecs/input/objects/cat-pet-animal-domestic-104827.jpeg
    TIOCL FATAL: Failed to open file /dev/mem

This time TIDL was found, but we need to run as root due to TIDL's need to
directly manipulate `/dev/mem`.  So,

    $ sudo PYTHONPATH=/usr/share/ti/tidl/tidl_api ./imagenet.py
    [sudo] password for debian:
    Input: ../test/testvecs/input/objects/cat-pet-animal-domestic-104827.jpeg
    1: Egyptian_cat,   prob = 34.12%
    2: tabby,   prob = 34.12%
    3: Angora,   prob =  9.41%
    4: tiger_cat,   prob =  7.84%

Since TIDL Python apps have to run as root, you may run into unexpected errors
even if you `export PYTHONPATH=/usr/share/ti/tidl/tidl_api` in your `.bashrc`.

## TIDL's Python API

This TIDL package for Python does not expose the entire TIDL C++ API to Python.
Instead, it only provides the following as of version 01.04.00:

Method/Class/etc             | Type
-----------------------------|-----------------------------------
tidl.ArgInfo                 | pybind11\_builtins.pybind11\_type
tidl.Configuration           | pybind11\_builtins.pybind11\_type
tidl.DeviceId                | pybind11\_builtins.pybind11\_type
tidl.DeviceType              | pybind11\_builtins.pybind11\_type
tidl.ExecutionObject         | pybind11\_builtins.pybind11\_type
tidl.ExecutionObjectPipeline | pybind11\_builtins.pybind11\_type
tidl.Executor                | pybind11\_builtins.pybind11\_type
tidl.TidlError               | type (it's an exception)
tidl.allocate\_memory        | builtin\_function\_or\_method
tidl.enable\_time\_stamps    | builtin\_function\_or\_method
tidl.free\_memory            | builtin\_function\_or\_method

The namespace of the `tidl.so` package is dumped out by doing something like
this:

```python
import sys
sys.path.append("/usr/share/ti/tidl/tidl_api")
import tidl

for part in dir(tidl):
    print(part, eval("str(type(tidl.{}))".format(part)))
```

Notably, the C++ `tidl::imgutil` is _not_ included so we don't have access to
[`tidl::imgutil::PreprocessImage`][imgutil src].  This function applies the
OpenCV steps required to transform any old input image into the format expected
TIDL's models.  So, we have to preprocess images ourselves in Python with
OpenCV; [TI's imagenet.py example][] shows how this is done.

For completeness (and since it's not documented anywhere), I've included all the
interfaces provided by the TIDL Python API below.  The best documentation on
what each member does can be found in the [TIDL API Reference][].

[TIDL API Reference]: https://downloads.ti.com/mctools/esd/docs/tidl-api/api.html

### tidl.ArgInfo

Member                       | Type
-----------------------------|----------------
tidl.ArgInfo.size            | instancemethod

### tidl.Configuration

Member                                  | Type
----------------------------------------|----------------
tidl.Configuration.channels             | property
tidl.Configuration.enable\_api\_trace   | property
tidl.Configuration.enable\_layer\_dump  | property
tidl.Configuration.height               | property
tidl.Configuration.in\_data             | property
tidl.Configuration.layer\_index\_to\_layer\_group\_id   | property
tidl.Configuration.network\_binary      | property
tidl.Configuration.network\_heap\_size  | property
tidl.Configuration.num\_frames          | property
tidl.Configuration.out\_data            | property
tidl.Configuration.param\_heap\_size    | property
tidl.Configuration.parameter\_binary    | property
tidl.Configuration.pre\_proc\_type      | property
tidl.Configuration.read\_from\_file     | instancemethod
tidl.Configuration.run\_full\_net       | property
tidl.Configuration.show\_heap\_stats    | property
tidl.Configuration.width                | property

### tidl.DeviceID

Member                  | Type
------------------------|----------------
tidl.DeviceId.ID0       | tidl.DeviceId
tidl.DeviceId.ID1       | tidl.DeviceId
tidl.DeviceId.ID2       | tidl.DeviceId
tidl.DeviceId.ID3       | tidl.DeviceId

### tidl.DeviceType

Member                  | Type
------------------------|----------------
tidl.DeviceType.DSP     | tidl.DeviceType
tidl.DeviceType.EVE     | tidl.DeviceType

### tidl.ExecutionObject

Member                                              | Type
----------------------------------------------------|----------------
tidl.ExecutionObject.get\_device\_name              | instancemethod
tidl.ExecutionObject.get\_frame\_index              | instancemethod
tidl.ExecutionObject.get\_input\_buffer             | instancemethod
tidl.ExecutionObject.get\_output\_buffer            | instancemethod
tidl.ExecutionObject.get\_process\_time\_in\_ms     | instancemethod
tidl.ExecutionObject.process\_frame\_start\_async   | instancemethod
tidl.ExecutionObject.process\_frame\_wait           | instancemethod
tidl.ExecutionObject.set\_frame\_index              | instancemethod
tidl.ExecutionObject.write\_layer\_outputs\_to\_file| instancemethod

### tidl.ExecutionObjectPipeline

Member                                              | Type
----------------------------------------------------|----------------
tidl.ExecutionObjectPipeline.get\_device\_name      | instancemethod
tidl.ExecutionObjectPipeline.get\_frame\_index      | instancemethod
tidl.ExecutionObjectPipeline.get\_input\_buffer     | instancemethod
tidl.ExecutionObjectPipeline.get\_output\_buffer    | instancemethod
tidl.ExecutionObjectPipeline.process\_frame\_start\_async | instancemethod
tidl.ExecutionObjectPipeline.process\_frame\_wait   | instancemethod
tidl.ExecutionObjectPipeline.set\_frame\_index      | instancemethod

### tidl.Executor

Member                                      | Type
--------------------------------------------|----------------
tidl.Executor.at                            | instancemethod
tidl.Executor.get\_api\_version             | builtin\_function\_or\_method
tidl.Executor.get\_num\_devices             | builtin\_function\_or\_method
tidl.Executor.get\_num\_execution\_objects  | instancemethod

[imgutil src]: https://git.ti.com/cgit/tidl/tidl-api/tree/tidl_api/src/imgutil.cpp#n36
[TI's imagenet.py example]: https://git.ti.com/cgit/tidl/tidl-api/tree/examples/pybind/imagenet.py#n175

## Image interface into Python

The BeagleBone [demo app][c++ demo] and the [TI Python example][ti imagenet demo]
use OpenCV, so let's use that too.  [PIL][] is an alternative used in the
[Jetson Nano classification demo][], and it may be a better choice in the future
since it's a simpler library than OpenCV, but PIL is not included with the
BeagleBone AI OS whereas OpenCV is.

To import an image from a USB webcam:

```python
#!/usr/bin/env python3
import cv2

camera = cv2.VideoCapture("/dev/video1")
_, image = camera.read()
cv2.imwrite('cv2capture.jpg', image)
```

[PIL]: https://pillow.readthedocs.io/en/stable/
[Jetson Nano classification demo]: https://github.com/glennklockwood/jetson-nano-fun/blob/main/classification/classify.py

## Streaming OpenCV over HTTP

Flask comes with BeagleBone's OS and provides everything you need to stream
video over HTTP as the [BeagleBone AI's classification demo][c++ demo] app does.
There's just a little glue code needed to 
[read images using OpenCV](#image-interface-into-python) and
[write them to an mjpg stream][miguelgrinberg blog]:

```python3
#!/usr/bin/env python3

import flask
import cv2

app = flask.Flask(__name__)
def stream_camera(camera):
    while True:
        ret, frame = camera.read()
        if ret:
            _, imstr = cv2.imencode(".jpg", frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                + bytes(imstr) + b'\r\n')

@app.route('/')
def video_feed():
    return flask.Response(
        stream_camera(cv2.VideoCapture("/dev/video1")),
        mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
```

The beauty here is that you can modify `frame` after it is read in
`stream_camera()` to manipulate the image before sending it to the HTTP video
stream.  This is where you can insert functionality (such as using OpenCV to
add a text overlay) on each video frame.

## Classifying video frames

You can intercept frames in `stream_camera()` and apply an arbitrary `filter_function()`
before passing it to the mjpg stream:

```python
def stream_camera(camera):
    while True:
        ret, frame = camera.read()
        if ret:
            frame = filter_function(frame)
            _, imstr = cv2.imencode(".jpg", frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                + bytes(imstr) + b'\r\n')
```

Naively, this `filter_function()` could do something like...

1. run the frame through a neural net by way of TIDL or any other ML framework
   to classify the contents of image
2. overlay a text message with the label we got from step 1

On BeagleBone AI this would be slow though; every frame would have to be
processed and streamed before the next frame could begin, bottlenecking
inference on the inference performance of a single frame.  With more
careful integration, you can round-robin image frames over all EVEs and
DSPs to keep them all busy processing frames though.

I've written an example app that integrates [TIDL, OpenCV, and Flask to do
streaming classification][classify_webcam].  Its core loop looks at each
ExecutionObjectPipeline in a round-robin fashion and does the following:

1. Checks to see if an ExecutionObjectPipeline (EOP) is done processing its work
    1. If so, read the results from the EOP's EVE or DSP.
    2. Find out the label with the highest confidence from those results
    3. Use `cv2.putText()` to write that topmost label on the image
    4. Send the image as the next video frame via Flask
2. Reads an image frame from the webcam
3. Squeezes the frame down to 224 &#215; 224 pixels, which is what the TIDL
   model being used expects
4. Rearranges the layout of the image in memory to match [the in-memory image
   representation that TIDL expects][tidl tensor format]
5. Asynchronously launches the ExecutionObjectPipeline to classify the image

{% call alert("info") %}
Remember: One EVE or DSP can have one ExecutionObject (EO) at most.  It seems
that EOs can be assembled into ExecutionObjectPipelines (EOPs) without much
restriction, but one EOP typically has only one EO when doing image
classification.  This means that one EVE or DSP processes one image frame.
{% endcall %}

By using TIDL asynchronously and looping over ExecutionObjectPipelines, we can
load one frame on to each DSP and EVE to be classified in parallel.  As EVEs
and DSPs finish classifying their frame, we can load up another frame and
launch it asynchronously while we look at the results we just got back.

This is like having your washer and dryer going at the same time--if you've
got multiple loads of laundry to wash, you can let your dryer run while you
load your second load into the washer, and you can fold your laundry when both
washer and dryer are running.  On BeagleBone AI, we have four EVEs and two DSPs
which allows us to have five other video frames being processed while we
use `cv2.putText()` to overlay text on the image we're about to stream out.

[classify_webcam]: https://github.com/glennklockwood/beaglebone-ai/blob/main/pyclassify/classify_webcam.py

[miguelgrinberg blog]: https://blog.miguelgrinberg.com/post/video-streaming-with-flask
[tidl tensor format]: https://software-dl.ti.com/jacinto7/esd/processor-sdk-rtos-jacinto7/06_02_00_21/exports/docs/tidl_j7_01_01_00_10/ti_dl/docs/user_guide_html/md_tidl_fsg_io_tensors_format.html

