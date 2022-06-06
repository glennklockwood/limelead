---
title: Azure Basics
---

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
$ az vm image list -o table --all --publisher Canonical --sku 22_04-lts

Offer                         Publisher    Sku                 Urn                                                                     Version
----------------------------  -----------  ------------------  ----------------------------------------------------------------------  ---------------
0001-com-ubuntu-server-jammy  Canonical    22_04-lts           Canonical:0001-com-ubuntu-server-jammy:22_04-lts:22.04.202204200        22.04.202204200
0001-com-ubuntu-server-jammy  Canonical    22_04-lts           Canonical:0001-com-ubuntu-server-jammy:22_04-lts:22.04.202206040        22.04.202206040
0001-com-ubuntu-server-jammy  Canonical    22_04-lts-gen2      Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:22.04.202204200   22.04.202204200
0001-com-ubuntu-server-jammy  Canonical    22_04-lts-gen2      Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:22.04.202206040   22.04.202206040
```
