---
title: Azure Basics
---

I'm still figuring out techniques and best practices for using Azure coming from
a background in HPC.  A lot of the documentation takes a
Windows/Powershell/GUI-first approach which does not compute for me, so I'm
taking notes here so I don't lose track of how to do common tasks.

So far I'm converging on using a combination of [Azure CLI][] and [Bicep][] as
the foundational tools for standing up infrastructure in Azure.  I'm not sure
this is the best way to start for people who are new to both Azure itself and
infrastructure-as-code since the declarative approach to IaC adds extra
verbosity and syntactic complexity to operations, so I think starting with the
imperative [Azure CLI][] approach is a good place to start.

## Working in a big subscription

Most online documentation assume you have your own developer subscription to
play around in.  In reality, most people thrown head-first into Azure have one
or more existing subscriptions that are subject to complex regional restrictions
and quotas, so here's some of the problems I encountered while playing around.

### VM SKU / hypervisor conflicts

I tried this:

```
$ az deployment group create --resource-group glock-rg \
                             --template-file template.bicep \
                             --parameters @parameters.json

The selected VM size 'Standard_A1_v2' cannot boot Hypervisor Generation '2'. If
this was a Create operation please check that the Hypervisor Generation of the
Image matches the Hypervisor Generation of the selected VM Size. If this was
an Update operation please select a Hypervisor Generation '2' VM Size.
```

It turns out this is because my `properties.storageProfile.imageReference.sku`
was `18_04-lts-gen2` - the `gen2` was the incompatible part.  To find all the
compatible VMs:

```
$ az vm image list-skus --location westcentralus --publisher Canonical --offer UbuntuServer --output table
Location       Name
-------------  --------------------
westcentralus  12.04.5-LTS
westcentralus  14.04.0-LTS
westcentralus  14.04.1-LTS
westcentralus  14.04.2-LTS
...
```

See [this page](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/cli-ps-findimage) for the full documentation.

[Azure CLI]: https://docs.microsoft.com/en-us/cli/azure/
[Bicep]: https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview
