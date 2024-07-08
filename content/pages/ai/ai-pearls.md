---
title: AI Pearls of Wisdom
status: draft
---

## Introduction

This page is a hand-curated list of interesting and useful explanations of how
different aspects of AI work under the hood that I've gleaned from my readings.
I keep this for my own reference, but it may be useful to others who are trying
to learn more about how AI works, specifically as it pertains to understanding
infrastructure requirements.

## Inferencing infrastructure

From the [DeepSpeed-FastGen paper](https://arxiv.org/abs/2401.08671):

- Prompt processing:
  - input is user-provided text (the prompt)
  - output is a key-value cache for attention
  - compute-bound and scales with the input length
- Token generation:
  - adds a token to the KV cache, then generates a new token
  - memory bandwidth-bound and shows approximately O(1) scaling

