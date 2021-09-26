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

### tidle.Configuration

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

## Streaming OpenCV over HTTP

Flask comes with BeagleBone's OS and provides everything you need to stream
video over HTTP as the BeagleBone AI's classification demo app does.  There's
just a little glue code needed to [read images using OpenCV](#image-interface-into-python)
and [writing them to an mjpg stream][miguelgrinberg blog]:

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
`stream_camera` using OpenCV to manipulate the image before sending it to the
HTTP video stream.  This is where you can insert functionality such as
image classification and overlaying text on each video frame.

[miguelgrinberg blog]: https://blog.miguelgrinberg.com/post/video-streaming-with-flask

[PIL]: https://pillow.readthedocs.io/en/stable/
[Jetson Nano classification demo]: https://github.com/glennklockwood/jetson-nano-fun/blob/main/classification/classify.py
