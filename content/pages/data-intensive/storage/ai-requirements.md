---
title: I/O Requirements of AI
shortTitle: I/O Requirements of AI
---

These are notes and references I've been accumulating to illustrate that
designing a good storage subsystem is just as important as buying a ton of GPUs
for training neural networks.

[Architectural Requirements for Deep Learning Workloads in HPC Environments][]
by Ibrahim et al establishes a nice method for calculating how much storage
bandwidth is required to keep a GPU fully utilized when training different
models. They evaluate relatively small models that are most relevant to
scientific research and demonstrate:

1. If you can establish how many flops are required to pass one sample through
   a model (forward and backwards) during training, you can use the average
   size of a sample to calculate a MiB per FLOP ratio for a model. This is
   equivalent to MiB/s per FLOPS and you can multiply it by the FLOPS
   capability of a GPU (or a whole system) to get an order-of-magnitude
   estimate of the bandwidth required per GPU to train a specific model.
2. They show that DeepCAM is a computationally inexpensive model and requires
   65 GB/s per petaFLOP/s. They found that, in practice, DeepCAM can only
   utilize 35-50 TFLOP/s per NVIDIA V100 GPU, so training this model on a single
   V100 requires 2.275 - 3.250 GB/s, and **an 8-way V100 node would require
   18.2 GB/s - 26 GB/s. By comparison, a typical NFS client cannot achieve more
   than 3 GB/s over TCP.**

[Exascale deep learning for climate analytics][] by Kurth et al directly
calculated their required storage bandwidth for a modified "Tiramisu" network
for climate dataset segmentation and classification at
189 MB/s per V100 GPU, or **1.14 GB/s for a 6-way Power9 GPU node,** or 1.16
TB/s for the full scale of the training job they ran. Their FLOP/s/sample was
4.188 on V100 GPUs, and they achieved 20.93 TFLOP/s/GPU during training.

[Exascale deep learning for climate analytics]: https://dl.acm.org/doi/10.5555/3291656.3291724

[Architectural Requirements for Deep Learning Workloads in HPC Environments]: https://dx.doi.org/10.1109/PMBS54543.2021.00007
