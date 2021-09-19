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

Method/Class/etc               | Type
-------------------------------|-----------------------------------
`tidl.ArgInfo`                 | `pybind11_builtins.pybind11_type`
`tidl.Configuration`           | `pybind11_builtins.pybind11_type`
`tidl.DeviceId`                | `pybind11_builtins.pybind11_type`
`tidl.DeviceType`              | `pybind11_builtins.pybind11_type`
`tidl.ExecutionObject`         | `pybind11_builtins.pybind11_type`
`tidl.ExecutionObjectPipeline` | `pybind11_builtins.pybind11_type`
`tidl.Executor`                | `pybind11_builtins.pybind11_type`
`tidl.TidlError`               | `type` (it's an exception)
`tidl.allocate_memory`         | `builtin_function_or_method`
`tidl.enable_time_stamps`      | `builtin_function_or_method`
`tidl.free_memory`             | `builtin_function_or_method`

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
OpenCV.

[imgutil src]: https://git.ti.com/cgit/tidl/tidl-api/tree/tidl_api/src/imgutil.cpp#n36

## Image interface into Python

The BeagleBone [demo app][c++ demo] and the [TI Python example][ti imagenet demo]
use OpenCV, so let's use that too.  [PIL][] is an alternative used in the
[Jetson Nano classification demo][], and it may be a better choice in the future
since it's a simpler library than OpenCV.  However OpenCV comes with the
BeagleBone AI OS, so we might as well use it.

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
