---
title: Computational Requirements of AI
shortTitle: Computational Requirements of AI
---

These are notes and references I've been accumulating to understand how AI
workflows (both training and inferencing) work to help inform the architectural
decisions that go into designing supercomputers specifically for AI.

## Workload partitioning

There are three ways in which **training** a model can be divided across GPU
nodes:

1. Data parallelism
    - simplest way to train at scale (thousands of GPUs)
    - partition the training dataset (the batch) and give each GPU node its own
      subset of the training dataset (a minibatch)
    - each GPU node holds the entire model
    - communication happens after each epoch
    - scales very well since multiple copies of the model are training in
      parallel, but may increase the time to train a model (convergence time)
      since training data may be less randomized as a result of partitioning
2. Pipeline parallelism (aka layer parallelism)
    - break up model into layers, then distribute whole layers across GPU nodes
    - requires moderate rewriting the training code to include communication
      within each epoch
    - scales well for models with lots of big layers
3. Model parallelism (aka tensor parallelism, tensor slicing)
    - break layers of a neural network up and distribute them across GPU nodes
    - requires significant rewriting the training code to include communication
      within each epoch
    - does not scale well due to high communication requirements

These parallelization approaches can be used at the same time.  For example,
training a large language model across multiple DGX nodes likely involves
tensor parallelism within the DGX node (since it has NVLink which makes the
communication fast), pipeline parallelism across 16 DGX nodes, and data
parallelism to accelerate training by scaling to a thousand DGX nodes.

[Microsoft DeepSpeed introduction]: https://www.youtube.com/watch?v=wbG2ZEDPIyw

### Communication

When performing **data-parallel training**, each concurrent instance of the
model uses a different subset of inputs (the _batch_ is partitioned into
_minibatches_ and each model instance gets a minibatch). Then,

1. During forward propagation, there is no communication since the model on
   each concurrent instance (and its weights) are identical. The only difference
   is in the input data (the minibatch).
2. During backpropagation, there is a nonblocking AllReduce that happens after
   each layer's gradients have been calculated.
3. There is a barrier at the end of backpropagation to ensure that all gradients
   have been added up appropriately.
4. After the backpropagation has completed, the sum of all gradients are then
   used to update weights on each instance. Since the weights on each model
   instance were identical at step 1 and AllReduce ensures our gradients are
   all identical, there is no communication needed to update the weights.

I found an article by [Simon Boehm on Data-Parallel Distributed Training of Deep
Learning Models][boehm2022] really helpful in understanding how this works.

[boehm2022]: https://siboehm.com/articles/22/data-parallel-training

## Memory

According to [Microsoft DeepSpeed introduction][], a 40 GB GPU can hold a
model containing 1.2 billion parameters which corresponds to 32 bytes (256 bits)
per parameter. This isn't to say the model stores 256-bit precision parameters;
there is just a lot of supporting data (optimizer states, activations, etc)
that also need to be stored in memory for training.

## Storage

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
2. They show that CosmoFlow is a computationally inexpensive model and requires
   65 GB/s per petaFLOP/s. They found that, in practice, CosmoFlow can only
   utilize 35-50 TFLOP/s per NVIDIA V100 GPU, so training this model on a single
   V100 requires 2.275 - 3.250 GB/s, and **an 8-way V100 node would require
   18.2 GB/s - 26 GB/s. By comparison, a typical NFS client cannot achieve more
   than 3 GB/s over TCP.**
3. By comparison, ResNet-50 being trained on ImageNet is the least I/O-intensive
   and only requires, at most, 573 MB/s per V100 or **3.9 GB/s per 8-way V100
   node.**

I've created a simple tool that illustrates how to do this arithmetic and
[calculates the GB/s required to train a model on different GPUs][ml-model-io-tool].
It's a very loose model and estimates the upper bound of bandwidth required by
assuming that each GPU has enough memory bandwidth, PCIe bandwidth, power,
cooling, etc to train at the full rated performance on their respective spec
sheets.  As shown in this Ibrahim paper (they find that CosmoFlow trains at
35-50 TFLOPS of the theoretical 130 TFLOPS), this is never the case.

[Architectural Requirements for Deep Learning Workloads in HPC Environments]: https://dx.doi.org/10.1109/PMBS54543.2021.00007
[ml-model-io-tool]: https://github.com/glennklockwood/atgtools/blob/master/ml-model-io-requirements.py

[Exascale deep learning for climate analytics][] by Kurth et al directly
calculated their required storage bandwidth for a modified "Tiramisu" network
for climate dataset segmentation and classification at
189 MB/s per V100 GPU, or **1.14 GB/s for a 6-way Power9 GPU node,** or 1.16
TB/s for the full scale of the training job they ran. Their FLOP/s/sample was
4.188 on V100 GPUs, and they achieved 20.93 TFLOP/s/GPU during training.

[Exascale deep learning for climate analytics]: https://dl.acm.org/doi/10.5555/3291656.3291724
